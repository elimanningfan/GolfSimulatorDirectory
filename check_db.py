from app import app, db, Location

with app.app_context():
    locations = Location.query.all()
    print(f"Total locations: {len(locations)}")
    print("\nFirst 3 locations:")
    for location in locations[:3]:
        print(f"- {location.business_name} ({location.city}, {location.state})") 