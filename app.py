import os
import logging
from datetime import datetime
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PG_ENUM
from sqlalchemy.types import TypeDecorator, String
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Database configuration
database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/golf_simulators')

try:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info(f"Using PostgreSQL database: {database_url}")
except Exception as e:
    logger.error(f"Error configuring database URL: {str(e)}")
    raise

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
logger.info("Database extensions initialized successfully")

@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error occurred: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

# Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaDzWL2-rrIKWpvCjGYiuF9ovmbwYfYSM5q_4YTuwG7_vPOsH7P0uVeVmfzpuQG3igxhW5nnwM3AMS/pub?output=csv"

class POINT(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)  # Format: "(lat,lon)"

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Remove parentheses and split into lat,lon
        coords = value.strip('()').split(',')
        return {'latitude': float(coords[0]), 'longitude': float(coords[1])}

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'))
    business_name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.Text, nullable=False)
    state = db.Column(PG_ENUM('OR', 'WA', 'CA', 'ID', name='state_code'), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20))
    website = db.Column(db.Text)
    description = db.Column(db.Text)
    hours = db.Column(JSONB)
    slug = db.Column(db.Text, nullable=False, unique=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
    rating = db.Column(db.Numeric(3,2))
    reviews_count = db.Column(db.Integer)
    reviews_link = db.Column(db.Text)
    location = db.Column(POINT)
    location_metadata = db.Column(JSONB)

    def to_dict(self):
        return {
            'id': str(self.id),
            'business_name': self.business_name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'website': self.website,
            'description': self.description,
            'hours': self.hours,
            'slug': self.slug,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'rating': float(self.rating) if self.rating else None,
            'reviews_count': self.reviews_count,
            'reviews_link': self.reviews_link,
            'location': self.location,
            'location_metadata': self.location_metadata
        }

@app.route('/')
def home():
    try:
        locations = Location.query.all()
        logger.info(f"Retrieved {len(locations)} locations for home page")
        return render_template('home.html', locations=locations)
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/location/<slug>')
def location_detail(slug):
    try:
        location = Location.query.filter_by(slug=slug).first_or_404()
        logger.info(f"Retrieved location details for slug: {slug}")
        return render_template('location_detail.html', location=location)
    except Exception as e:
        logger.error(f"Error in location_detail route for slug {slug}: {str(e)}")
        return render_template('500.html'), 500

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    locations = Location.query.all()
    filtered_locations = [loc for loc in locations if query in loc.business_name.lower() or query in loc.city.lower()]
    return render_template('search_results.html', locations=filtered_locations, query=query)

def create_slug(business_name):
    # Convert to lowercase and replace spaces with hyphens
    slug = business_name.lower().replace(' ', '-')
    # Remove any special characters
    slug = ''.join(e for e in slug if e.isalnum() or e == '-')
    return slug

def create_city_slug(city, state):
    # Convert to lowercase and replace spaces with hyphens
    city_slug = city.lower().replace(' ', '-')
    state_slug = state.lower().replace(' ', '-')
    # Remove any special characters
    city_slug = ''.join(e for e in city_slug if e.isalnum() or e == '-')
    state_slug = ''.join(e for e in state_slug if e.isalnum() or e == '-')
    return f"{city_slug}-{state_slug}"

@app.route('/city/<city_slug>')
def city_detail(city_slug):
    # Split the slug into city and state
    try:
        # First split off the state code (last 2-3 characters after last hyphen)
        parts = city_slug.rsplit('-', 1)
        if len(parts) != 2:
            return render_template('404.html'), 404
            
        city_slug_part, state_code = parts
        
        # Convert city slug back to display format
        city_display = ' '.join(word.capitalize() for word in city_slug_part.split('-'))
        state_display = state_code.upper()
        
        # Query locations for this city
        locations = Location.query.filter(
            Location.city.ilike(city_display),
            Location.state == state_display  # Changed from ilike to == for enum
        ).all()
        
        if not locations:
            return render_template('404.html'), 404
            
        return render_template('city_detail.html',
                             locations=locations,
                             city_name=city_display,
                             state_name=state_display,
                             location_count=len(locations))
    except ValueError:
        return render_template('404.html'), 404

@app.route('/cities')
def city_list():
    # Get unique cities with their location counts
    cities = db.session.query(
        Location.city,
        Location.state,
        db.func.count(Location.id).label('location_count')
    ).group_by(Location.city, Location.state).all()
    
    # Format cities with their slugs
    formatted_cities = [
        {
            'city': city,
            'state': state,
            'count': count,
            'slug': create_city_slug(city, state)
        }
        for city, state, count in cities
    ]
    
    return render_template('city_list.html', cities=formatted_cities)

def sync_with_google_sheet():
    """
    Sync database with Google Sheet data
    """
    try:
        logger.info("Starting sync with Google Sheet")
        # Read the CSV data from Google Sheets
        df = pd.read_csv(SHEET_URL)
        
        # Map the Google Sheet columns to our database columns
        column_mapping = {
            'name': 'business_name',
            'full_address': 'address',
            'state': 'state',
            'phone': 'phone',
            'site': 'website',
            'description': 'description',
            'working_hours': 'hours',
            'rating': 'rating',
            'reviews': 'reviews_count',
            'reviews_link': 'reviews_link',
            'latitude': 'location',
            'longitude': 'location'
        }
        
        # Rename columns according to our mapping
        df = df.rename(columns=column_mapping)
        
        # Extract city and zip code from full_address
        df['address'] = df['address'].fillna('')
        df[['city', 'zip_code']] = df['address'].str.extract(r'(?:.*),\s*(.*?),\s*\w+\s+(\d{5})')
        
        current_time = datetime.utcnow()
        updates = 0
        new_records = 0
        
        for _, row in df.iterrows():
            # Create slug for the business
            business_slug = create_slug(row['business_name'])
            
            # Check if location exists
            location = Location.query.filter_by(slug=business_slug).first()
            
            # Prepare location data
            location_data = {
                'business_name': row['business_name'],
                'address': row['address'],
                'city': row['city'],
                'state': row['state'],
                'zip_code': str(row['zip_code']),
                'phone': str(row['phone']) if pd.notna(row['phone']) else None,
                'website': row['website'] if pd.notna(row['website']) else None,
                'description': row['description'] if pd.notna(row['description']) else None,
                'hours': row['hours'] if pd.notna(row['hours']) else None,
                'rating': float(row['rating']) if pd.notna(row['rating']) else None,
                'reviews_count': int(row['reviews_count']) if pd.notna(row['reviews_count']) else None,
                'reviews_link': row['reviews_link'] if pd.notna(row['reviews_link']) else None,
                'location': row['location'] if pd.notna(row['location']) else None,
                'updated_at': current_time
            }
            
            if location:
                # Update existing location
                for key, value in location_data.items():
                    setattr(location, key, value)
                updates += 1
            else:
                # Create new location
                location_data['slug'] = business_slug
                new_location = Location(**location_data)
                db.session.add(new_location)
                new_records += 1
        
        db.session.commit()
        logger.info(f"Sync completed. Updated {updates} records, added {new_records} new records.")
        return True
        
    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        db.session.rollback()
        return False

@app.cli.command("sync-sheet")
def sync_sheet_command():
    """Manually trigger Google Sheet sync."""
    logger.info("Starting manual sync with Google Sheet")
    if sync_with_google_sheet():
        logger.info("Manual sync completed successfully")
    else:
        logger.error("Manual sync failed")

if __name__ == '__main__':
    app.run(debug=True) 