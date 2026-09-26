import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "evals" / "gold_set" / "sample_cases.jsonl"


def main():
    rows = [json.loads(line) for line in GOLD.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Gold cases: {len(rows)}")
    print("Target metrics: Recall@K, Precision@K, MRR, citation correctness/completeness, unsupported-claim rate,")
    print("classification accuracy, jurisdiction accuracy, safe-abstention precision/recall, multilingual obligation preservation, latency.")


if __name__ == "__main__":
    main()
