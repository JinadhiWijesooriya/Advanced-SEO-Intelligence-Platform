"""create seo_results table

Revision ID: a1b2c3d4e5f6
Revises: 9c0a1b2c3d4e
Create Date: 2026-09-07 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9c0a1b2c3d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('seo_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('crawl_job_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('technical_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('onpage_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('content_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('link_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('performance_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('mobile_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seo_results_id'), 'seo_results', ['id'], unique=False)
    op.create_index(op.f('ix_seo_results_page_id'), 'seo_results', ['page_id'], unique=True)
    op.create_index(op.f('ix_seo_results_project_id'), 'seo_results', ['project_id'], unique=False)
    op.create_index(op.f('ix_seo_results_crawl_job_id'), 'seo_results', ['crawl_job_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_seo_results_crawl_job_id'), table_name='seo_results')
    op.drop_index(op.f('ix_seo_results_project_id'), table_name='seo_results')
    op.drop_index(op.f('ix_seo_results_page_id'), table_name='seo_results')
    op.drop_index(op.f('ix_seo_results_id'), table_name='seo_results')
    op.drop_table('seo_results')
