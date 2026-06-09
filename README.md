# Spool Tracker - 3D Printer Filament Management

A Flask web application for tracking 3D printer filament spools, recording print usage, and viewing statistics.

## Features

- **Multi-user Authentication** - Secure user registration and login
- **Filament Management** - Add, edit, and archive filament spools
- **Usage Tracking** - Record weight used for each print job
- **Smart Archive** - Automatically archive empty spools
- **Overflow Handling** - Link new spools when usage exceeds remaining weight
- **Print History** - View complete usage history for each spool
- **Statistics Dashboard** - Visualize usage by type, color, and more
- **Low Filament Warnings** - Get alerts when spools are running low (<20%)
- **Search & Filter** - Easily find filaments by type or color
- **Responsive UI** - Bootstrap 5 interface works on all devices
- **Docker Ready** - Fully containerized for easy deployment

## Technology Stack

- **Backend**: Flask 3.0, SQLAlchemy, Flask-Login, Flask-Migrate
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: Bootstrap 5, Chart.js
- **Forms**: Flask-WTF, WTForms
- **Deployment**: Docker, Gunicorn

## Quick Start

### Option 1: Docker (Recommended)

```powershell
# Build and start the container
docker-compose up -d

# Access the application
# Open browser to http://localhost:5000
```

That's it! The database will be automatically initialized on first run.

### Option 2: Local Development

1. **Create virtual environment**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Install dependencies**

```powershell
pip install -r requirements.txt
```

3. **Initialize database**

```powershell
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. **Run the application**

```powershell
python run.py
```

5. **Access the application**

- Open browser to http://localhost:5000

## Usage Guide

### First Time Setup

1. Register a new account at `/auth/register`
2. Log in with your credentials
3. Add your first filament spool

### Adding Filament

1. Click "Add Filament" button
2. Enter filament type (e.g., "PLA Matte", "PETG")
3. Enter color (e.g., "Red", "Blue")
4. Enter starting weight in grams (typically 1000g for standard spools)
5. Click "Save Filament"

### Recording Usage

1. Click on a filament card or use "Add Usage" button
2. Enter weight used in grams
3. Enter print name (e.g., "Phone Stand")
4. Enter component name (e.g., "Base")
5. Submit - the remaining weight will be automatically calculated

### Handling Overflow

If usage exceeds remaining weight:

1. The system will prompt you to add a new spool
2. Enter new spool details (pre-filled with same type/color)
3. System will:
   - Use remaining weight from old spool and archive it
   - Create new spool and deduct overflow amount
   - Record usage across both spools

### Viewing Statistics

Navigate to Statistics page to see:

- Total filament used across all spools
- Usage breakdown by type and color (charts)
- Most used filament spools
- Low filament warnings
- Active vs archived spool counts

### Archived Filaments

- Spools are automatically archived when weight reaches 0
- Manual archive is also available
- View archived spools under "Archived" section
- Print history is preserved for archived spools
- Can unarchive if needed

## Configuration

### Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URI=sqlite:///instance/spool_tracker.db
LOW_FILAMENT_THRESHOLD=20
```

### Database Configuration

**SQLite (Default)**:

```python
DATABASE_URI=sqlite:///instance/spool_tracker.db
```

**PostgreSQL (Production)**:

```python
DATABASE_URI=postgresql://username:password@localhost:5432/spool_tracker
```

## Docker Deployment

### Build Image

```powershell
docker build -t spool-tracker .
```

### Run Container

```powershell
docker-compose up -d
```

### View Logs

```powershell
docker-compose logs -f
```

### Stop Container

```powershell
docker-compose down
```

### Backup Database

The SQLite database is stored in `instance/spool_tracker.db` and persists via Docker volume.

```powershell
# Copy database from container
docker cp spool_tracker:/app/instance/spool_tracker.db ./backup.db
```

## Project Structure

```
spool_tracker/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── forms.py             # WTForms definitions
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── filament.py
│   │   └── print_history.py
│   ├── routes/              # Route blueprints
│   │   ├── auth.py          # Authentication
│   │   ├── main.py          # Dashboard & statistics
│   │   └── filaments.py     # Filament CRUD
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── auth/
│   │   ├── filaments/
│   │   └── errors/
│   └── static/              # CSS, JS, images
│       ├── css/
│       └── js/
├── instance/                # Database storage
├── migrations/              # Database migrations
├── config.py               # Configuration
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose config
└── docker-entrypoint.sh   # Container startup script
```

## API Routes

### Authentication

- `GET/POST /auth/register` - User registration
- `GET/POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Dashboard

- `GET /` - Home dashboard with active filaments
- `GET /statistics` - Statistics and reporting

### Filaments

- `GET/POST /filaments/add` - Add new filament
- `GET/POST /filaments/<id>/edit` - Edit filament
- `POST /filaments/<id>/archive` - Archive filament
- `POST /filaments/<id>/unarchive` - Unarchive filament
- `GET /filaments/<id>/history` - View print history
- `GET/POST /filaments/<id>/add-usage` - Record usage
- `POST /filaments/<id>/add-usage-with-overflow` - Record usage with overflow
- `GET /filaments/archived` - View archived filaments

## Development

### Database Migrations

```powershell
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Running Tests

```powershell
# Install test dependencies
pip install pytest pytest-cov

# Run tests (when implemented)
pytest
```

## Troubleshooting

### Database Issues

If you encounter database errors:

```powershell
# Delete existing database and migrations
Remove-Item -Recurse -Force instance, migrations

# Reinitialize
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Docker Issues

```powershell
# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f
```

### Permission Issues (Linux/Mac)

```bash
# Make entrypoint executable
chmod +x docker-entrypoint.sh
```

## Future Enhancements

Potential features for future versions:

- Cost tracking per spool
- Barcode/QR code scanning
- Export reports to PDF/CSV
- Mobile app
- Filament vendor management
- Print time tracking
- Multi-filament prints support
- API endpoints for external integrations

## License

This project is open source and available for personal and commercial use.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review the usage guide
3. Check application logs

## Credits

Built with Flask, Bootstrap 5, and Chart.js.
