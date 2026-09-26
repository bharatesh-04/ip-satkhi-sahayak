.PHONY: test api web seed ingest index eval updates lint

api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	PYTHONPATH=apps/api pytest -q

seed:
	PYTHONPATH=apps/api python scripts/seed_demo.py

ingest:
	PYTHONPATH=apps/api python scripts/ingest_source.py --manifest knowledge/source_manifests/india_core.json

index:
	PYTHONPATH=apps/api python scripts/index_jsonl.py

eval:
	PYTHONPATH=apps/api python scripts/run_eval.py

updates:
	PYTHONPATH=apps/api python scripts/check_updates.py --manifest knowledge/source_manifests/india_core.json
