from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DocAI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_DIR: str = "logs"    # 日志目录

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/doc_ai"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_GUEST: int = 10485760  # 10MB
    MAX_FILE_SIZE_AUTHENTICATED: int = 104857600  # 100MB

    # AI Configuration
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_TIMEOUT: int = 60

    # WeChat Pay Configuration
    WECHAT_MCHID: str = ""  # 商户号
    WECHAT_APPID: str = ""  # 应用ID
    WECHAT_APPSECRET: str = ""  # 应用密钥
    WECHAT_APIV3_KEY: str = ""  # APIv3密钥
    WECHAT_CERT_SERIAL_NO: str = ""  # 证书序列号
    WECHAT_CERT_PATH: str = "cert/apiclient_cert.pem"  # 商户证书路径
    WECHAT_KEY_PATH: str = "cert/apiclient_key.pem"  # 商户私钥路径
    WECHAT_PUBLIC_KEY_PATH: str = "cert/pub_key.pem"  # 微信平台公钥路径
    WECHAT_PUBLIC_KEY_ID: str = ""  # 微信平台公钥ID (格式: PUB_KEY_ID_xxx)
    WECHAT_NOTIFY_URL: str = ""  # 支付回调地址
    WECHAT_REDIRECT_URI: str = ""  # 微信登录回调地址

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


settings = Settings()
