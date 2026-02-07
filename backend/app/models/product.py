from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Text
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, comment="套餐名称")
    key = Column(String(50), unique=True, nullable=False, index=True, comment="套餐标识符")
    price = Column(Integer, nullable=False, comment="价格（分）")  # 存储为分
    count = Column(Integer, nullable=False, comment="包含次数")
    count_type = Column(String(20), nullable=False, comment="次数类型(basic/full)")
    description = Column(Text, comment="描述")
    active = Column(Boolean, default=True, comment="是否上架")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "key": self.key,
            "price": self.price / 100.0,  # 转回元
            "count": self.count,
            "count_type": self.count_type,
            "description": self.description,
            "active": self.active
        }
