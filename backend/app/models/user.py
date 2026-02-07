from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名（用于登录）")
    password_hash = Column(String(255), nullable=False, comment="密码哈希（BCrypt）")
    nickname = Column(String(64), comment="昵称")
    free_count = Column(Integer, default=3, comment="免费检查次数")
    basic_count = Column(Integer, default=0, comment="基础检测包次数（10元/次）")
    full_count = Column(Integer, default=0, comment="完整检测包次数（20元/次）")
    last_reset_date = Column(Date, comment="上次免费次数重置日期")
    last_template_id = Column(Integer, ForeignKey("rule_templates.id", ondelete="SET NULL"), nullable=True, comment="上次使用的规则模板ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "free_count": self.free_count,
            "basic_count": self.basic_count,
            "full_count": self.full_count,
            "last_reset_date": self.last_reset_date.isoformat() if self.last_reset_date else None,
            "last_template_id": self.last_template_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
