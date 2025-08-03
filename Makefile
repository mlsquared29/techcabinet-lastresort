.PHONY: redis celery services dev stop-redis

# Start Redis
redis:
	docker run -d -p 6379:6379 --name redis redis:alpine 2>/dev/null || echo "Redis already running"

# Start Celery worker
celery:
	celery -A website worker -l info

# Start both Redis and Celery
services: redis
	sleep 2
	celery -A website worker -l info

# Start Django development server
dev:
	python manage.py runserver

# Stop Redis
stop-redis:
	docker stop redis 2>/dev/null || echo "Redis not running"
	docker rm redis 2>/dev/null || echo "Redis container not found"

# Check Redis status
check-redis:
	docker ps | grep redis || echo "Redis not running" 