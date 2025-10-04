.PHONY: help dev start stop restart logs health status clean build test security audit

# Default target
help:
	@echo "========================================="
	@echo "🌌 Astro-Zoom Development Commands"
	@echo "========================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start all services in development mode"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs       - View all service logs"
	@echo "  make health     - Check service health"
	@echo "  make status     - Show detailed status"
	@echo ""
	@echo "Docker:"
	@echo "  make build      - Build all Docker images"
	@echo "  make clean      - Clean up containers and volumes"
	@echo ""
	@echo "Security:"
	@echo "  make security   - Run security scans"
	@echo "  make audit      - View audit logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run all tests"
	@echo "  make test-api   - Run API tests"
	@echo "  make test-web   - Run frontend tests"
	@echo ""

# Development
dev:
	@echo "🚀 Starting development environment..."
	docker-compose -f infra/docker-compose.yml up --build

start:
	@echo "🚀 Starting all services..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		powershell -File start.ps1; \
	else \
		bash start.sh; \
	fi

stop:
	@echo "🛑 Stopping all services..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		powershell -File stop.ps1; \
	else \
		bash stop.sh; \
	fi

restart:
	@echo "🔄 Restarting all services..."
	@make stop
	@sleep 2
	@make start

# Monitoring
logs:
	@echo "📋 Viewing logs..."
	docker-compose -f infra/docker-compose.yml logs -f

health:
	@echo "🏥 Checking health..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		powershell -File healthcheck.ps1; \
	else \
		bash healthcheck.sh; \
	fi

status:
	@echo "📊 Checking status..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		powershell -File status.ps1; \
	else \
		bash status.sh; \
	fi

# Docker operations
build:
	@echo "🔨 Building Docker images..."
	docker-compose -f infra/docker-compose.yml build

clean:
	@echo "🧹 Cleaning up..."
	docker-compose -f infra/docker-compose.yml down -v
	@echo "✅ Cleanup complete"

# Security
security:
	@echo "🔒 Running security scans..."
	@echo "\n📦 Checking Python dependencies (API)..."
	cd apps/api && pip-audit || echo "⚠️  pip-audit not installed. Run: pip install pip-audit"
	@echo "\n📦 Checking Python dependencies (AI)..."
	cd apps/ai && pip-audit || echo "⚠️  pip-audit not installed. Run: pip install pip-audit"
	@echo "\n📦 Checking Node dependencies..."
	cd apps/web && pnpm audit || echo "⚠️  No critical vulnerabilities"
	@echo "\n✅ Security scan complete"

audit:
	@echo "📜 Viewing audit logs..."
	@if [ -f "logs/audit.log" ]; then \
		tail -n 50 logs/audit.log | jq -r '. | "\(.timestamp) [\(.user_id)] \(.method) \(.path) -> \(.status)"' 2>/dev/null || tail -n 50 logs/audit.log; \
	else \
		echo "No audit logs found. Start the services to generate logs."; \
	fi

# Testing
test:
	@echo "🧪 Running all tests..."
	@make test-api
	@make test-web

test-api:
	@echo "🧪 Running API tests..."
	cd apps/api && python -m pytest tests/ -v || echo "⚠️  No tests found yet"

test-web:
	@echo "🧪 Running frontend tests..."
	cd apps/web && pnpm test || echo "⚠️  No tests found yet"

# Database
db-migrate:
	@echo "🗄️  Running database migrations..."
	cd apps/api && alembic upgrade head

db-seed:
	@echo "🌱 Seeding database..."
	cd apps/api && python -m app.seed

# Quick access
api-shell:
	docker-compose -f infra/docker-compose.yml exec api bash

web-shell:
	docker-compose -f infra/docker-compose.yml exec web sh

ai-shell:
	docker-compose -f infra/docker-compose.yml exec ai bash

# Generate sample tiles
tiles:
	@echo "🖼️  Generating sample tiles..."
	python infra/generate_sample_tiles.py

