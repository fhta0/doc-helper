"""
Order Models
订单相关数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"  # 待支付
    PAID = "paid"        # 已支付
    REFUNDED = "refunded" # 已退款
    EXPIRED = "expired"  # 已过期
    CLOSED = "closed"    # 已关闭


class PaymentMethod(str, enum.Enum):
    WECHAT_NATIVE = "wechat_native"  # 微信扫码支付
    ALIPAY_PAGE = "alipay_page"      # 支付宝网页支付
    TEST = "test"                    # 测试支付


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False, index=True, comment="商户订单号")
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, comment="产品ID")
    
    # 产品快照（防止产品修改后订单信息对不上）
    product_name = Column(String(100), nullable=False, comment="产品名称")
    product_count = Column(Integer, nullable=False, comment="包含次数")
    count_type = Column(String(20), nullable=True, comment="次数类型")
    
    # 支付信息
    amount = Column(Integer, nullable=False, comment="订单金额（分）")
    payment_method = Column(String(50), nullable=True, comment="支付方式")
    status = Column(String(20), default=OrderStatus.PENDING, index=True, comment="订单状态")
    
    # 微信支付特定字段
    wechat_transaction_id = Column(String(64), nullable=True, index=True, comment="微信支付交易号")
    wechat_prepay_id = Column(String(64), nullable=True, comment="微信预支付ID")
    wechat_code_url = Column(String(512), nullable=True, comment="微信支付二维码链接")
    
    # 时间信息
    paid_at = Column(DateTime, nullable=True, comment="支付时间")
    expires_at = Column(DateTime, nullable=True, comment="订单过期时间")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # Relationships
    user = relationship("User", backref="orders")
    product = relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "product_name": self.product_name,
            "product_count": self.product_count,
            "amount": self.amount / 100.0,  # 转回元
            "status": self.status,
            "payment_method": self.payment_method,
            "code_url": self.wechat_code_url,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
