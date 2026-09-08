from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    source_url = Column(String(1024), nullable=False)
    target_url = Column(String(1024), nullable=False)
    link_type = Column(String(20), default="internal", nullable=False)  # internal or external
    anchor_text = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=True)
    is_broken = Column(Boolean, default=False, nullable=False)

    page = relationship("Page", back_populates="links")
