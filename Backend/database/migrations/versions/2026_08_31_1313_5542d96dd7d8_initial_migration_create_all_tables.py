"""Initial migration: create all tables

Revision ID: 5542d96dd7d8
Revises: 
Create Date: 2026-08-31 13:13:36.166935+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5542d96dd7d8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('selected_model', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'], unique=False)
    op.create_index('ix_chat_sessions_user_created', 'chat_sessions', ['user_id', 'created_at'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_session_id', 'messages', ['session_id'], unique=False)
    op.create_index('ix_messages_session_created', 'messages', ['session_id', 'created_at'], unique=False)

    # Create verification_reports table
    op.create_table(
        'verification_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('hallucination_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id'),
        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='ck_confidence_score_range'),
    )
    op.create_index('ix_verification_reports_message_id', 'verification_reports', ['message_id'], unique=True)

    # Create verification_claims table
    op.create_table(
        'verification_claims',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('verdict', sa.String(length=30), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['verification_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_claim_confidence_range'),
    )
    op.create_index('ix_verification_claims_report_id', 'verification_claims', ['report_id'], unique=False)

    # Create verification_evidence table
    op.create_table(
        'verification_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_title', sa.String(length=500), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('evidence_snippet', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=20), nullable=False, server_default='other'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['verification_claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_verification_evidence_claim_id', 'verification_evidence', ['claim_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_verification_evidence_claim_id', table_name='verification_evidence')
    op.drop_table('verification_evidence')
    op.drop_index('ix_verification_claims_report_id', table_name='verification_claims')
    op.drop_table('verification_claims')
    op.drop_index('ix_verification_reports_message_id', table_name='verification_reports')
    op.drop_table('verification_reports')
    op.drop_index('ix_messages_session_created', table_name='messages')
    op.drop_index('ix_messages_session_id', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_chat_sessions_user_created', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')