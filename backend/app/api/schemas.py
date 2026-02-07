from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


# ============== Request Schemas ==============

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    guest_username: Optional[str] = Field(None, max_length=50, description="游客用户名（用于迁移数据）")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    nickname: Optional[str] = Field(None, max_length=64, description="昵称")
    guest_username: Optional[str] = Field(None, max_length=50, description="游客用户名（用于迁移数据）")


class CheckSubmitRequest(BaseModel):
    file_id: str = Field(..., description="文件ID")
    check_type: str = Field(default="basic", description="检查类型")
    filename: Optional[str] = Field(None, description="原始文件名")
    rule_template_id: Optional[int] = Field(None, description="规则模板ID")


class PurchaseRequest(BaseModel):
    package_type: str = Field(..., description="套餐类型: basic_pack, full_pack, single_full")
    payment_method: str = Field(default="test", description="支付方式: test(测试), wechat, alipay")


# ============== Response Schemas ==============

class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Any = None


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    free_count: int
    created_at: Optional[str]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Note: Response models removed as they are not used in the API.
# All endpoints use ApiResponse with data field for flexibility.
