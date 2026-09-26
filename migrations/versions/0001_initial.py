"""Initial IP-SAKTI schema."""
from alembic import op, context
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _embedding_type():
    if context.get_context().dialect.name == "postgresql":
        try:
            from pgvector.sqlalchemy import Vector
            return Vector(384)
        except Exception:
            pass
    return sa.JSON()


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    emb = _embedding_type()
    op.create_table("legal_documents",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.String(200), unique=True, index=True),
        sa.Column("canonical_url", sa.Text(), nullable=False), sa.Column("title", sa.Text(), nullable=False), sa.Column("authority", sa.String(200), nullable=False),
        sa.Column("authority_level", sa.String(30), nullable=False, server_default="tier_1"), sa.Column("jurisdiction", sa.String(50), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=False), sa.Column("access_level", sa.String(30), nullable=False, server_default="PUBLIC"),
        sa.Column("content_hash", sa.String(64)), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("legal_versions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.String(200), index=True, nullable=False),
        sa.Column("version", sa.String(100), nullable=False), sa.Column("effective_from", sa.DateTime()), sa.Column("effective_to", sa.DateTime()),
        sa.Column("status", sa.String(30), nullable=False, server_default="current"), sa.Column("previous_hash", sa.String(64)), sa.Column("content_hash", sa.String(64)))
    op.create_table("legal_provisions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("chunk_id", sa.String(150), unique=True, index=True, nullable=False),
        sa.Column("source_id", sa.String(200), index=True, nullable=False), sa.Column("document_title", sa.Text(), nullable=False),
        sa.Column("authority", sa.String(200), nullable=False), sa.Column("authority_level", sa.String(30), nullable=False, server_default="tier_1"),
        sa.Column("jurisdiction", sa.String(50), index=True, nullable=False), sa.Column("regime", sa.String(100), index=True, nullable=False),
        sa.Column("instrument", sa.Text(), nullable=False), sa.Column("section", sa.String(100), index=True), sa.Column("subsection", sa.String(100)),
        sa.Column("article", sa.String(100)), sa.Column("chapter", sa.String(100)), sa.Column("paragraph", sa.String(100)), sa.Column("page", sa.Integer()),
        sa.Column("language", sa.String(20), nullable=False, server_default="en"), sa.Column("published_at", sa.DateTime()), sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_to", sa.DateTime()), sa.Column("version", sa.String(100)), sa.Column("status", sa.String(30), nullable=False, server_default="current"),
        sa.Column("citation", sa.Text(), nullable=False), sa.Column("access_level", sa.String(30), nullable=False, server_default="PUBLIC"),
        sa.Column("source_url", sa.Text(), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("embedding", emb),
        sa.Column("demo_only", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_provision_jurisdiction_status", "legal_provisions", ["jurisdiction", "status"])
    op.create_table("innovation_profiles",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("profile_id", sa.String(100), unique=True, index=True, nullable=False),
        sa.Column("user_id", sa.String(100), index=True, nullable=False), sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("memories",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("memory_id", sa.String(100), unique=True, index=True, nullable=False),
        sa.Column("user_id", sa.String(100), index=True, nullable=False), sa.Column("memory_type", sa.String(50), index=True, nullable=False),
        sa.Column("key", sa.String(200), index=True, nullable=False), sa.Column("value", sa.JSON(), nullable=False), sa.Column("source", sa.String(50), nullable=False, server_default="user"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"), sa.Column("expires_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("audit_events",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("trace_id", sa.String(100), index=True, nullable=False),
        sa.Column("user_id", sa.String(100), index=True, nullable=False), sa.Column("event_type", sa.String(100), index=True, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade():
    op.drop_table("audit_events")
    op.drop_table("memories")
    op.drop_table("innovation_profiles")
    op.drop_index("ix_provision_jurisdiction_status", table_name="legal_provisions")
    op.drop_table("legal_provisions")
    op.drop_table("legal_versions")
    op.drop_table("legal_documents")
