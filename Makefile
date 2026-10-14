# Bounding box for the Overture places extract (city: Almaty)
BBOX ?= 76.74,43.03,77.16,43.40

.PHONY: setup up down data lab lint

setup:
	uv sync

up:
	docker compose up -d

down:
	docker compose down

data:
	mkdir -p data/raw
	uv run overturemaps download --bbox=$(BBOX) -f geoparquet --type=place -o data/raw/places.parquet

lab:
	uv run jupyter lab

lint:
	uv run ruff check .
