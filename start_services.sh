#!/bin/bash

echo "Starting Redis and Celery..."
echo "Starting Redis..."
docker run -d -p 6379:6379 --name redis redis:alpine 2>/dev/null || echo "Redis already running"

sleep 2

echo "Starting Celery worker..."
celery -A website worker -l info 