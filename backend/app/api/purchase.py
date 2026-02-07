"""
Purchase API Routes
Handles package purchasing and payment.
"""
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
# from app.core.logger import get_logger
from app.models import User, Product, Order, OrderStatus, PaymentMethod
from app.api.schemas import ApiResponse, PurchaseRequest
from app.api.deps import get_current_user
from app.services.wechat_pay import get_wechat_pay_service

# logger = get_logger(__name__)


router = APIRouter(prefix="/purchase", tags=["Purchase"])


def generate_order_no() -> str:
    """生成唯一订单号"""
    timestamp = int(time.time() * 1000)
    random_str = uuid.uuid4().hex[:8].upper()
    return f"ORD{timestamp}{random_str}"


@router.get("/packages", response_model=ApiResponse)
def get_packages(db: Session = Depends(get_db)):
    """
    获取可购买的套餐列表

    Returns:
        API response with available packages
    """
    products = db.query(Product).filter(Product.active == True).all()
    packages_data = []

    for product in products:
        packages_data.append({
            "id": product.key,  # 保持前端兼容性，使用 key 作为 id
            "name": product.name,
            "price": product.price / 100.0,  # 转换为元
            "count": product.count,
            "description": product.description
        })

    return ApiResponse(
        code=200,
        message="成功",
        data={"packages": packages_data}
    )


@router.post("/order", response_model=ApiResponse)
def create_order(
    request: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建购买订单

    Args:
        request: 购买请求
        current_user: 当前用户
        db: 数据库会话

    Returns:
        API response with order info
    """
    # 验证套餐类型
    product = db.query(Product).filter(Product.key == request.package_type, Product.active == True).first()

    if not product:
        return ApiResponse(
            code=4001,
            message="无效的套餐类型",
            data=None
        )

    # 测试模式：直接模拟支付成功
    if request.payment_method == "test":
        if product.count_type == "basic":
            current_user.basic_count += product.count
        else:  # full
            current_user.full_count += product.count
        db.commit()

        return ApiResponse(
            code=200,
            message="购买成功",
            data={
                "package_name": product.name,
                "count_added": product.count,
                "count_type": product.count_type,
                "new_balance": {
                    "basic_count": current_user.basic_count,
                    "full_count": current_user.full_count
                }
            }
        )

    # 微信 Native 支付
    if request.payment_method == "wechat":
        return _create_wechat_order(product, current_user, db)

    # 其他支付方式暂未实现
    return ApiResponse(
        code=4002,
        message="暂不支持此支付方式",
        data=None
    )


def _create_wechat_order(product: Product, user: User, db: Session) -> ApiResponse:
    """创建微信支付订单"""
    try:
        # 检查是否有未支付的订单（未过期的）
        pending_order = db.query(Order).filter(
            Order.user_id == user.id,
            Order.status == OrderStatus.PENDING,
            Order.expires_at > datetime.now()
        ).first()

        if pending_order:
            # 返回未支付订单信息，提示用户先处理
            return ApiResponse(
                code=4003,
                message="存在未支付的订单",
                data={
                    "pending_order": pending_order.to_dict(),
                    "message": "您有未支付的订单，请先完成或关闭该订单后再创建新订单"
                }
            )

        wxpay = get_wechat_pay_service()

        # 生成订单号
        order_no = generate_order_no()

        # 创建订单记录
        order = Order(
            order_no=order_no,
            user_id=user.id,
            product_id=product.id,
            product_name=product.name,
            product_count=product.count,
            count_type=product.count_type,
            amount=product.price,
            payment_method=PaymentMethod.WECHAT_NATIVE,
            status=OrderStatus.PENDING,
            expires_at=datetime.now() + timedelta(hours=2)  # 2小时过期
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 调用微信支付下单
        wxpay_result = wxpay.create_native_order(
            order_no=order_no,
            description=f"{product.name} - {product.description or ''}",
            amount=product.price
        )

        # 更新订单信息
        order.wechat_prepay_id = wxpay_result.get("prepay_id")
        order.wechat_code_url = wxpay_result.get("code_url")
        db.commit()

        return ApiResponse(
            code=200,
            message="订单创建成功",
            data={
                "order_no": order_no,
                "amount": product.price / 100.0,
                "code_url": wxpay_result.get("code_url"),
                "expires_at": order.expires_at.isoformat()
            }
        )

    except Exception as e:
        import traceback
        error_msg = f"创建支付订单失败: {str(e)}"
        # logger.error(f"Error creating order: {error_msg}")
        # logger.error(traceback.format_exc())
        print(f"Error creating order: {error_msg}")
        print(traceback.format_exc())
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/order/{order_no}", response_model=ApiResponse)
def query_order(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询订单状态

    Args:
        order_no: 订单号
        current_user: 当前用户
        db: 数据库会话

    Returns:
        订单状态信息
    """
    order = db.query(Order).filter(
        Order.order_no == order_no,
        Order.user_id == current_user.id
    ).first()

    if not order:
        return ApiResponse(
            code=4004,
            message="订单不存在",
            data=None
        )

    # 如果订单仍为待支付状态，从微信查询最新状态
    if order.status == OrderStatus.PENDING:
        try:
            wxpay = get_wechat_pay_service()
            wxpay_result = wxpay.query_order(order_no)

            trade_state = wxpay_result.get("trade_state")
            if trade_state == "SUCCESS":
                # 支付成功，更新订单和用户余额
                order.status = OrderStatus.PAID
                order.wechat_transaction_id = wxpay_result.get("transaction_id")
                order.paid_at = datetime.now()

                # 增加用户次数
                if order.count_type == "basic":
                    current_user.basic_count += order.product_count
                else:
                    current_user.full_count += order.product_count

                db.commit()

            elif trade_state in ("CLOSED", "REVOKED"):
                order.status = OrderStatus.CLOSED
                db.commit()
            elif trade_state == "REFUND":
                order.status = OrderStatus.REFUNDED
                db.commit()

        except Exception as e:
            # 查询失败，返回本地存储的状态
            pass

    return ApiResponse(
        code=200,
        message="查询成功",
        data=order.to_dict()
    )


@router.post("/order/{order_no}/close", response_model=ApiResponse)
def close_order(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    关闭订单

    Args:
        order_no: 订单号
        current_user: 当前用户
        db: 数据库会话

    Returns:
        API response
    """
    # 查询订单
    order = db.query(Order).filter(
        Order.order_no == order_no,
        Order.user_id == current_user.id
    ).first()

    if not order:
        return ApiResponse(
            code=4004,
            message="订单不存在",
            data=None
        )

    # 只有待支付状态的订单可以关闭
    if order.status != OrderStatus.PENDING:
        return ApiResponse(
            code=4005,
            message=f"订单状态为 {order.status.value}，无法关闭",
            data=None
        )

    try:
        # 如果是微信支付订单，调用微信支付关闭订单接口
        if order.payment_method == PaymentMethod.WECHAT_NATIVE:
            wxpay = get_wechat_pay_service()
            success = wxpay.close_order(order_no)
            if not success:
                return ApiResponse(
                    code=5001,
                    message="关闭微信支付订单失败",
                    data=None
                )

        # 更新本地订单状态
        order.status = OrderStatus.CLOSED
        db.commit()

        return ApiResponse(
            code=200,
            message="订单已关闭",
            data={"order_no": order_no}
        )

    except Exception as e:
        import traceback
        print(f"Error closing order: {e}")
        print(traceback.format_exc())
        return ApiResponse(
            code=5000,
            message=f"关闭订单失败: {str(e)}",
            data=None
        )


@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: Session = Depends(get_db)):
    """
    微信支付回调通知

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        给微信的响应
    """
    try:
        # 获取请求头和请求体
        headers = dict(request.headers)
        body = await request.body()
        body_str = body.decode("utf-8")
        
        # 调试日志
        print(f"[微信回调] 收到通知: headers={headers}, body={body_str}")

        wxpay = get_wechat_pay_service()

        # 验证签名
        if not wxpay.verify_notify(headers, body_str):
            print("[微信回调] 签名验证失败")
            return {"code": "FAIL", "message": "签名验证失败"}

        # 解析回调数据
        import json
        notify_data = json.loads(body_str)

        # 解密订单信息
        resource = notify_data.get("resource", {})
        decrypted_data = wxpay.decrypt_notify_data(
            ciphertext=resource.get("ciphertext"),
            associated_data=resource.get("associated_data"),
            nonce=resource.get("nonce")
        )

        # 获取订单信息
        order_no = decrypted_data.get("out_trade_no")
        trade_state = decrypted_data.get("trade_state")
        transaction_id = decrypted_data.get("transaction_id")

        if not order_no:
            return {"code": "FAIL", "message": "订单号不存在"}

        # 查询订单
        order = db.query(Order).filter(Order.order_no == order_no).first()

        if not order:
            return {"code": "FAIL", "message": "订单不存在"}

        # 处理支付成功
        if trade_state == "SUCCESS" and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.PAID
            order.wechat_transaction_id = transaction_id
            order.paid_at = datetime.now()

            # 增加用户次数
            user = db.query(User).filter(User.id == order.user_id).first()
            if user:
                if order.count_type == "basic":
                    user.basic_count += order.product_count
                else:
                    user.full_count += order.product_count

            db.commit()

        return {"code": "SUCCESS", "message": "OK"}

    except Exception as e:
        return {"code": "FAIL", "message": f"处理失败: {str(e)}"}
