"""
游客模式 API - 提供临时匿名用户访问
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from datetime import timedelta
import uuid

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7天


@router.post("/init")
async def init_guest_session(db: Session = Depends(get_db)):
    """
    初始化游客会话
    - 创建临时匿名用户
    - 返回临时访问 Token
    - 默认给予 2 次基础检测额度
    """
    # 生成唯一的游客标识（用户名前缀 guest_ 表示游客）
    guest_id = f"guest_{uuid.uuid4().hex[:12]}"
    guest_username = f"游客_{guest_id[-6:]}"

    # 创建临时用户记录
    guest_user = User(
        username=guest_id,
        password_hash=get_password_hash("guest_temp"),  # 临时密码，游客无法登录
        nickname=guest_username,
        free_count=0,   # 已使用次数
        basic_count=2,  # 赠送 2 次基础检测
        full_count=0    # 不赠送完整检测
    )

    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)

    # 生成临时访问 Token（7天有效）
    # 使用 user.id 而不是 username，与正式用户保持一致
    access_token = create_access_token(
        data={"sub": str(guest_user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "code": 200,
        "message": "游客会话已创建",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "is_guest": True,
            "user": {
                "id": guest_user.id,
                "username": guest_user.username,
                "nickname": guest_username,
                "basic_count": 2,
                "full_count": 0,
                "free_count": 0
            }
        }
    }


def is_guest_user(username: str) -> bool:
    """检查是否为游客用户（通过用户名前缀判断）"""
    return username.startswith("guest_")
