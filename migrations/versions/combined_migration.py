"""combined migration

Revision ID: combined_migration
Revises: 
Create Date: 2025-02-18 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'combined_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('location',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(length=500), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('city', sa.String(length=200), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('zip_code', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hours', sa.String(length=1000), nullable=True),
        sa.Column('slug', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('reviews', sa.Integer(), nullable=True),
        sa.Column('reviews_link', sa.String(length=1000), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('membership_info', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

def downgrade():
    op.drop_table('location') 