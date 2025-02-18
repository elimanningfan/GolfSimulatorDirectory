import pandas as pd
from app import app, db, Location
from slugify import slugify
import re
import json
from sqlalchemy import text, inspect
from datetime import datetime
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def parse_hours(hours_str):
    """Convert hours string to JSONB format."""
    if not hours_str or pd.isna(hours_str):
        return None
        
    hours_dict = {}
    for day_hours in hours_str.split('|'):
        day, hours = day_hours.split(':')
        hours_dict[day] = hours.strip()
    return hours_dict

def create_point(lat, lon):
    """Create a string representation of PostgreSQL POINT from latitude and longitude."""
    if pd.isna(lat) or pd.isna(lon):
        return None
    return f"({lat},{lon})"

def setup_database():
    """Initialize the database schema."""
    try:
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return False

def import_locations():
    """Import location data into the database."""
    try:
        # Read the CSV file
        logger.info("Reading locations data from CSV...")
        df = pd.read_csv('data/locations.csv')
        
        # Clear existing data using raw SQL for better performance
        logger.info("Clearing existing data...")
        try:
            db.session.execute(text('DELETE FROM locations'))
            db.session.commit()
        except Exception as e:
            logger.warning(f"Error clearing existing data (this is normal for first run): {str(e)}")
            db.session.rollback()
        
        # Process each row
        logger.info("Processing location data...")
        processed = 0
        skipped = 0
        
        for _, row in df.iterrows():
            try:
                # Skip rows that are clearly example data or invalid
                if pd.isna(row['state']) or row['state'] not in ['OR', 'WA', 'CA', 'ID']:
                    skipped += 1
                    continue
                
                # Skip if essential fields are missing
                if pd.isna(row['name']) or pd.isna(row['full_address']):
                    skipped += 1
                    continue
                    
                # Create slug from business name
                slug = slugify(row['name'])
                
                # Extract zip code from full_address
                zip_match = re.search(r'(\d{5}(?:-\d{4})?)', row['full_address'])
                zip_code = zip_match.group(1) if zip_match else ''
                
                # Try to extract city from full address
                try:
                    city = row['full_address'].split(',')[1].strip() if ',' in row['full_address'] else ''
                except:
                    city = ''
                
                # Parse hours into JSONB
                hours = parse_hours(row['working_hours_old_format'])
                
                # Create POINT from lat/lon
                location = create_point(
                    float(row['latitude']) if pd.notna(row['latitude']) else None,
                    float(row['longitude']) if pd.notna(row['longitude']) else None
                )
                
                # Create metadata JSONB
                location_metadata = {
                    'type': row['type'] if pd.notna(row['type']) else None,
                    'subtypes': row['subtypes'].split(',') if pd.notna(row['subtypes']) else [],
                    'photos_count': int(row['photos_count']) if pd.notna(row['photos_count']) else 0,
                    'place_id': row['place_id'] if pd.notna(row['place_id']) else None,
                    'google_id': row['google_id'] if pd.notna(row['google_id']) else None,
                    'last_synced': datetime.utcnow().isoformat()
                }
                
                # Create location object
                location = Location(
                    business_name=row['name'],
                    address=row['full_address'],
                    city=city,
                    state=row['state'],
                    zip_code=zip_code,
                    phone=str(row['phone']) if pd.notna(row['phone']) else None,
                    website=str(row['site']) if pd.notna(row['site']) else None,
                    description=row['description'] if pd.notna(row['description']) else None,
                    hours=hours,
                    slug=slug,
                    rating=float(row['rating']) if pd.notna(row['rating']) else None,
                    reviews_count=int(row['reviews']) if pd.notna(row['reviews']) else None,
                    reviews_link=str(row['reviews_link']) if pd.notna(row['reviews_link']) else None,
                    location=location,
                    location_metadata=location_metadata
                )
                db.session.add(location)
                processed += 1
                
                # Commit every 100 records
                if processed % 100 == 0:
                    db.session.commit()
                    logger.info(f"Processed {processed} records...")
                
            except Exception as e:
                logger.error(f"Error processing row for {row.get('name', 'unknown')}: {str(e)}")
                skipped += 1
                continue
        
        # Final commit
        db.session.commit()
        logger.info(f"Data import completed. Processed: {processed}, Skipped: {skipped}")
        return True
        
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    with app.app_context():
        # First setup the database
        if not setup_database():
            logger.error("Failed to setup database")
            sys.exit(1)
            
        # Then import the data
        if not import_locations():
            logger.error("Failed to import data")
            sys.exit(1)
            
        logger.info("Import completed successfully")
        sys.exit(0) 