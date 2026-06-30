.PHONY: dev-backend dev-frontend install test seed clean

# Install all dependencies
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Run backend dev server
dev-backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run frontend dev server
dev-frontend:
	cd frontend && npm run dev

# Run both (use two terminals)
dev:
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

# Run tests
test:
	cd backend && python -m pytest tests/ -v

# Seed demo data
seed:
	cd backend && python -m app.seed_data

# Clean generated files
clean:
	rm -rf backend/data/*.db backend/data/chroma/*
	find backend -type d -name "__pycache__" -exec rm -rf {} +

# Docker
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
