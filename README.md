
# Business Finder – DuckDuckGo Edition

* Unlimited free searches via DuckDuckGo (`duckduckgo-search` lib).  
* Asynchronous scraping for speed.  
* Optional Hunter.io enrichment.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud
1. Put **these four files** in repo root (`app.py`, `scraper.py`, `requirements.txt`, `README.md`).
2. No mandatory secrets. Add `HUNTER_API_KEY` if you want enrichment.
3. Main file path: `app.py` → Deploy.
