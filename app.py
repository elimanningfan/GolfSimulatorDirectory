from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os
from config import Config
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Database configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Replace postgres:// with postgresql:// for SQLAlchemy
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # For local development, use SQLite with absolute path
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "golf_simulators.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reloading
app.debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'  # Enable debug mode
db = SQLAlchemy(app)
scheduler = APScheduler()

migrate = Migrate(app, db)

# Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaDzWL2-rrIKWpvCjGYiuF9ovmbwYfYSM5q_4YTuwG7_vPOsH7P0uVeVmfzpuQG3igxhW5nnwM3AMS/pub?output=csv"

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    hours = db.Column(db.String(500))
    slug = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Float)
    reviews = db.Column(db.Integer)
    reviews_link = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    membership_info = db.Column(db.Text)
    last_synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
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
            'rating': self.rating,
            'reviews': self.reviews,
            'reviews_link': self.reviews_link,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'membership_info': self.membership_info
        }

@app.route('/')
def home():
    locations = Location.query.all()
    return render_template('home.html', locations=locations)

@app.route('/location/<slug>')
def location_detail(slug):
    location = Location.query.filter_by(slug=slug).first_or_404()
    return render_template('location_detail.html', location=location)

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
            Location.state.ilike(state_display)
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
            'reviews': 'reviews',
            'reviews_link': 'reviews_link',
            'latitude': 'latitude',
            'longitude': 'longitude'
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
                'reviews': int(row['reviews']) if pd.notna(row['reviews']) else None,
                'reviews_link': row['reviews_link'] if pd.notna(row['reviews_link']) else None,
                'latitude': float(row['latitude']) if pd.notna(row['latitude']) else None,
                'longitude': float(row['longitude']) if pd.notna(row['longitude']) else None,
                'last_synced_at': current_time
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

# Schedule configuration
app.config['SCHEDULER_API_ENABLED'] = True

@scheduler.task('interval', id='sync_sheet', hours=1, misfire_grace_time=900)
def scheduled_sync():
    """
    Scheduled task to sync with Google Sheet every hour
    """
    sync_with_google_sheet()

# Start the scheduler
scheduler.init_app(app)
scheduler.start()

@app.cli.command("import-csv")
def import_csv():
    """Import locations from CSV file."""
    if not os.path.exists('data/locations.csv'):
        print("CSV file not found!")
        return
    
    try:
        df = pd.read_csv('data/locations.csv')
        print(f"Found {len(df)} locations to import")
        
        for index, row in df.iterrows():
            try:
                # Extract address components from full_address
                full_address = row['full_address']
                print(f"Processing address: {full_address}")
                
                address_parts = full_address.split(',')
                if len(address_parts) < 3:
                    print(f"Skipping row {index}: Invalid address format")
                    continue
                
                address = address_parts[0].strip()
                city = address_parts[1].strip()
                state_zip = address_parts[2].strip().split()
                
                if len(state_zip) < 2:
                    print(f"Skipping row {index}: Invalid state/zip format")
                    continue
                
                state = state_zip[0]
                zip_code = state_zip[1]

                # Create location object
                location = Location(
                    business_name=row['name'],
                    address=address,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    phone=row.get('phone', ''),
                    website=row.get('site', ''),
                    description=row.get('description', ''),
                    hours=row.get('working_hours_old_format', ''),
                    slug=create_slug(row['name']),
                    rating=row.get('rating', None),
                    reviews=row.get('reviews', 0),
                    reviews_link=row.get('reviews_link', ''),
                    latitude=row.get('latitude', None),
                    longitude=row.get('longitude', None),
                    membership_info=row.get('membership_info', '')
                )
                db.session.add(location)
                print(f"Added location: {location.business_name}")
            
            except Exception as row_error:
                print(f"Error processing row {index}: {str(row_error)}")
                continue
        
        db.session.commit()
        print("Data imported successfully!")
    except Exception as e:
        print(f"Error importing data: {str(e)}")
        db.session.rollback()

@app.cli.command("sync-sheet")
def sync_sheet_command():
    """Manually trigger Google Sheet sync."""
    logger.info("Starting manual sync with Google Sheet")
    if sync_with_google_sheet():
        logger.info("Manual sync completed successfully")
    else:
        logger.error("Manual sync failed")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 