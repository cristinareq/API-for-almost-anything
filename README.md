# Create APIs for Almost Anything

*A Natural‑Language Web‑Scraping API Generator*

> **Generate production‑ready FastAPI scrapers from a single sentence.**

![screenshot](docs/hero.png)

---

## Table of contents

1. [Overview](#overview)
2. [Key features](#key-features)
3. [Live demo](#live-demo)
4. [System architecture](#system-architecture)
5. [Tech stack](#tech-stack)
6. [Prerequisites](#prerequisites)
7. [Installation](#installation)
8. [Quick‑start](#quick-start)
9. [Usage workflow](#usage-workflow)
10. [Performance](#performance)
11. [Limitations](#limitations)
12. [Ethical use](#ethical-use)
13. [License](#license)
14. [Acknowledgements](#acknowledgements)

---

## Overview

> “A tool that transforms natural‑language instructions into fully functional web‑scraping APIs.” — *Capstone thesis, April 2025*

The project tackles the **API gap**: most websites still ship without public endpoints or impose price and rate limits. By combining **Streamlit**, **FastAPI**, **BeautifulSoup**, **Selenium** and **OpenAI GPT‑3.5 / GPT‑4o**, the app lets anyone type *“Extract all book titles and prices from this page”* and receive:

* suggested CSS selectors;
* a FastAPI micro‑service with JSON & CSV endpoints;
* Swagger docs, async background tasks, caching and CORS;
* one‑click test and data export.

All without touching a single line of code.

## Key features

* Natural‑language input → **automatic field detection** (GPT‑3.5).
* **HTML pre‑processing** to remove noise and stay under token limits.
* Robust selector fallback (alternative CSS / JS parsing).
* **Headless Selenium** fallback for JS‑heavy sites.
* Generated FastAPI includes async, caching, CSV export and Swagger UI.
* **Code‑merge** feature (GPT‑4o) integrates the scraper into existing projects.
* Streamlit UI with four pages: Home, Extract, Results, Merge Code.

## Live demo

▶️ [api‑for‑almost‑anything.streamlit.app](https://api-for-almost-anything.streamlit.app)

*(Public key is injected at runtime via GitHub Actions secrets.)*

## System architecture

```
[User]
  ⬇ natural‑language request
[Streamlit UI]  —HTML→  [Pre‑processor (BeautifulSoup)]
  ⬇ prompt + filtered HTML
[OpenAI GPT‑3.5] → field JSON
  ⬇ selected fields
[Generator] → FastAPI template (+ fallback logic)
  ⬇ optional
[GPT‑4o] (merge legacy code)
```

The full diagram is available in the thesis (Figure B‑2).

## Tech stack

| Layer       | Technology                                                            |
| ----------- | --------------------------------------------------------------------- |
| UI          | Streamlit, custom CSS, `streamlit‑option‑menu`                        |
| Scraping    | Requests, BeautifulSoup, **Selenium** fallback                        |
| AI models   | OpenAI **GPT‑3.5‑turbo** (field suggestions), **GPT‑4o** (code merge) |
| API runtime | **FastAPI** + Uvicorn                                                 |
| Packaging   | Poetry / pip, Docker (optional)                                       |

## Prerequisites

* Python ≥ 3.10
* OpenAI API key (`OPENAI_API_KEY`)
* (Optional) Chrome/Chromium for Selenium fallback.

## Installation

```bash
# clone the repo
$ git clone https://github.com/<your‑fork>/api-for-almost-anything.git
$ cd api-for-almost-anything

# create venv & install deps
$ python -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt

# set your OpenAI key (Bash example)
$ export OPENAI_API_KEY="sk‑..."
```

## Quick‑start

### 1️⃣ Run the Streamlit interface

```bash
$ streamlit run web_scraper_app.py
```

Visit `http://localhost:8501` and follow the four‑step workflow:

1. **Paste URL + goal**
2. Pick your fields
3. Generate API & docs
4. Test or download

### 2️⃣ Run a generated scraper directly

```bash
$ pip install fastapi uvicorn requests beautifulsoup4 pandas
$ uvicorn web_scraper_api:app --reload
```

Swagger UI will be served at `/docs`.

## Usage workflow

| Page           | Action                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------ |
| **Home**       | Read intro, click *Start Extracting Data*                                                        |
| **Extract**    | Enter URL & description → *Analyse the website* → select fields → *Generate API & Documentation* |
| **Results**    | Tabs: *API Code*, *Documentation*, *Test & Export* (live scrape + JSON / CSV download)           |
| **Merge Code** | Paste existing code → *Merge Code* (GPT‑4o)                                                      |

## Performance

Average end‑to‑end latency on static pages is **< 8 s**. Success rates across 8 test sites:

| Tier                     | Success‑rate |
| ------------------------ | ------------ |
| Easy / static            | 100 %        |
| Medium / server‑rendered | 83 %         |
| JS‑heavy                 | 60 %         |
| High‑traffic protected   | 50 %         |

See thesis Table A‑3 for full metrics.

## Limitations

* Reliant on site structure — drastic layout changes may break selectors.
* JS‑heavy sites may require Selenium (slower) and still hit anti‑bot walls.
* Token limits: HTML is trimmed to 420 kB before prompting.
* AI models can mis‑label fields; always validate output.

## Ethical use

This tool is **NOT** a bypass for terms‑of‑service or privacy laws. Check a site’s `robots.txt`, ToS and data‑protection rules before scraping. Use responsibly and cache results to minimise load.

## License

MIT — see `LICENSE` file for details.

## Acknowledgements

*Capstone Project — IE University, School of Science & Technology.*

Special thanks to **Marcos Navarro** for supervision and to the OpenAI, Streamlit and FastAPI communities for their tools.

