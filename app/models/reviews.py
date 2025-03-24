from sqlalchemy import Column, CheckConstraint, Integer, DateTime, Boolean, Text, ForeignKey, func

from app.backend.db import Base


class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    comment = Column(Text)
    comment_date = Column(DateTime(timezone=True), server_default=func.now())
    grade = Column(Integer)
    is_active = Column(Boolean, default=True)

    __table_args__ = (CheckConstraint("grade BETWEEN 1 AND 10", name="check_grade_range"),)