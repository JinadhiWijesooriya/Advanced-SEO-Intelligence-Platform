"""create crawl_tasks table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('crawl_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crawl_job_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crawl_tasks_id'), 'crawl_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_crawl_tasks_crawl_job_id'), 'crawl_tasks', ['crawl_job_id'], unique=False)
    op.create_index(op.f('ix_crawl_tasks_url'), 'crawl_tasks', ['url'], unique=False)
    op.create_index(op.f('ix_crawl_tasks_status'), 'crawl_tasks', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_crawl_tasks_status'), table_name='crawl_tasks')
    op.drop_index(op.f('ix_crawl_tasks_url'), table_name='crawl_tasks')
    op.drop_index(op.f('ix_crawl_tasks_crawl_job_id'), table_name='crawl_tasks')
    op.drop_index(op.f('ix_crawl_tasks_id'), table_name='crawl_tasks')
    op.drop_table('crawl_tasks')
