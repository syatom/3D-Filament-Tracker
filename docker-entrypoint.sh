#!/bin/bash
set -e

echo "Starting Spool Tracker..."

# Wait a moment for any dependencies to be ready
sleep 2

# Initialize database if migrations/env.py doesn't exist
if [ ! -f "migrations/env.py" ]; then
    echo "Initializing database migrations..."
    flask db init
    echo "Creating initial migration..."
    flask db migrate -m "Initial migration"
fi

# Run database migrations
echo "Running database migrations..."
flask db upgrade

echo "Database setup complete!"

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:5000 \
              --workers 4 \
              --timeout 120 \
              --access-logfile - \
              --error-logfile - \
              "app:create_app()"
