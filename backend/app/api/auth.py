"""
Authentication API Routes
Handles user registration and login.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
from app.models.check import Check
from app.models.order import Order
from app.api.schemas import (
    ApiResponse,
    LoginRequest,
    RegisterRequest,
)
from app.api.deps import get_current_user
from datetime import date
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        request: Registration request with username, password, nickname, and optional guest_username
        db: Database session

    Returns:
        API response with access token and user data (auto-login after registration)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        return ApiResponse(
            code=400,
            message="用户名已存在",
            data=None
        )

    # Create new user
    new_user = User(
        username=request.username,
        password_hash=get_password_hash(request.password),
        nickname=request.nickname,
        free_count=3,
        last_reset_date=date.today()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Migrate guest data if guest_username is provided
    if request.guest_username:
        logger.info(f"Migrating guest data after registration: {request.guest_username} -> {new_user.id}")
        try:
            _migrate_guest_data(db, request.guest_username, new_user.id)
        except Exception as e:
            logger.error(f"Failed to migrate guest data after registration: {e}")
            # Don't fail registration if migration fails, just log the error

    # Create access token (auto-login)
    access_token = create_access_token(data={"sub": str(new_user.id)})

    return ApiResponse(
        code=200,
        message="注册成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 604800,  # 7 days
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "nickname": new_user.nickname,
                "free_count": new_user.free_count,
                "basic_count": new_user.basic_count,
                "full_count": new_user.full_count,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
            }
        }
    )


@router.post("/login", response_model=ApiResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login.

    Args:
        request: Login request with username, password, and optional guest_username
        db: Database session

    Returns:
        API response with access token and user data
    """
    logger.info(f"Login request - username: {request.username}, guest_username: {request.guest_username}")

    # Find user by username
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.password_hash):
        return ApiResponse(
            code=1001,
            message="用户名或密码错误",
            data=None
        )

    # Migrate guest data if guest_username is provided
    if request.guest_username:
        logger.info(f"Migrating guest data: {request.guest_username} -> {user.id}")
        try:
            _migrate_guest_data(db, request.guest_username, user.id)
        except Exception as e:
            logger.error(f"Failed to migrate guest data: {e}")
            # Don't fail login if migration fails, just log the error

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return ApiResponse(
        code=200,
        message="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 604800,  # 7 days
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "free_count": user.free_count,
                "basic_count": user.basic_count,
                "full_count": user.full_count,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        }
    )


def _migrate_guest_data(db: Session, guest_username: str, target_user_id: int):
    """
    Migrate guest user's data to the logged-in user.

    Args:
        db: Database session
        guest_username: The guest username (starts with 'guest_')
        target_user_id: The target user ID to migrate data to
    """
    # Find guest user by username
    guest_user = db.query(User).filter(User.username == guest_username).first()

    if not guest_user:
        logger.warning(f"Guest user not found: {guest_username}")
        return

    # Update all checks associated with guest user to target user
    updated_count = db.query(Check).filter(
        Check.user_id == guest_user.id
    ).update({"user_id": target_user_id}, synchronize_session=False)

    if updated_count > 0:
        logger.info(f"Migrated {updated_count} checks from guest {guest_username} to user {target_user_id}")

    # Delete guest user
    db.delete(guest_user)
    db.commit()

    logger.info(f"Deleted guest user: {guest_username}")


@router.get("/user/profile", response_model=ApiResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        API response with user profile data
    """
    # Get last template info if exists
    last_template = None
    if current_user.last_template_id:
        from app.models.rule_template import RuleTemplate
        template = db.query(RuleTemplate).filter(RuleTemplate.id == current_user.last_template_id).first()
        if template:
            last_template = {
                "id": template.id,
                "name": template.name,
                "template_type": template.template_type
            }

    # Calculate total purchased counts from orders
    from app.models.order import Order, OrderStatus
    from sqlalchemy import func

    # Query completed orders for this user
    completed_orders = db.query(Order).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.PAID
    ).all()

    # Sum up the counts from all completed orders
    basic_total = 0
    full_total = 0
    for order in completed_orders:
        if order.product:
            if order.product.count_type == "basic":
                basic_total += order.product.count
            elif order.product.count_type == "full":
                full_total += order.product.count

    # Calculate used counts
    basic_used = max(0, basic_total - current_user.basic_count)
    full_used = max(0, full_total - current_user.full_count)

    return ApiResponse(
        code=200,
        message="成功",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname,
            "free_count": current_user.free_count,
            "basic_count": current_user.basic_count,
            "full_count": current_user.full_count,
            "last_template_id": current_user.last_template_id,
            "last_template": last_template,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            # 套餐使用情况
            "quota": {
                "basic": {
                    "total": basic_total,
                    "used": basic_used,
                    "remaining": current_user.basic_count
                },
                "full": {
                    "total": full_total,
                    "used": full_used,
                    "remaining": current_user.full_count
                }
            }
        }
    )


@router.get("/user/orders", response_model=ApiResponse)
def get_user_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's order history.

    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page
        current_user: Current authenticated user
        db: Database session

    Returns:
        API response with order history
    """
    # Query orders for current user
    query = db.query(Order).filter(Order.user_id == current_user.id)

    # Get total count
    total = query.count()

    # Get paginated orders, ordered by created_at desc
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    orders_data = []
    for order in orders:
        orders_data.append({
            "id": order.id,
            "order_no": order.order_no,
            "product_name": order.product_name,
            "product_count": order.product_count,
            "amount": order.amount / 100.0,  # Convert to yuan
            "status": order.status,
            "payment_method": order.payment_method,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        })

    return ApiResponse(
        code=200,
        message="成功",
        data={
            "total": total,
            "orders": orders_data,
            "page": page,
            "page_size": page_size
        }
    )
