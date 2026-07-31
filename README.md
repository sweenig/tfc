# Scout Meeting Planner

A web app for BSA troop leaders. Pull it up at a meeting, mark who showed up, and instantly see which requirements are needed by the most scouts present so you can plan the night around who is actually there.

This project now supports multiple deployment models: private Docker + [Tailscale](https://tailscale.com), local Wi-Fi hosting (for example on a Raspberry Pi), and a fully static GitHub Pages mode using a standalone HTML app.

## Features

- **Upload reports** — load ScoutBook CSV exports in-app
- **Take attendance quickly** — tap scout chips to mark present/absent
- **Ranked recommendations** — requirements sorted by how many present scouts still need them, with names listed per requirement
- **Two app modes** — backend-assisted mode (`index.html`) and fully portable client-only mode (`portable.html`)

## Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI |
| Frontend | Vanilla JS · single HTML file · no build step |
| Runtime | Docker Compose |
| Optional private access | Tailscale (VPN — no public internet exposure) |

## Prerequisites

- Docker + Docker Compose (for Docker-hosted modes)
- A modern browser (Chrome, Safari, Edge, Firefox)
- A free [Tailscale](https://tailscale.com) account if you use the private Tailscale mode

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

- With the current `docker-compose.yml` (DEV mode), open:
```
http://localhost:8082
```
- In Tailscale mode, use your Tailnet hostname/IP for the app service.

On Android, open Chrome → three-dot menu → **Add to Home screen** to install it as a shortcut that feels like a native app.

## Usage (Current UI)

1. **Load report data**
	- Docker app (`index.html`): tap **Upload new report CSV** and pick a ScoutBook CSV.
	- Portable app (`portable.html`): load one or more ScoutBook CSV files at session start.
2. **Choose a rank view**
	- Use the rank pills (Scout, Tenderfoot, Second Class, First Class, etc.) to switch reports.
3. **Mark attendance**
	- Tap scout chips to toggle present/absent status.
4. **Plan the meeting**
	- Review requirements sorted by highest need among present scouts.
	- Tap a requirement card to expand the scout list for that requirement.

## Hosting Options

### 1) Private VPN hosting with Tailscale (recommended for private shared access)

- Run the Docker stack.
- Keep `tfc-app` behind Tailscale.
- Access from devices on your Tailnet.
- Best when you want multi-user access and private network boundaries.

### 2) Local self-contained Wi-Fi hosting (for example Raspberry Pi)

- Run the app on a local device (such as a Pi) and expose it on local Wi-Fi only.
- Users connect to your local network and open the app in their browser.
- Best for in-person meetings without internet dependence.

### 3) Static hosting on GitHub Pages (portable mode)

- Publish the repository with `index.html` at root redirecting to `app/static/portable.html`.
- App logic runs entirely in each user's browser; there is no backend service.
- Users must load CSV files locally each session.
- Best for zero-server deployment and broad device compatibility.

> Important: GitHub Pages is public by default. Do not commit real scout CSV data to the repository.

## Data & Privacy

- In portable mode, CSV processing happens locally in the browser.
- In Tailscale or local Wi-Fi Docker modes, CSVs are stored on the host under `data/`.
- Scout CSVs are listed in `.gitignore` and should never be committed to this repo.
- The `.env` file (Tailscale auth key) is excluded from git.

## Project Structure

```
tfc/
├── app/
│   ├── main.py            # FastAPI backend
│   ├── requirements.txt
│   └── static/
│       ├── index.html     # Backend-assisted frontend
│       └── portable.html  # Fully standalone client-only app
├── data/                  # Mounted as a Docker volume
│   └── .gitkeep           # Keeps the directory tracked in git
├── index.html             # Root landing page redirect (GitHub Pages)
├── .env.example           # Template for the Tailscale auth key
├── .gitignore
├── Dockerfile
└── docker-compose.yml
```

## Updating the Report

When ScoutBook publishes updated advancement data:

- Docker app (`index.html`): use **Upload new report CSV**. The backend uses the newest matching file.
- Portable app (`portable.html`): reload one or more CSV files at session start; latest file per rank is selected from what you loaded.

## Tailscale Notes

- The `tailscale` container registers on your Tailnet as **tfc-planner**
- MagicDNS (enabled by default on all Tailnets) resolves `tfc-planner` to its Tailscale IP automatically
- The `tfc-app` container shares the Tailscale container's network namespace — no host ports are exposed
- Tailscale state is stored in a named Docker volume (`tailscale-state`) so the device stays authenticated across restarts
