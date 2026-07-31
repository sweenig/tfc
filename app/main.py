import csv
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

DATA_DIR = Path("data")
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB ceiling — scout CSVs are tiny


# ── CSV helpers ───────────────────────────────────────────────────────────────

def get_latest_csv() -> Path | None:
    files = list(DATA_DIR.glob("*.csv"))
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def safe_filename(name: str) -> str:
    """Strip path components and allow only safe characters."""
    stem = Path(name).name
    return re.sub(r"[^\w\-.]", "_", stem)


def parse_csv(filepath: Path) -> dict:
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]

    if len(rows) < 7:
        raise ValueError("File does not look like a ScoutBook report (too few rows)")

    # Row 0: label column + scout names
    scouts = [s.strip() for s in rows[0][1:] if s.strip()]
    n = len(scouts)
    if n == 0:
        raise ValueError("No scout names found in the first row")

    # Rows 1-5: metadata (Age, Current Rank, Current Rank Date, FC%, FC v2022%)
    meta_keys = [
        "age",
        "current_rank",
        "current_rank_date",
        "first_class_pct",
        "first_class_v2022_pct",
    ]
    metadata: dict[str, dict[str, str]] = {}
    for i, key in enumerate(meta_keys):
        row = rows[i + 1] if i + 1 < len(rows) else []
        metadata[key] = {
            scouts[j]: (row[j + 1].strip() if j + 1 < len(row) else "")
            for j in range(n)
        }

    # Rows 6+: individual requirements
    requirements = []
    for row in rows[6:]:
        req_name = row[0].strip() if row else ""
        if not req_name:
            continue
        completed = {
            scouts[j]: bool(row[j + 1].strip() if j + 1 < len(row) else "")
            for j in range(n)
        }
        requirements.append({"name": req_name, "completed": completed})

    return {
        "scouts": scouts,
        "metadata": metadata,
        "requirements": requirements,
        "source_file": filepath.name,
    }


app = FastAPI(title="Scout Meeting Planner")


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/api/report")
async def get_report():
    csv_file = get_latest_csv()
    if not csv_file:
        raise HTTPException(status_code=404, detail="No report file found. Upload a CSV to get started.")
    try:
        return parse_csv(csv_file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/upload")
async def upload_report(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    # Read with size cap
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(16_384):
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds 2 MB limit")
        chunks.append(chunk)
    content = b"".join(chunks)

    dest = DATA_DIR / safe_filename(file.filename)
    dest.write_bytes(content)

    try:
        data = parse_csv(dest)
        if not data["scouts"]:
            raise ValueError("No scouts detected")
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Invalid file: {exc}")

    return {"message": f"Uploaded {dest.name}", "scouts": len(data["scouts"])}


# ── Static files (served last so API routes take priority) ───────────────────

app.mount("/", StaticFiles(directory="static", html=True), name="static")
