#!/bin/bash

# Development startup script for LastResort Django application

echo "🚀 Starting development environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Configure for development environment
echo "🔧 Configuring for development environment..."
sed -i 's/SECURE_SSL_REDIRECT=True/SECURE_SSL_REDIRECT=False/' .env
sed -i 's/SESSION_COOKIE_SECURE=True/SESSION_COOKIE_SECURE=False/' .env
sed -i 's/CSRF_COOKIE_SECURE=True/CSRF_COOKIE_SECURE=False/' .env

# Add CSRF_COOKIE_SECURE if missing
if ! grep -q "CSRF_COOKIE_SECURE" .env; then
    echo "CSRF_COOKIE_SECURE=False" >> .env
fi

# Build Tailwind CSS
echo "🎨 Building Tailwind CSS..."
if command -v npm &> /dev/null; then
    npm install --silent
    npm run build:css:prod
    echo "✅ Tailwind CSS built successfully"
else
    echo "⚠️  npm not found. Skipping CSS build. Install Node.js to build CSS."
fi

# Start development environment
echo "🔨 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose exec web python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Checking for superuser..."
docker-compose exec -T web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

echo "✅ Development environment is ready!"
echo ""
echo "📋 Access your application:"
echo "  🌐 Web: http://localhost:8000/lastresort/"
echo "  🔧 Admin: http://localhost:8000/admin (admin/admin123)"
echo "  📊 Health: http://localhost:8000/health/"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Access container: docker-compose exec web bash"
echo "  Watch CSS changes: npm run build:css" 