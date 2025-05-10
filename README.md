
# School Website & Email Mapper

Upload an EMIS Excel/CSV of South African schools → the app finds likely official websites and contact emails.

## Columns required
* `Province`, `District`, `School Name`

## Quick run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional: set `HUNTER_API_KEY` as an environment variable or paste it in the UI for extra email enrichment.
