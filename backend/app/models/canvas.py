import uuid
from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CanvasObject(Base):
    __tablename__ = "canvas_objects"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    object_type: Mapped[str] = mapped_column(String(80), nullable=False, default="custom", server_default="custom")
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    width: Mapped[float] = mapped_column(Float, nullable=False, default=180)
    height: Mapped[float] = mapped_column(Float, nullable=False, default=100)
    rotation: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    placed: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    locked: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["companies.tenant_id"], name="fk_canvas_objects_tenant"),
        ForeignKeyConstraint(["parent_id"], ["canvas_objects.id"], name="fk_canvas_objects_parent", ondelete="SET NULL"),
        UniqueConstraint("tenant_id", "id", name="uq_canvas_objects_tenant_id"),
    )
