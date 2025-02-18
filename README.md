# Golf Simulator Directory

A web-based directory for golf simulator rental locations, optimized for SEO with individual URLs for each business location. The directory is built with Flask and provides a clean, modern interface for users to find golf simulator facilities in their area.

## Features

- Searchable directory of golf simulator rental locations
- Individual detail pages for each business with unique URLs
- SEO-optimized page structure and content
- Import business data from CSV file
- Modern, responsive design
- Google Maps integration for location visualization
- Schema.org markup for enhanced SEO

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd golf-simulator-directory
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

## Data Import

1. Prepare your CSV file with the following columns:
   - business_name
   - address
   - city
   - state
   - zip_code
   - phone (optional)
   - website (optional)
   - description (optional)
   - hours (optional)

2. Place your CSV file in the `data` directory as `locations.csv`

3. Import the data:
```bash
flask import-csv
```

## Configuration

1. Create a `.env` file in the project root:
```
FLASK_APP=app.py
FLASK_ENV=development
GOOGLE_MAPS_API_KEY=your_api_key_here
```

2. Replace `your_api_key_here` with your Google Maps API key

## Running the Application

1. Start the development server:
```bash
flask run
```

2. Visit `http://localhost:5000` in your web browser

## Production Deployment

For production deployment:

1. Set appropriate environment variables:
```bash
export FLASK_ENV=production
export FLASK_APP=app.py
```

2. Use a production-grade WSGI server:
```bash
gunicorn app:app
```

## SEO Features

- Unique, descriptive titles for each page
- Meta descriptions optimized for search engines
- Schema.org markup for local businesses
- Clean URL structure with business slugs
- Semantic HTML structure
- Mobile-friendly responsive design

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 