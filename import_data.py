import pandas as pd
from app import app, db, Location
from slugify import slugify
import re
import json
from sqlalchemy import text
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
    try:
        if isinstance(hours_str, str):
            # Try to parse the JSON string
            if hours_str.startswith('{'):
                return json.loads(hours_str.replace("'", '"'))
            # Parse the old format (pipe-separated)
            hours_dict = {}
            for pair in hours_str.split('|'):
                if ':' in pair:
                    day, time = pair.split(':', 1)
                    hours_dict[day] = time
            return hours_dict if hours_dict else None
    except Exception as e:
        logger.warning(f"Error parsing hours: {str(e)}")
        return None
    return None

def extract_city_from_address(full_address):
    """Extract city from full address."""
    if pd.isna(full_address):
        return None
    # Expected format: "street, city, state zip"
    parts = full_address.split(',')
    if len(parts) >= 2:
        city = parts[1].strip()
        # Remove state and zip if they're in the city part
        city = city.split(' ')[0]
        return city
    return None

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
        logger.info(f"CSV columns found: {', '.join(df.columns)}")
        
        # Clear existing data
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
                # Extract city from full address if needed
                city = extract_city_from_address(row['full_address'])
                if not city:
                    logger.warning(f"Could not extract city from address: {row['full_address']}")
                    continue

                # Create slug from business name
                slug = slugify(row['name'])
                
                # Parse hours
                hours = parse_hours(row.get('working_hours') or row.get('working_hours_old_format'))
                
                # Create location object
                location = Location(
                    business_name=row['name'],
                    address=row['full_address'],
                    city=city,
                    state=row['state'][:2] if pd.notna(row['state']) else None,  # Take first 2 chars of state
                    zip_code=row['full_address'].split()[-1] if pd.notna(row['full_address']) else None,
                    phone=str(row['phone']) if pd.notna(row['phone']) else None,
                    website=str(row['site']) if pd.notna(row['site']) else None,
                    description=row['description'] if pd.notna(row['description']) else None,
                    hours=hours,
                    slug=slug,
                    rating=float(row['rating']) if pd.notna(row['rating']) else None,
                    reviews_count=int(row['reviews']) if pd.notna(row['reviews']) else None,
                    reviews_link=str(row['reviews_link']) if pd.notna(row['reviews_link']) else None,
                    location=create_point(
                        float(row['latitude']) if pd.notna(row['latitude']) else None,
                        float(row['longitude']) if pd.notna(row['longitude']) else None
                    ),
                    location_metadata={
                        'type': row['type'] if pd.notna(row['type']) else None,
                        'subtypes': row['subtypes'].split(',') if pd.notna(row['subtypes']) else [],
                        'photos_count': int(row['photos_count']) if pd.notna(row['photos_count']) else 0,
                        'place_id': row['place_id'] if pd.notna(row['place_id']) else None,
                        'google_id': row['google_id'] if pd.notna(row['google_id']) else None,
                        'last_synced': datetime.utcnow().isoformat()
                    }
                )
                
                db.session.add(location)
                processed += 1
                logger.info(f"Successfully processed: {row['name']}")
                
                # Commit every 50 records
                if processed % 50 == 0:
                    db.session.commit()
                    logger.info(f"Processed {processed} records...")
                
            except Exception as e:
                logger.error(f"Error processing row for {row.get('name', 'unknown')}: {str(e)}")
                logger.error(f"Row data: {row.to_dict()}")
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