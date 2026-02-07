from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class CheckType(str, enum.Enum):
    BASIC = "basic"
    FULL = "full"


class CheckStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CostType(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    FULL = "full"


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(32), unique=True, nullable=False, index=True, comment="检查ID（业务ID）")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    file_id = Column(String(32), nullable=False, comment="文件ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    revised_file_path = Column(String(500), nullable=True, comment="修订版文件存储路径")
    check_type = Column(Enum(CheckType), default=CheckType.BASIC, comment="检查类型")
    status = Column(Enum(CheckStatus), default=CheckStatus.PENDING, comment="检查状态")
    result_json = Column(Text, comment="检查结果（JSON格式）")
    rule_template_id = Column(Integer, ForeignKey("rule_templates.id", ondelete="SET NULL"), nullable=True, comment="使用的规则模板ID")
    rule_config_json = Column(JSON, nullable=True, comment="规则配置快照（JSON格式）")
    cost_type = Column(Enum(CostType), default=CostType.FREE, comment="消耗类型")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # Relationship
    user = relationship("User", backref="checks")

    def to_dict(self):
        return {
            "check_id": self.check_id,
            "user_id": self.user_id,
            "file_id": self.file_id,
            "filename": self.filename,
            "revised_file_generated": bool(self.revised_file_path),
            "check_type": self.check_type.value if self.check_type else None,
            "status": self.status.value if self.status else None,
            "cost_type": self.cost_type.value if self.cost_type else None,
            "rule_template_id": self.rule_template_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_result_dict(self):
        result = self.to_dict()
        if self.result_json:
            import json
            try:
                result["result"] = json.loads(self.result_json)
            except:
                result["result"] = None
        return result
