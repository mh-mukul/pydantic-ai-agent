from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime, Boolean

from configs.database import Base


class AbstractBase(Base):
    __abstract__ = True

    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc)
        return self

    @classmethod
    def get_active(cls, db: Session):
        return db.query(cls).filter(cls.is_deleted == False)
