"""create seo_issues table

Revision ID: 9c0a1b2c3d4e
Revises: 8b9f0a1c2d3e
Create Date: 2026-09-07 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c0a1b2c3d4e'
down_revision: Union[str, None] = '8b9f0a1c2d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('seo_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=True),
        sa.Column('crawl_job_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seo_issues_id'), 'seo_issues', ['id'], unique=False)
    op.create_index(op.f('ix_seo_issues_project_id'), 'seo_issues', ['project_id'], unique=False)
    op.create_index(op.f('ix_seo_issues_page_id'), 'seo_issues', ['page_id'], unique=False)
    op.create_index(op.f('ix_seo_issues_crawl_job_id'), 'seo_issues', ['crawl_job_id'], unique=False)
    op.create_index(op.f('ix_seo_issues_category'), 'seo_issues', ['category'], unique=False)
    op.create_index(op.f('ix_seo_issues_severity'), 'seo_issues', ['severity'], unique=False)
    op.create_index(op.f('ix_seo_issues_code'), 'seo_issues', ['code'], unique=False)
    op.create_index(op.f('ix_seo_issues_status'), 'seo_issues', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_seo_issues_status'), table_name='seo_issues')
    op.drop_index(op.f('ix_seo_issues_code'), table_name='seo_issues')
    op.drop_index(op.f('ix_seo_issues_severity'), table_name='seo_issues')
    op.drop_index(op.f('ix_seo_issues_category'), table_name='seo_issues')
    op.drop_index(op.f('ix_seo_issues_crawl_job_id'), table_name='seo_issues')
    op.drop_index(op.f('ix_seo_issues_page_id'), table_name='seo_issues')
    op.drop_index(op.f('ix_seo_issues_project_id'), table_name='seo_issues')
    op.drop_index(op.f('ix_seo_issues_id'), table_name='seo_issues')
    op.drop_table('seo_issues')
