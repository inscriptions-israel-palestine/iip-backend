#!/usr/bin/env bash

alembic upgrade head

python ingest_inscriptions.py

uvicorn iip_search.app:app --proxy-headers --host 0.0.0.0 --port 8080