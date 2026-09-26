# SIH Demo Runbook

## 1. Start infrastructure

```bash
docker compose up -d
```

## 2. Start API

```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 3. Seed deterministic demo evidence

```bash
python scripts/seed_demo.py
```

## 4. Start web

```bash
cd apps/web
npm install
npm run dev
```

## 5. Judge scenario

Use:

> I have developed a turmeric-based Ayurvedic formulation and want to sell it in Germany. Can I protect it and what should I check?

Then demonstrate:

1. India → International switch.
2. Germany country profile.
3. Classification + innovation context.
4. Hybrid retrieval and evidence cards.
5. Confidence and demo-mode warning.
6. Next-step roadmap.

## Important

The seeded evidence is intentionally labelled **DEMO ONLY**. It is source pointers and architecture test data, not controlling law. Replace it with current authorized primary-source evidence before making legal/regulatory claims.
