"""create crawler tables (crawl_jobs, pages, links, images)

Revision ID: 8b9f0a1c2d3e
Revises: 7a8e9f01b2c3
Create Date: 2026-09-07 10:21:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b9f0a1c2d3e'
down_revision: Union[str, None] = '7a8e9f01b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. crawl_jobs table
    op.create_table('crawl_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_urls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_urls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_urls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crawl_jobs_id'), 'crawl_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_crawl_jobs_project_id'), 'crawl_jobs', ['project_id'], unique=False)
    op.create_index(op.f('ix_crawl_jobs_status'), 'crawl_jobs', ['status'], unique=False)

    # 2. pages table
    op.create_table('pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('crawl_job_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('canonical_url', sa.String(length=1024), nullable=True),
        sa.Column('h1_tags', sa.Text(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('crawled_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pages_id'), 'pages', ['id'], unique=False)
    op.create_index(op.f('ix_pages_project_id'), 'pages', ['project_id'], unique=False)
    op.create_index(op.f('ix_pages_crawl_job_id'), 'pages', ['crawl_job_id'], unique=False)
    op.create_index(op.f('ix_pages_url'), 'pages', ['url'], unique=False)

    # 3. links table
    op.create_table('links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('source_url', sa.String(length=1024), nullable=False),
        sa.Column('target_url', sa.String(length=1024), nullable=False),
        sa.Column('link_type', sa.String(length=20), nullable=False, server_default='internal'),
        sa.Column('anchor_text', sa.Text(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('is_broken', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_links_id'), 'links', ['id'], unique=False)
    op.create_index(op.f('ix_links_page_id'), 'links', ['page_id'], unique=False)

    # 4. images table
    op.create_table('images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('alt_text', sa.Text(), nullable=True),
        sa.Column('has_alt', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_images_id'), 'images', ['id'], unique=False)
    op.create_index(op.f('ix_images_page_id'), 'images', ['page_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_images_page_id'), table_name='images')
    op.drop_index(op.f('ix_images_id'), table_name='images')
    op.drop_table('images')

    op.drop_index(op.f('ix_links_page_id'), table_name='links')
    op.drop_index(op.f('ix_links_id'), table_name='links')
    op.drop_table('links')

    op.drop_index(op.f('ix_pages_url'), table_name='pages')
    op.drop_index(op.f('ix_pages_crawl_job_id'), table_name='pages')
    op.drop_index(op.f('ix_pages_project_id'), table_name='pages')
    op.drop_index(op.f('ix_pages_id'), table_name='pages')
    op.drop_table('pages')

    op.drop_index(op.f('ix_crawl_jobs_status'), table_name='crawl_jobs')
    op.drop_index(op.f('ix_crawl_jobs_project_id'), table_name='crawl_jobs')
    op.drop_index(op.f('ix_crawl_jobs_id'), table_name='crawl_jobs')
    op.drop_table('crawl_jobs')
