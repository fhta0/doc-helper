"""
WeChat Pay Service
微信支付服务，使用 API v3
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from wechatpayv3 import WeChatPayType, WeChatPay

from app.core.config import settings

logger = logging.getLogger(__name__)


# 获取项目根目录的绝对路径（backend 目录）
BASE_DIR = Path(__file__).parent.parent.parent.resolve()


class WeChatPayService:
    """微信支付服务类"""

    def __init__(self):
        """初始化微信支付客户端"""
        # 构建证书的绝对路径
        key_path = BASE_DIR / settings.WECHAT_KEY_PATH
        public_key_path = BASE_DIR / settings.WECHAT_PUBLIC_KEY_PATH

        logger.info(f"私钥路径: {key_path}, exists: {key_path.exists()}")
        logger.info(f"平台公钥路径: {public_key_path}, exists: {public_key_path.exists()}")

        # 加载商户私钥
        private_key_str = self._load_private_key(str(key_path))

        # 验证私钥是否有效
        if not private_key_str or not private_key_str.strip():
            raise ValueError("私钥文件为空或无效")

        # 加载微信支付平台公钥
        public_key_str = self._load_public_key(str(public_key_path))

        # 验证平台公钥是否有效
        if not public_key_str or not public_key_str.strip():
            raise ValueError("平台公钥文件为空或无效")

        logger.info(f"商户号: {settings.WECHAT_MCHID}")
        logger.info(f"AppID: {settings.WECHAT_APPID}")
        logger.info(f"证书序列号: {settings.WECHAT_CERT_SERIAL_NO}")
        logger.info(f"私钥长度: {len(private_key_str)}")
        logger.info(f"平台公钥长度: {len(public_key_str)}")
        logger.info(f"平台公钥ID: {settings.WECHAT_PUBLIC_KEY_ID}")

        # 验证平台公钥ID是否配置
        if not settings.WECHAT_PUBLIC_KEY_ID:
            raise ValueError(
                "未配置 WECHAT_PUBLIC_KEY_ID！请按以下步骤操作：\n"
                "1. 登录微信支付商户平台 https://pay.weixin.qq.com\n"
                "2. 进入 账户中心 > API安全 > 微信支付公钥\n"
                "3. 申请并下载微信支付公钥（保存为 cert/pub_key.pem）\n"
                "4. 复制微信支付公钥ID（格式类似 PUB_KEY_ID_123456...）\n"
                "5. 在 .env 文件中设置 WECHAT_PUBLIC_KEY_ID=复制的公钥ID"
            )

        # 使用平台公钥模式（新商户必须使用此模式）
        wxpay_params = {
            "wechatpay_type": WeChatPayType.NATIVE,
            "mchid": settings.WECHAT_MCHID,
            "private_key": private_key_str,
            "cert_serial_no": settings.WECHAT_CERT_SERIAL_NO,
            "appid": settings.WECHAT_APPID,
            "apiv3_key": settings.WECHAT_APIV3_KEY,
            "public_key": public_key_str,
            "public_key_id": settings.WECHAT_PUBLIC_KEY_ID,
            "notify_url": settings.WECHAT_NOTIFY_URL
        }

        self.wxpay = WeChatPay(**wxpay_params)
        logger.info("微信支付客户端初始化成功")

    def _load_private_key(self, key_path: str) -> str:
        """加载商户私钥"""
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"私钥文件不存在: {key_path}")
            raise

    def _load_public_key(self, key_path: str) -> str:
        """加载微信支付平台公钥"""
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"平台公钥文件不存在: {key_path}")
            raise

    def create_native_order(
        self,
        order_no: str,
        description: str,
        amount: int,
        expire_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建 Native 支付订单

        Args:
            order_no: 商户订单号
            description: 商品描述
            amount: 订单金额（分）
            expire_time: 订单过期时间（秒），默认2小时

        Returns:
            包含 code_url 的字典
        """
        try:
            # 处理过期时间，转换为 RFC3339 格式
            if expire_time is None:
                expire_dt = datetime.now() + timedelta(hours=2)
            else:
                expire_dt = datetime.fromtimestamp(expire_time)
            
            # 转换为带时区的 ISO 格式字符串
            expire_time_str = expire_dt.astimezone().isoformat()

            # 调用 pay 方法创建订单，返回 (status_code, response_json)
            code, result = self.wxpay.pay(
                description=description,
                out_trade_no=order_no,
                amount={"total": amount},
                time_expire=expire_time_str,
                pay_type=WeChatPayType.NATIVE
            )

            logger.info(f"[微信支付] 下单响应: code={code}, result={result}")

            # 检查状态码
            if code not in [200, 202]:
                result_dict = json.loads(result) if isinstance(result, str) else result
                error_msg = result_dict.get("message", "未知错误")
                logger.error(f"[微信支付] 下单失败: {error_msg}")
                raise Exception(f"微信支付下单失败: {error_msg}")

            # 解析结果
            result_dict = json.loads(result) if isinstance(result, str) else result
            code_url = result_dict.get("code_url")
            
            if not code_url:
                error_msg = result_dict.get("message", "未知错误")
                raise Exception(f"微信支付返回的 code_url 为空: {error_msg}")

            return {
                "code_url": code_url,
                "prepay_id": result_dict.get("prepay_id")
            }

        except Exception as e:
            logger.error(f"微信支付下单失败: {e}")
            raise

    def query_order(self, order_no: str) -> Dict[str, Any]:
        """
        查询订单状态

        Args:
            order_no: 商户订单号

        Returns:
            订单状态信息
        """
        try:
            # query 方法返回 (code, result) tuple
            code, result = self.wxpay.query(out_trade_no=order_no)
            logger.info(f"[微信支付] 查询订单响应: code={code}, result type={type(result)}, result={result}")

            # 解析结果
            if isinstance(result, str):
                result_dict = json.loads(result)
            elif isinstance(result, dict):
                result_dict = result
            else:
                result_dict = dict(result) if hasattr(result, '__iter__') else {}

            logger.info(f"查询微信订单成功: order_no={order_no}, status={result_dict.get('trade_state')}")
            return result_dict
        except Exception as e:
            logger.error(f"查询微信订单失败: {e}")
            raise

    def verify_notify(self, headers: Dict[str, str], body: str) -> bool:
        """
        验证支付回调签名

        Args:
            headers: HTTP 请求头
            body: 请求体

        Returns:
            验签是否成功
        """
        try:
            # wechatpayv3 会自动验证签名
            # 如果验签失败会抛出异常
            wechatpay_timestamp = headers.get("Wechatpay-Timestamp")
            wechatpay_nonce = headers.get("Wechatpay-Nonce")
            wechatpay_serial = headers.get("Wechatpay-Serial")
            wechatpay_signature = headers.get("Wechatpay-Signature")

            self.wxpay.verify_notify_signature(
                timestamp=wechatpay_timestamp,
                nonce=wechatpay_nonce,
                body=body,
                signature=wechatpay_signature
            )

            logger.info("微信支付回调验签成功")
            return True

        except Exception as e:
            logger.error(f"微信支付回调验签失败: {e}")
            return False

    def decrypt_notify_data(self, ciphertext: str, associated_data: str, nonce: str) -> Dict[str, Any]:
        """
        解密支付回调数据

        Args:
            ciphertext: 加密数据
            associated_data: 附加数据
            nonce: 随机串

        Returns:
            解密后的订单数据
        """
        try:
            result = self.wxpay.decrypt(
                ciphertext=ciphertext,
                associated_data=associated_data,
                nonce=nonce
            )
            logger.info(f"解密回调数据成功: {result}")
            return result
        except Exception as e:
            logger.error(f"解密回调数据失败: {e}")
            raise

    def close_order(self, order_no: str) -> bool:
        """
        关闭订单

        Args:
            order_no: 商户订单号

        Returns:
            是否成功
        """
        try:
            self.wxpay.close(out_trade_no=order_no)
            logger.info(f"关闭微信订单成功: order_no={order_no}")
            return True
        except Exception as e:
            logger.error(f"关闭微信订单失败: {e}")
            return False


# 全局单例
_wechat_pay_service: Optional[WeChatPayService] = None


def get_wechat_pay_service() -> WeChatPayService:
    """获取微信支付服务单例"""
    global _wechat_pay_service
    if _wechat_pay_service is None:
        _wechat_pay_service = WeChatPayService()
    return _wechat_pay_service
