import csv
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

DATA_DIR = Path("data")
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB ceiling — scout CSVs are tiny

# ReportBuilder_<Unit>_<Rank_Parts>_<YYYYMMDD>.csv
_RANK_RE = re.compile(r'^ReportBuilder_[^_]+_(.+)_(\d{8})\.csv$', re.IGNORECASE)


# ── CSV helpers ───────────────────────────────────────────────────────────────

def extract_rank_info(filename: str) -> tuple[str, str] | None:
    """Return (rank_label, date_str) or None if filename doesn't match."""
    m = _RANK_RE.match(filename)
    if not m:
        return None
    rank = m.group(1).replace('_', ' ')
    # ScoutBook names the file "Scout Rank" but the rank is just "Scout"
    if rank == "Scout Rank":
        rank = "Scout"
    return rank, m.group(2)


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

@app.get("/api/ranks")
async def get_ranks():
    best: dict[str, tuple[Path, str]] = {}
    for f in DATA_DIR.glob("*.csv"):
        info = extract_rank_info(f.name)
        if not info:
            continue
        rank, date_str = info
        if rank not in best or date_str > best[rank][1]:
            best[rank] = (f, date_str)
    rank_order = ["Scout", "Tenderfoot", "Second Class", "First Class"]
    def rank_key(item):
        try:
            return rank_order.index(item[0])
        except ValueError:
            return len(rank_order)
    return [{"rank": k, "date": v[1]} for k, v in sorted(best.items(), key=rank_key)]


@app.get("/api/report")
async def get_report(rank: str | None = None):
    if rank:
        best_file, best_date = None, ""
        for f in DATA_DIR.glob("*.csv"):
            info = extract_rank_info(f.name)
            if info and info[0] == rank and info[1] > best_date:
                best_file, best_date = f, info[1]
        if not best_file:
            raise HTTPException(status_code=404, detail=f"No report found for rank: {rank}")
        csv_file = best_file
    else:
        csv_file = get_latest_csv()
        if not csv_file:
            raise HTTPException(status_code=404, detail="No report file found. Upload a CSV to get started.")
    try:
        return parse_csv(csv_file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/upload")
async def upload_report(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="At least one .csv file is required")

    saved_paths: list[Path] = []
    uploaded_names: list[str] = []
    total_scouts = 0

    try:
        for file in files:
            if not file.filename or not file.filename.lower().endswith(".csv"):
                raise HTTPException(status_code=400, detail="Only .csv files are accepted")

            # Read with per-file size cap
            chunks: list[bytes] = []
            total = 0
            while chunk := await file.read(16_384):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"{file.filename} exceeds 2 MB limit")
                chunks.append(chunk)
            content = b"".join(chunks)

            dest = DATA_DIR / safe_filename(file.filename)
            dest.write_bytes(content)
            saved_paths.append(dest)

            try:
                data = parse_csv(dest)
                if not data["scouts"]:
                    raise ValueError("No scouts detected")
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f"Invalid file {dest.name}: {exc}")

            uploaded_names.append(dest.name)
            total_scouts += len(data["scouts"])

        return {
            "message": f"Uploaded {len(uploaded_names)} file(s)",
            "files": uploaded_names,
            "scouts": total_scouts,
        }
    except HTTPException:
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise


# ── Static files (served last so API routes take priority) ───────────────────

app.mount("/", StaticFiles(directory="static", html=True), name="static")
