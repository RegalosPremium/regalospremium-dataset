#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "data" / "ads" / "inbox"
PROCESSED = ROOT / "data" / "ads" / "processed"
STATE = ROOT / "var" / "ads_ingest_state.json"
REPORT = ROOT / "reports" / "ads" / "live" / "latest_ingest.json"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"processed_sha256": []}
def inspect_csv(path: Path) -> dict:
    encodings = ("utf-8-sig", "utf-8", "latin-1")
    last_error = None
    for enc in encodings:
        try:
            with path.open(encoding=enc, newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            header = rows[0] if rows else []
            return {
                "encoding": enc,
                "rows": max(len(rows) - 1, 0),
                "columns": len(header),
                "header": header,
            }
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"No se pudo leer {path.name}: {last_error}")

def run_qa() -> list[dict]:
    checks = [
        ["python3", "scripts/validate_ads_mapping.py"],
        ["python3", "scripts/validate_url_ecosystem.py"],
    ]
    results = []
    for cmd in checks:
        cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        results.append({
            "command": " ".join(cmd),
            "returncode": cp.returncode,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
        })
    return results
def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    state = load_state()
    seen = set(state.get("processed_sha256", []))
    files = sorted(INBOX.glob("*.csv"))
    ingested = []

    for src in files:
        digest = sha256(src)
        if digest in seen:
            src.unlink(missing_ok=True)
            continue
        meta = inspect_csv(src)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dst = PROCESSED / f"{stamp}__{src.name}"
        shutil.move(str(src), str(dst))
        seen.add(digest)
        ingested.append({
            "source_name": src.name,
            "archived_as": dst.name,
            "sha256": digest,
            **meta,
        })

    qa = run_qa()
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ingested_count": len(ingested),
        "ingested": ingested,
        "qa": qa,
        "status": "PASS" if all(x["returncode"] == 0 for x in qa) else "FAIL",
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    STATE.write_text(json.dumps({"processed_sha256": sorted(seen)}, indent=2), encoding="utf-8")
    print(json.dumps({"ingested": len(ingested), "status": payload["status"]}))
    return 0 if payload["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
