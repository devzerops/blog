#!/bin/bash
set -e

# Function to check PostgreSQL connection
check_postgres() {
    echo "Waiting for PostgreSQL to become available..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; then
            echo "✅ PostgreSQL is up and running!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo "⏳ PostgreSQL is unavailable - attempt $attempt of $max_attempts - sleeping..."
        sleep 2
    done
    
    echo "❌ Failed to connect to PostgreSQL after $max_attempts attempts. Exiting..."
    exit 1
}

# Main execution
main() {
    # Check PostgreSQL connection
    check_postgres

    # Create necessary directories with proper permissions
    echo "📂 Creating necessary directories..."
    mkdir -p /app/instance /app/app/static/uploads /app/app/static/temp
    chmod -R 777 /app/app/static

    # Initialize database
    echo "🔄 Running database migrations..."
    flask db upgrade

    # Initialize database with default data
    echo "💾 Initializing database with default data..."
    flask init-db

    echo "✅ Database initialization complete!"
}

# Run the main function
main
