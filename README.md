# Recipe Downloader

A local Flask app that extracts ingredients and instructions from recipe pages and presents an interactive cooking checklist. The browser provides progress tracking, serving adjustments, theme controls, and speech synthesis.

## Run locally

Use Python 3.11 and a fresh virtual environment:

```sh
git clone https://github.com/Neel-Sh/RecipeDownloader.git
cd RecipeDownloader
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run --host 127.0.0.1 --port 5000
```

Open [localhost:5000](http://localhost:5000), paste a recipe URL, and submit it. The Python server fetches the recipe page; this app does **not** run entirely in the browser.

## Extraction and limits

The parser tries recipe-scrapers, structured metadata through Extruct, JSON-LD, HTML headings/lists, and a Readability fallback. Results depend on the source website: blocked requests, changed markup, paywalls, and missing structured data can prevent extraction. Check ingredient quantities and instruction order against the original page.

Checklist state uses browser storage. Voice playback depends on the browser's speech-synthesis support. Source websites receive requests from the machine running Flask. Run this as a local tool: the URL-fetching endpoint is not designed as a public, authenticated scraping service.

## Project layout

| Path | Purpose |
| --- | --- |
| `app.py` | Flask routes and recipe extraction |
| `templates/` | Input and recipe views |
| `static/` | Browser styles and interaction code |
| `requirements.txt` | Direct runtime dependencies |

Virtual environments and Python bytecode are generated locally and excluded from Git. See [Contributing](CONTRIBUTING.md) for validation and bug reports. No repository-wide license file is included.
