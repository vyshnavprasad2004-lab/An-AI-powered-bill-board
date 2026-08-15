# AI Student Info Board

A physical kiosk that watches multiple disaster/hazard feeds and news
sources, cross-checks stories across sources, and uses a **local LLM**
(Ollama) to turn confirmed stories into short student-friendly bulletins,
each illustrated by a **local image model** (Stable Diffusion via
AUTOMATIC1111). Confirmed high-severity disaster alerts interrupt normal
rotation with a full-screen priority takeover.

No cloud AI APIs are used anywhere in this project.

## Problem statement

Students don't have one trustworthy screen to check between classes.
Disaster warnings (weather, seismic, campus safety) are scattered across
different agency sites and apps, and general news is scattered across
outlets with no easy way to tell what's independently verified versus
reported by a single source. This board solves both problems: it only
surfaces disaster alerts once 2+ independent sources agree, and it
rewrites everything into short, plain-language bulletins for a busy
student walking past a screen.

## Features

- **Multi-source disaster monitoring** — pulls from GDACS, USGS
  earthquakes, ReliefWeb, and any additional agency feeds you add.
- **Cross-source verification** — stories are clustered by similarity;
  a disaster alert only becomes "confirmed" once 2+ independent sources
  report it (configurable).
- **Local LLM summarization** — Ollama (Llama 3 / Mistral / Gemma) rewrites
  raw feed text into a short headline, a 2–3 sentence bulletin, and a
  severity rating.
- **Local image generation** — Stable Diffusion (AUTOMATIC1111 API)
  generates one illustrative image per bulletin.
- **Kiosk display app** — fullscreen, auto-rotating board with a live
  clock, source-verification indicator, and a red full-screen takeover
  for confirmed severe alerts.
- **Scheduled pipeline** — re-fetches, re-summarizes, and re-illustrates
  on a timer (default every 20 minutes, configurable).

## Architecture

```
News & disaster sources (RSS/Atom)
          │
          ▼
Aggregator & verifier  ── dedupes stories, counts independent sources
          │
          ▼
Local LLM (Ollama)  ── summarizes + rates severity
          │
          ▼
Local image model (Stable Diffusion)  ── illustrates the bulletin
          │
          ▼
Kiosk display app (FastAPI + HTML)  ── fullscreen rotation
          │
          └── confirmed severe alert → priority takeover screen
```

See `docs/architecture.png` for the diagram version.

## Repository structure

```
campusboard/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── app.py                     # FastAPI entrypoint + scheduler
├── src/
│   ├── config.py               # sources, model endpoints, thresholds
│   ├── fetchers.py             # RSS/Atom fetching
│   ├── aggregator.py           # clustering + cross-source verification
│   ├── llm.py                  # Ollama client (summarize + classify)
│   ├── imagegen.py             # Stable Diffusion client
│   ├── pipeline.py             # orchestrates the full run
│   └── kiosk/
│       ├── templates/index.html
│       └── static/
├── docs/
│   ├── architecture.png
│   ├── workflow.png
│   └── screenshots/
├── models/                     # notes on which local models to pull (not the weights themselves)
├── data/                       # cached raw fetches
├── outputs/
│   ├── images/                 # generated illustrations
│   └── bulletins/              # generated bulletin JSON
└── demo/
    └── demo.mp4
```

## Installation

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally
- [AUTOMATIC1111 Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
  (or ComfyUI with an equivalent API) running locally with its API enabled

### 2. Pull the local models

```bash
ollama pull llama3
ollama serve   # if not already running
```

Start the Stable Diffusion WebUI with its API flag:

```bash
./webui.sh --api          # Linux/Mac
webui-user.bat --api      # Windows (add --api to COMMANDLINE_ARGS)
```

### 3. Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure

Edit `src/config.py`:
- Add/replace the RSS feeds under `SOURCES` with feeds relevant to your
  region and campus.
- Adjust `OLLAMA_MODEL`, `OLLAMA_URL`, `SD_URL` if your local setup differs
  from the defaults.

### 5. Run

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The first pipeline run happens automatically on startup, then repeats on
the interval set by `REFRESH_INTERVAL_MINUTES`. Trigger a manual refresh
any time (useful for demos):

```bash
curl -X POST http://localhost:8000/api/refresh
```

### 6. Display on the kiosk screen

On the machine driving the physical display:

```bash
chromium --kiosk http://localhost:8000
```

(Or point any browser at that URL in fullscreen mode.)

## Usage

- The board rotates automatically through current bulletins.
- Each bulletin shows a verification indicator — filled dots equal the
  number of independent sources that reported the story.
- If a disaster story is confirmed by 2+ sources and rated "high"
  severity, the board switches to a full-screen red alert until the story
  is no longer active.

## Screenshots

See `docs/screenshots/` — add board screenshots here (normal rotation and
the alert takeover).

## Demo video

See `demo/demo.mp4` — record the board cycling through bulletins and
triggering the alert takeover (you can force one for the demo by editing
a fetched item's severity, or by waiting for a real earthquake feed hit).

## Notes on running fully locally

- Every text generation call goes to `localhost:11434` (Ollama).
- Every image generation call goes to `localhost:7860` (AUTOMATIC1111 API).
- The only network calls to the outside world are read-only HTTP requests
  to public RSS/Atom feeds — no account, key, or cloud AI service is
  required.
