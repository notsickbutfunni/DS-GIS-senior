# Bounding box for the Overture places extract (default: Manhattan)
BBOX ?= -74.03,40.70,-73.93,40.80

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
