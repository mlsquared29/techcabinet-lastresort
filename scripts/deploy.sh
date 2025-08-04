#!/bin/bash

# Production deployment script for LastResort Django application

set -e  # Exit on any error

echo "🚀 Starting production deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy env.example to .env and configure your environment variables."
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
required_vars=(
    "DJANGO_SECRET_KEY"
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "OPENAI_API_KEY"
    "DJANGO_ALLOWED_HOSTS"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env file"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Configure for production environment
echo "🚀 Configuring for production environment..."
sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' .env
sed -i 's/SESSION_COOKIE_SECURE=False/SESSION_COOKIE_SECURE=True/' .env
sed -i 's/CSRF_COOKIE_SECURE=False/CSRF_COOKIE_SECURE=True/' .env

# Add CSRF_COOKIE_SECURE if missing
if ! grep -q "CSRF_COOKIE_SECURE" .env; then
    echo "CSRF_COOKIE_SECURE=True" >> .env
fi

# Build Tailwind CSS locally before deployment
echo "🎨 Building Tailwind CSS..."
if command -v npm &> /dev/null; then
    if [ -f "package.json" ]; then
        npm install --silent
        npm run build:css:prod
        echo "✅ Tailwind CSS built successfully"
    else
        echo "⚠️  package.json not found. CSS will be built in Docker container."
    fi
else
    echo "⚠️  npm not found. CSS will be built in Docker container."
fi

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Check if SSL certificates exist
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    echo "⚠️  Warning: SSL certificates not found in ssl/ directory"
    echo "For production, you should obtain proper SSL certificates."
    echo "For testing, you can generate self-signed certificates:"
    echo "openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl/key.pem -out ssl/cert.pem"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start production containers
echo "🔨 Building and starting production containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser (if needed)..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# Collect static files
echo "📁 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Check if services are running
echo "🔍 Checking service health..."
sleep 5

# Health check
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    echo "✅ Application is healthy and running!"
    echo "🌐 Access your application at: http://localhost"
    echo "🔒 For HTTPS: https://localhost (requires SSL certificates)"
else
    echo "❌ Health check failed. Check the logs:"
    docker-compose -f docker-compose.prod.yml logs web
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  Access Django admin: http://localhost/admin" 