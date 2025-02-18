"""Initial migration

Revision ID: 1e979bf1a76c
Revises: 
Create Date: 2024-02-17 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e979bf1a76c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create Location table
    op.create_table('location',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(length=200), nullable=False),
        sa.Column('address', sa.String(length=200), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('zip_code', sa.String(length=20), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('website', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hours', sa.String(length=500), nullable=True),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('reviews', sa.Integer(), nullable=True),
        sa.Column('reviews_link', sa.String(length=500), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('membership_info', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )


def downgrade():
    op.drop_table('location') 