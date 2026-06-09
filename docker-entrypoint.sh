#!/bin/bash
set -e

echo "Starting Spool Tracker..."

# Wait a moment for any dependencies to be ready
sleep 2

# Initialize database if migrations don't exist
if [ ! -d "migrations" ]; then
    echo "Initializing database migrations..."
    flask db init
fi

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Check if we need to create initial migration
if [ ! "$(ls -A migrations/versions 2>/dev/null)" ]; then
    echo "Creating initial migration..."
    flask db migrate -m "Initial migration"
    flask db upgrade
fi

echo "Database setup complete!"

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:5000 \
              --workers 4 \
              --timeout 120 \
              --access-logfile - \
              --error-logfile - \
              "app:create_app()"
