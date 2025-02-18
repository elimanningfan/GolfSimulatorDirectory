import pandas as pd
from app import app, db, Location
from slugify import slugify

def import_locations():
    with app.app_context():
        # Read the CSV file
        df = pd.read_csv('data/locations.csv')
        
        # Clear existing data
        Location.query.delete()
        
        # Process each row
        for _, row in df.iterrows():
            # Create slug from business name
            slug = slugify(row['name'])
            
            # Create location object
            location = Location(
                business_name=row['name'],
                address=row['full_address'],
                city=row['city'] if pd.notna(row['city']) else '',
                state=row['state'] if pd.notna(row['state']) else '',
                zip_code='',  # You might want to extract this from full_address
                phone=row['phone'] if pd.notna(row['phone']) else None,
                website=row['site'] if pd.notna(row['site']) else None,
                description=row['description'] if pd.notna(row['description']) else None,
                hours=row['working_hours'] if pd.notna(row['working_hours']) else None,
                slug=slug,
                rating=float(row['rating']) if pd.notna(row['rating']) else None,
                reviews=int(row['reviews']) if pd.notna(row['reviews']) else None,
                reviews_link=row['reviews_link'] if pd.notna(row['reviews_link']) else None,
                latitude=float(row['latitude']) if pd.notna(row['latitude']) else None,
                longitude=float(row['longitude']) if pd.notna(row['longitude']) else None
            )
            db.session.add(location)
        
        # Commit all changes
        db.session.commit()
        print("Data import completed successfully!")

if __name__ == "__main__":
    import_locations() 