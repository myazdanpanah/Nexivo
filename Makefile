# Nexivo - Local Development Makefile
# ====================================

.PHONY: help install dev migrate seed stop clean

PYTHON = python
PIP = pip
NPM = npm
MANAGE = $(PYTHON) backend/manage.py

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd backend && $(PIP) install -r requirements.txt
	cd frontend && $(NPM) install

migrate: ## Run database migrations
	cd backend && $(MANAGE) migrate

seed: ## Create dev superuser + sample users (idempotent)
	cd backend && $(MANAGE) create_dev_data

start-db: ## Start PostgreSQL (requires Docker)
	docker start nexivo_db 2>/dev/null || docker run -d --name nexivo_db \
		-e POSTGRES_DB=nexivo \
		-e POSTGRES_USER=nexivo_user \
		-e POSTGRES_PASSWORD=nexivo_pass \
		-p 5432:5432 \
		postgres:15

start-redis: ## Start Redis (requires Docker)
	docker start nexivo_redis 2>/dev/null || docker run -d --name nexivo_redis \
		-p 6379:6379 \
		redis:7-alpine

start-services: start-db start-redis ## Start all required services (Postgres + Redis)
	@echo "Waiting for PostgreSQL..."
	@sleep 3
	@echo "Services started!"

backend: ## Start the Django backend (http://localhost:8000)
	cd backend && $(MANAGE) runserver 0.0.0.0:8000

frontend: ## Start the Vite frontend (http://localhost:3000)
	cd frontend && $(NPM) run dev

dev: migrate seed ## Full local dev setup: migrate, seed, then start backend + frontend
	@echo ""
	@echo "==========================================="
	@echo "  Nexivo - Starting Local Development"
	@echo "==========================================="
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Admin:    admin / admin12345"
	@echo "==========================================="
	@echo ""
	@echo "Start the backend and frontend in separate terminals:"
	@echo "  make backend"
	@echo "  make frontend"

dev-all: migrate seed ## Start backend and frontend (run in background)
	cd backend && $(MANAGE) runserver 0.0.0.0:8000 &
	cd frontend && $(NPM) run dev &
	@echo "Backend: http://localhost:8000 | Frontend: http://localhost:3000"

stop: ## Stop and remove Docker containers
	docker stop nexivo_db nexivo_redis 2>/dev/null || true
	docker rm nexivo_db nexivo_redis 2>/dev/null || true

clean: stop ## Remove all containers, volumes, and __pycache__
	docker volume rm nexivo_db_data 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

test-backend: ## Run Django checks
	cd backend && $(MANAGE) check

test-frontend: ## Run TypeScript typecheck
	cd frontend && npx tsc --noEmit
