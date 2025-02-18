import pandas as pd
from app import app, db, Location
from slugify import slugify
import re

def extract_zip_code(address):
    # Try to extract zip code from address
    zip_match = re.search(r'(\d{5}(?:-\d{4})?)', address)
    return zip_match.group(1) if zip_match else ''

def import_locations():
    with app.app_context():
        # Read the CSV file
        df = pd.read_csv('data/locations.csv')
        
        # Clear existing data
        Location.query.delete()
        
        # Process each row
        for _, row in df.iterrows():
            # Skip rows that are clearly example data or invalid
            if pd.isna(row['state']) or row['state'] == 'CA' or len(row['state']) > 20:
                continue
            
            # Skip if essential fields are missing
            if pd.isna(row['name']) or pd.isna(row['full_address']):
                continue
                
            # Create slug from business name
            slug = slugify(row['name'])
            
            # Extract zip code from full_address
            zip_code = extract_zip_code(row['full_address'])
            
            # Try to extract city from full address
            try:
                city = row['full_address'].split(',')[1].strip() if ',' in row['full_address'] else ''
            except:
                city = ''
            
            # Create location object
            location = Location(
                business_name=row['name'][:500],  # Truncate if too long
                address=row['full_address'][:500],
                city=city[:200],
                state=row['state'][:100],
                zip_code=zip_code[:50],
                phone=str(row['phone'])[:50] if pd.notna(row['phone']) else None,
                website=str(row['site'])[:500] if pd.notna(row['site']) else None,
                description=row['description'] if pd.notna(row['description']) else None,
                hours=row['working_hours_old_format'][:1000] if pd.notna(row['working_hours_old_format']) else None,
                slug=slug[:500],
                rating=float(row['rating']) if pd.notna(row['rating']) else None,
                reviews=int(row['reviews']) if pd.notna(row['reviews']) else None,
                reviews_link=str(row['reviews_link'])[:1000] if pd.notna(row['reviews_link']) else None,
                latitude=float(row['latitude']) if pd.notna(row['latitude']) else None,
                longitude=float(row['longitude']) if pd.notna(row['longitude']) else None
            )
            db.session.add(location)
        
        # Commit all changes
        db.session.commit()
        print("Data import completed successfully!")

if __name__ == "__main__":
    import_locations() 