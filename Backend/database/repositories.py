"""Repository layer for SkepticAI database operations.

Provides data access methods for all entities without exposing
SQLAlchemy internals to the service layer.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from Backend.database.models import (
    User,
    ChatSession,
    Message,
    VerificationReport,
    VerificationClaim,
    VerificationEvidence,
    MessageRole,
    VerificationStatus,
    ClaimVerdict,
    SourceType,
)


class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
    ) -> User:
        """Create a new user."""
        user = User(name=name, email=email, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Update user."""
        user.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete user."""
        await self.session.delete(user)
        await self.session.flush()


class ChatSessionRepository:
    """Repository for chat session operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        selected_model: str,
    ) -> ChatSession:
        """Create a new chat session."""
        chat_session = ChatSession(
            user_id=user_id,
            title=title,
            selected_model=selected_model,
        )
        self.session.add(chat_session)
        await self.session.flush()
        await self.session.refresh(chat_session)
        return chat_session

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[ChatSession]:
        """Get chat session by ID with messages loaded."""
        result = await self.session.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatSession]:
        """Get chat sessions for a user, ordered by most recent first."""
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, chat_session: ChatSession) -> ChatSession:
        """Update chat session."""
        chat_session.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(chat_session)
        return chat_session

    async def delete(self, chat_session: ChatSession) -> None:
        """Delete chat session."""
        await self.session.delete(chat_session)
        await self.session.flush()


class MessageRepository:
    """Repository for message operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        session_id: uuid.UUID,
        role: MessageRole,
        content: str,
        model: Optional[str] = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            model=model,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        """Get message by ID with verification report loaded."""
        result = await self.session.execute(
            select(Message)
            .options(selectinload(Message.verification_report)
                    .selectinload(VerificationReport.claims)
                    .selectinload(VerificationClaim.evidence_sources))
            .where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_by_session(
        self,
        session_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        """Get messages for a session, ordered by creation time."""
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_last_assistant_message(
        self,
        session_id: uuid.UUID,
    ) -> Optional[Message]:
        """Get the most recent assistant message in a session."""
        result = await self.session.execute(
            select(Message)
            .where(
                Message.session_id == session_id,
                Message.role == MessageRole.ASSISTANT,
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class VerificationReportRepository:
    """Repository for verification report operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        message_id: uuid.UUID,
        confidence_score: float,
        hallucination_detected: bool,
        status: VerificationStatus = VerificationStatus.PENDING,
        summary: Optional[str] = None,
    ) -> VerificationReport:
        """Create a new verification report."""
        report = VerificationReport(
            message_id=message_id,
            confidence_score=confidence_score,
            hallucination_detected=hallucination_detected,
            status=status,
            summary=summary,
        )
        self.session.add(report)
        await self.session.flush()
        await self.session.refresh(report)
        return report

    async def get_by_id(self, report_id: uuid.UUID) -> Optional[VerificationReport]:
        """Get verification report by ID with claims and evidence loaded."""
        result = await self.session.execute(
            select(VerificationReport)
            .options(
                selectinload(VerificationReport.claims)
                .selectinload(VerificationClaim.evidence_sources)
            )
            .where(VerificationReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_by_message_id(self, message_id: uuid.UUID) -> Optional[VerificationReport]:
        """Get verification report by message ID."""
        result = await self.session.execute(
            select(VerificationReport)
            .options(
                selectinload(VerificationReport.claims)
                .selectinload(VerificationClaim.evidence_sources)
            )
            .where(VerificationReport.message_id == message_id)
        )
        return result.scalar_one_or_none()

    async def update(self, report: VerificationReport) -> VerificationReport:
        """Update verification report."""
        await self.session.flush()
        await self.session.refresh(report)
        return report

    async def update_status(
        self,
        report_id: uuid.UUID,
        status: VerificationStatus,
        confidence_score: Optional[float] = None,
        hallucination_detected: Optional[bool] = None,
        summary: Optional[str] = None,
    ) -> Optional[VerificationReport]:
        """Update verification report status and optionally other fields."""
        report = await self.get_by_id(report_id)
        if report is None:
            return None

        report.status = status
        if confidence_score is not None:
            report.confidence_score = confidence_score
        if hallucination_detected is not None:
            report.hallucination_detected = hallucination_detected
        if summary is not None:
            report.summary = summary

        await self.session.flush()
        await self.session.refresh(report)
        return report


class VerificationClaimRepository:
    """Repository for verification claim operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        report_id: uuid.UUID,
        claim_text: str,
        verdict: ClaimVerdict,
        confidence: float,
        evidence: Optional[str] = None,
    ) -> VerificationClaim:
        """Create a new verification claim."""
        claim = VerificationClaim(
            report_id=report_id,
            claim_text=claim_text,
            verdict=verdict,
            confidence=confidence,
            evidence=evidence,
        )
        self.session.add(claim)
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def get_by_id(self, claim_id: uuid.UUID) -> Optional[VerificationClaim]:
        """Get verification claim by ID with evidence loaded."""
        result = await self.session.execute(
            select(VerificationClaim)
            .options(selectinload(VerificationClaim.evidence_sources))
            .where(VerificationClaim.id == claim_id)
        )
        return result.scalar_one_or_none()

    async def get_by_report_id(self, report_id: uuid.UUID) -> list[VerificationClaim]:
        """Get all claims for a verification report."""
        result = await self.session.execute(
            select(VerificationClaim)
            .options(selectinload(VerificationClaim.evidence_sources))
            .where(VerificationClaim.report_id == report_id)
            .order_by(VerificationClaim.created_at.asc())
        )
        return list(result.scalars().all())

    async def bulk_create(
        self,
        *,
        report_id: uuid.UUID,
        claims_data: list[dict],
    ) -> list[VerificationClaim]:
        """Create multiple verification claims at once."""
        claims = [
            VerificationClaim(
                report_id=report_id,
                claim_text=data["claim_text"],
                verdict=data["verdict"],
                confidence=data["confidence"],
                evidence=data.get("evidence"),
            )
            for data in claims_data
        ]
        self.session.add_all(claims)
        await self.session.flush()
        for claim in claims:
            await self.session.refresh(claim)
        return claims


class VerificationEvidenceRepository:
    """Repository for verification evidence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        claim_id: uuid.UUID,
        source_title: Optional[str] = None,
        source_url: Optional[str] = None,
        evidence_snippet: Optional[str] = None,
        source_type: SourceType = SourceType.OTHER,
    ) -> VerificationEvidence:
        """Create a new evidence entry."""
        evidence = VerificationEvidence(
            claim_id=claim_id,
            source_title=source_title,
            source_url=source_url,
            evidence_snippet=evidence_snippet,
            source_type=source_type,
        )
        self.session.add(evidence)
        await self.session.flush()
        await self.session.refresh(evidence)
        return evidence

    async def bulk_create(
        self,
        *,
        claim_id: uuid.UUID,
        evidence_list: list[dict],
    ) -> list[VerificationEvidence]:
        """Create multiple evidence entries for a claim."""
        evidence_items = [
            VerificationEvidence(
                claim_id=claim_id,
                source_title=data.get("source_title"),
                source_url=data.get("source_url"),
                evidence_snippet=data.get("evidence_snippet"),
                source_type=data.get("source_type", SourceType.OTHER),
            )
            for data in evidence_list
        ]
        self.session.add_all(evidence_items)
        await self.session.flush()
        for item in evidence_items:
            await self.session.refresh(item)
        return evidence_items

    async def get_by_claim_id(self, claim_id: uuid.UUID) -> list[VerificationEvidence]:
        """Get all evidence for a claim."""
        result = await self.session.execute(
            select(VerificationEvidence)
            .where(VerificationEvidence.claim_id == claim_id)
            .order_by(VerificationEvidence.created_at.asc())
        )
        return list(result.scalars().all())