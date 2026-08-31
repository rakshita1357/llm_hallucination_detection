"""SQLAlchemy models for SkepticAI database schema.

Defines the core tables:
- users
- chat_sessions
- messages
- verification_reports
- verification_claims
- verification_evidence

Uses UUIDs for primary keys and proper foreign key relationships.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database.connection import Base


class UserRole(str, enum.Enum):
    """User roles (for future extensibility)."""
    USER = "user"
    ADMIN = "admin"


class MessageRole(str, enum.Enum):
    """Message roles in a chat session."""
    USER = "user"
    ASSISTANT = "assistant"


class VerificationStatus(str, enum.Enum):
    """Verification report status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ClaimVerdict(str, enum.Enum):
    """Claim verification verdict."""
    SUPPORTED = "supported"
    REFUTED = "refuted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class SourceType(str, enum.Enum):
    """Type of evidence source."""
    WEB = "web"
    DOCUMENT = "document"
    API = "api"
    OTHER = "other"


class User(Base):
    """User account table."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        default=UserRole.USER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"


class ChatSession(Base):
    """Chat session table - a conversation between a user and the AI."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    selected_model: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Message.created_at",
    )

    # Indexes
    __table_args__ = (
        Index("ix_chat_sessions_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title={self.title})>"


class Message(Base):
    """Message table - individual messages within a chat session."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    verification_report: Mapped[Optional["VerificationReport"]] = relationship(
        "VerificationReport",
        back_populates="message",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_messages_session_created", "session_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, session_id={self.session_id}, role={self.role})>"


class VerificationReport(Base):
    """Verification report for an assistant message.

    Each assistant message can have at most one verification report.
    """

    __tablename__ = "verification_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    confidence_score: Mapped[float] = mapped_column(nullable=False)
    hallucination_detected: Mapped[bool] = mapped_column(nullable=False, default=False)
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="verification_report")
    claims: Mapped[list["VerificationClaim"]] = relationship(
        "VerificationClaim",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="VerificationClaim.created_at",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_confidence_score_range"),
    )

    def __repr__(self) -> str:
        return f"<VerificationReport(id={self.id}, message_id={self.message_id}, status={self.status})>"


class VerificationClaim(Base):
    """Individual claim within a verification report."""

    __tablename__ = "verification_claims"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("verification_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[ClaimVerdict] = mapped_column(
        Enum(ClaimVerdict, native_enum=False),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(nullable=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    report: Mapped["VerificationReport"] = relationship("VerificationReport", back_populates="claims")
    evidence_sources: Mapped[list["VerificationEvidence"]] = relationship(
        "VerificationEvidence",
        back_populates="claim",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_claim_confidence_range"),
    )

    def __repr__(self) -> str:
        return f"<VerificationClaim(id={self.id}, report_id={self.report_id}, verdict={self.verdict})>"


class VerificationEvidence(Base):
    """Evidence/source associated with a verification claim."""

    __tablename__ = "verification_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("verification_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False),
        default=SourceType.OTHER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    claim: Mapped["VerificationClaim"] = relationship("VerificationClaim", back_populates="evidence_sources")

    def __repr__(self) -> str:
        return f"<VerificationEvidence(id={self.id}, claim_id={self.claim_id}, type={self.source_type})>"