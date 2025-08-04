# LastResort

A Django application with PostgreSQL, Redis, Celery, and OpenAI integration for hosting Human vs AI competitions.

## 🚀 Quick Start

### Development Setup

**Option 1: Full Stack Development (Recommended)**
```bash
# 1. Navigate to your project
cd ~/lastresort

# 2. Start the full development environment
./scripts/dev.sh

# 3. Your app is now running at:
# - Web: http://localhost:8000/lastresort/
# - Admin: http://localhost:8000/admin (admin/admin123)
# - Health: http://localhost:8000/health/
```

**Note:** The dev script automatically configures your environment for development (disables SSL redirect, secure cookies, etc.)

**Option 2: Lightweight Development (If you don't need Celery/Redis)**
```bash
# 1. Start just the database
docker-compose up -d db

# 2. Run Django directly
python manage.py runserver

# 3. Your app runs at http://localhost:8000/lastresort/
```

### Production Deployment

```bash
# 1. Configure environment
cp env.example .env
# Edit .env with your production values

# 2. Deploy
./scripts/deploy.sh

# 3. Access at http://localhost (or your domain)
```

**Note:** The deploy script automatically configures your environment for production (enables SSL redirect, secure cookies, etc.)

## 🛠️ Development Workflow

### Daily Development

**Making Code Changes:**
- Changes are live (no restart needed)

**CSS Development:**
```bash
# Watch for CSS changes
npm run build:css

# Build CSS for production
npm run build:css:prod
```

**Database Changes:**
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

**Viewing Logs:**
```bash
# If using dev.sh
docker-compose logs -f

# If using runserver
# Logs appear in your terminal
```

**Accessing Database:**
```bash
# If using dev.sh
docker-compose exec web psql -U postgres -d lastresort

# If using runserver
python manage.py dbshell
```

### End of Day

**Stop Development Environment:**
```bash
# If using dev.sh
docker-compose down

# If using runserver
# Just Ctrl+C in the terminal
```

### Common Tasks

**Check if everything is running:**
```bash
# Check container status
docker-compose ps

# Check health
curl http://localhost:8000/health/
```

**Reset database (if needed):**
```bash
# Drop and recreate
docker-compose down -v
docker-compose up -d db
python manage.py migrate
python manage.py createsuperuser
```

## 🚀 Production Deployment

### Prerequisites

- Docker and Docker Compose installed
- A server with at least 2GB RAM and 10GB storage
- Domain name (optional but recommended)
- SSL certificates (for HTTPS)

### Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Application Setup

```bash
# Clone repository
git clone <your-repository-url>
cd lastresort

# Configure environment
cp env.example .env
nano .env  # Edit with your production values
```

**Required environment variables:**
```bash
# Django Settings
DJANGO_SECRET_KEY=your-very-secure-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database Settings
POSTGRES_DB=lastresort_prod
POSTGRES_USER=lastresort_user
POSTGRES_PASSWORD=your-very-secure-db-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis Settings
REDIS_PASSWORD=your-very-secure-redis-password

# OpenAI Settings
OPENAI_API_KEY=your-openai-api-key

# Production Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### SSL Certificates

#### Option A: Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to project directory
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chown -R $USER:$USER ssl/
```

#### Option B: Self-Signed (Testing Only)
```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl/key.pem -out ssl/cert.pem
```

### Deploy

```bash
# Deploy using the script
./scripts/deploy.sh

# Or manually
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🔧 Technical Details

### Architecture

- **Django**: Web framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and Celery broker
- **Celery**: Background task processing
- **Nginx**: Reverse proxy and static file serving
- **Docker**: Containerization
- **Tailwind CSS**: Styling (v3 with build process)

### CSS Development

```bash
# Install dependencies
npm install

# Build CSS for development
npm run build:css:prod

# Watch for changes
npm run build:css
```

### Troubleshooting

#### CSS Not Loading
1. Check that `output.css` exists in `lastresort/static/lastresort/dist/`
2. Verify static files are collected: `python manage.py collectstatic`
3. Check nginx logs for CSP violations

#### CSRF Token Errors
1. Verify `CSRF_TRUSTED_ORIGINS` includes your domain
2. Check that `CSRF_COOKIE_SECURE=True` in production
3. Ensure HTTPS is properly configured

#### Build Issues
1. Check Node.js is installed in Docker container
2. Verify `package.json` and `tailwind.config.js` are present
3. Check build logs for npm errors

## 📁 Project Structure

```
lastresort/
├── lastresort/          # Django app
│   ├── static/         # Static files
│   │   └── lastresort/
│   │       ├── dist/   # Built CSS
│   │       ├── src/    # Source CSS
│   │       └── images/ # Images
│   ├── templates/      # HTML templates
│   └── ...
├── website/            # Django project settings
├── scripts/            # Deployment scripts
├── ssl/               # SSL certificates
├── docker-compose.yml # Development setup
├── docker-compose.prod.yml # Production setup
└── ...
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.