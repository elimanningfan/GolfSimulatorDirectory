import pandas as pd
from app import app, db, Location
from slugify import slugify
import re
import json
from sqlalchemy import text
from datetime import datetime

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
    """Create PostgreSQL POINT from latitude and longitude."""
    if pd.isna(lat) or pd.isna(lon):
        return None
    return f"({lat},{lon})"

def import_locations():
    with app.app_context():
        # Read the CSV file
        df = pd.read_csv('data/locations.csv')
        
        # Clear existing data
        db.session.execute(text('TRUNCATE TABLE locations CASCADE'))
        
        # Process each row
        for _, row in df.iterrows():
            # Skip rows that are clearly example data or invalid
            if pd.isna(row['state']) or row['state'] not in ['OR', 'WA', 'CA', 'ID']:
                continue
            
            # Skip if essential fields are missing
            if pd.isna(row['name']) or pd.isna(row['full_address']):
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
            metadata = {
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
                metadata=metadata
            )
            db.session.add(location)
        
        # Commit all changes
        db.session.commit()
        print("Data import completed successfully!")

if __name__ == "__main__":
    import_locations() 