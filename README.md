# Scout Meeting Planner

A self-hosted web app for BSA troop leaders. Pull up the app at a meeting, mark who showed up, and instantly see which First Class requirements are needed by the most scouts present — so you can plan the night around the scouts who are actually there.

Runs in Docker and is accessible only through [Tailscale](https://tailscale.com), keeping all scout data (names, ages, ranks, attendance) off the public internet.

## Features

- **Upload reports** — download a CSV from ScoutBook/Scoutmaster, upload it in the app; the most recent file is always used automatically
- **Take attendance** — tap scout names to mark who's present
- **Ranked recommendations** — requirements sorted by how many present scouts still need them, with the specific scouts listed
- **Attendance history** — past meetings are saved locally in SQLite for reference

## Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · SQLite |
| Frontend | Vanilla JS · single HTML file · no build step |
| Runtime | Docker Compose |
| Private access | Tailscale (VPN — no public internet exposure) |

## Prerequisites

- Docker + Docker Compose
- A free [Tailscale](https://tailscale.com) account
- Tailscale installed on any device that will access the app (phone, tablet, etc.)

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/your-username/tfc.git
cd tfc
```

**2. Generate a Tailscale auth key**

In the [Tailscale admin console](https://login.tailscale.com/admin/settings/keys), generate an auth key. Check **Reusable** so the container can restart without re-authenticating.

**3. Create your `.env` file**
```bash
cp .env.example .env
# edit .env and paste your auth key
```

**4. Add your first report**

Download a "First Class" multi-unit CSV from ScoutBook and drop it in the `data/` folder, or use the upload feature in the app after starting.

**5. Start the stack**
```bash
docker compose up -d
```

**6. Open the app**

On any device connected to your Tailscale network, navigate to:
```
http://tfc-planner:8080
```

On Android, open Chrome → three-dot menu → **Add to Home screen** to install it as a shortcut that feels like a native app.

## Usage

1. **Before the meeting** — if you have a new report from ScoutBook, tap **Upload New Report** and select the CSV from your downloads
2. **At the meeting** — tap **Start Meeting**, then tap each scout's name as they arrive (green = present)
3. **Get recommendations** — tap **See Recommendations** to see requirements ranked by the number of present scouts who still need them; tap any requirement to expand the list of which scouts need it
4. **Save the record** — tap **Save Attendance Record** before closing

## Data & Privacy

- **No data leaves your machine.** The app is only reachable through your Tailscale private network.
- Scout CSVs and the attendance database are listed in `.gitignore` and will never be committed to this repo.
- The `.env` file (Tailscale auth key) is also excluded from git.

## Project Structure

```
tfc/
├── app/
│   ├── main.py            # FastAPI backend
│   ├── requirements.txt
│   └── static/
│       └── index.html     # Full single-page frontend
├── data/                  # Mounted as a Docker volume
│   └── .gitkeep           # Keeps the directory tracked in git
├── .env.example           # Template for the Tailscale auth key
├── .gitignore
├── Dockerfile
└── docker-compose.yml
```

## Updating the Report

When ScoutBook publishes updated advancement data, download the new CSV and use the **Upload New Report** button. The app always uses whichever CSV in `data/` has the most recent modification time, so old files can be left in place or deleted.

## Tailscale Notes

- The `tailscale` container registers on your Tailnet as **tfc-planner**
- MagicDNS (enabled by default on all Tailnets) resolves `tfc-planner` to its Tailscale IP automatically
- The `tfc-app` container shares the Tailscale container's network namespace — no host ports are exposed
- Tailscale state is stored in a named Docker volume (`tailscale-state`) so the device stays authenticated across restarts
