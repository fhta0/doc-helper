from sqlalchemy import Column, String, Text, DateTime, JSON, func, Boolean, Integer, ForeignKey
from app.core.database import Base
import enum


class TemplateType(str, enum.Enum):
    SYSTEM = "system"  # 系统模板（只读）
    CUSTOM = "custom"  # 用户自定义模板


class RuleTemplate(Base):
    """规则模板表 - 存储文档格式配置模板"""
    __tablename__ = "rule_templates"

    id = Column(Integer, primary_key=True, index=True, comment="模板ID")
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    template_type = Column(String(20), default=TemplateType.CUSTOM, nullable=False, index=True, comment="模板类型")

    # 所属用户（系统模板为null）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="所属用户ID")

    # 规则配置 JSON（核心数据）
    config_json = Column(JSON, nullable=False, comment="规则配置（页边距、字体、行距、标题样式等）")

    # 模板状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认模板")

    # 使用统计
    use_count = Column(Integer, default=0, comment="使用次数")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "user_id": self.user_id,
            "config": self.config_json,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "use_count": self.use_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # 配置JSON结构示例：
    # {
    #   "page": {
    #     "margins": {
    #       "top_cm": 2.5,
    #       "bottom_cm": 2.5,
    #       "left_cm": 3.0,
    #       "right_cm": 2.5
    #     },
    #     "paper_name": "A4"
    #   },
    #   "headings": [
    #     {
    #       "level": 1,
    #       "font": "SimHei",
    #       "size_pt": 16,
    #       "bold": true,
    #       "alignment": "center"
    #     },
    #     {
    #       "level": 2,
    #       "font": "SimHei",
    #       "size_pt": 14,
    #       "bold": true,
    #       "alignment": "left"
    #     }
    #   ],
    #   "body": {
    #     "font": "SimSun",
    #     "size_pt": 12,
    #     "line_spacing_pt": 25,
    #     "first_line_indent_chars": 2
    #   }
    # }
