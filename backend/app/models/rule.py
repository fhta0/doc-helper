from sqlalchemy import Column, String, Text, DateTime, JSON, func
from app.core.database import Base
import enum


class CheckerType(str, enum.Enum):
    DETERMINISTIC = "deterministic"
    AI = "ai"
    HYBRID = "hybrid"


class Rule(Base):
    __tablename__ = "rules"

    id = Column(String(50), primary_key=True, comment="规则ID（业务ID，如PAGE_MARGIN_25）")
    name = Column(String(100), nullable=False, comment="规则名称")
    category = Column(String(50), nullable=False, index=True, comment="规则分类")
    match = Column(String(50), comment="匹配目标")
    condition_json = Column(JSON, nullable=False, comment="匹配条件（JSON格式）")
    error_message = Column(Text, comment="错误消息")
    suggestion = Column(Text, comment="修复建议")
    checker = Column(String(20), default="deterministic", comment="检查器类型")
    prompt_template = Column(Text, comment="AI检查的prompt模板")
    fix_action = Column(String(100), comment="自动修复动作")
    fix_params = Column(JSON, comment="自动修复参数（JSON格式）")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "match": self.match,
            "condition": self.condition_json,
            "error_message": self.error_message,
            "suggestion": self.suggestion,
            "checker": self.checker,
            "prompt_template": self.prompt_template,
            "fix_action": self.fix_action,
            "fix_params": self.fix_params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
