from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="created", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_agent: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    dependencies: Mapped[list[int]] = mapped_column(
        JSON, default=list, nullable=False
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str] = mapped_column(
        String(30), default="not_required", nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )
    requested_action: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
