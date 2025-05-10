# School Website Mapper – Google 100‑free‑search Edition

Uses Google Programmable Search (Custom Search JSON API) to find official school websites.

## Setup
Add two secrets (or environment variables):

```
GOOGLE_API_KEY = "your_api_key"
GOOGLE_CX = "your_search_engine_id"
```

Optional: `HUNTER_API_KEY` for extra email enrichment.

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```
