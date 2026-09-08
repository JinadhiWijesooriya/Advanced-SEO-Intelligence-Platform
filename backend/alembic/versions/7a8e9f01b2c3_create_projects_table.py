"""create projects table

Revision ID: 7a8e9f01b2c3
Revises: 495ee205c232
Create Date: 2026-09-07 10:13:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8e9f01b2c3'
down_revision: Union[str, None] = '495ee205c232'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('target_url', sa.String(length=1024), nullable=False),
        sa.Column('max_crawl_pages', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('max_crawl_depth', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('custom_user_agent', sa.String(length=255), nullable=False, server_default='SEOIntelligenceBot/1.0'),
        sa.Column('respect_robots_txt', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_projects_user_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
