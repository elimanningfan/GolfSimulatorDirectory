"""postgres native migration

Revision ID: postgres_native_migration
Revises: 
Create Date: 2025-02-18 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'postgres_native_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    op.execute("CREATE TYPE state_code AS ENUM ('OR', 'WA', 'CA', 'ID')")
    
    # Create the locations table with PostgreSQL-specific features
    op.create_table('locations',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('business_name', sa.Text(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('city', sa.Text(), nullable=False),
        sa.Column('state', postgresql.ENUM('OR', 'WA', 'CA', 'ID', name='state_code'), nullable=False),
        sa.Column('zip_code', sa.String(length=10), nullable=False),
        sa.Column('phone', sa.String(length=20)),
        sa.Column('website', sa.Text()),
        sa.Column('description', sa.Text()),
        sa.Column('hours', postgresql.JSONB()),
        sa.Column('slug', sa.Text(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('rating', postgresql.NUMERIC(3,2)),
        sa.Column('reviews_count', sa.Integer()),
        sa.Column('reviews_link', sa.Text()),
        sa.Column('location', sa.String(50)),  # Store as "(lat,lon)" string
        sa.Column('metadata', postgresql.JSONB()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        postgresql.ExcludeConstraint(
            ('slug', '='),
            using='btree'
        )
    )
    
    # Add indexes
    op.create_index('idx_locations_business_name', 'locations', ['business_name'])
    op.create_index('idx_locations_city', 'locations', ['city'])
    op.create_index('idx_locations_state', 'locations', ['state'])
    op.create_index('idx_locations_rating', 'locations', ['rating'])
    
    # Add trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_locations_updated_at
            BEFORE UPDATE ON locations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

def downgrade():
    op.drop_table('locations')
    op.execute("DROP TYPE state_code")
    op.execute("DROP FUNCTION update_updated_at_column()") 