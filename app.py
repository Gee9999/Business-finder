
import streamlit as st, pandas as pd, asyncio, io
from scraper import scrape_location_async, enrich_with_hunter

st.set_page_config(page_title="Business Finder (Schools Wide Filter)", layout="wide")
st.title("🏫 Business Finder – School Leads (Wide Filter)")

st.markdown("""Looks for **school websites** and filters out obvious directories.  
* A result must either:  
  1. Have a domain ending in one of the allowed suffixes (editable). **OR**  
  2. Contain the word “school” in the domain name.  
Negative keywords `directory`, `listing`, `yellowpages` are still excluded.
""")

kw_col, loc_col = st.columns(2)
with kw_col:
    keyword = st.text_input("Institution keyword", value="schools")
with loc_col:
    location_input = st.text_input("Locations (comma‑separated)", value="Cape Town, Durban, South Africa")

max_sites = st.slider("Websites per location", 5, 50, 10, 5)
hunter_key = st.text_input("Hunter.io API key (optional)", type="password")
strict = st.checkbox("Require domain to end with allowed suffix (un‑check = school keyword OK)", value=True)

if st.button("🔎 Find leads"):
    locations = [l.strip() for l in location_input.split(",") if l.strip()]
    progress = st.progress(0)
    status = st.empty()

    async def runner():
        leads_all = []
        for idx, loc in enumerate(locations):
            status.info(f"Searching {loc} …")
            loc_leads = await scrape_location_async(keyword, loc, max_sites, strict)
            for ld in loc_leads:
                ld["location"] = loc
            leads_all.extend(loc_leads)
            progress.progress((idx + 1) / len(locations))
        return leads_all

    raw = asyncio.new_event_loop().run_until_complete(runner())
    final = enrich_with_hunter(raw, hunter_key)
    df = pd.DataFrame(final)

    st.success(f"Found {len(df)} leads across {', '.join(locations)}")
    st.dataframe(df, use_container_width=True)

    excel_bytes = io.BytesIO()
    with pd.ExcelWriter(excel_bytes, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    st.download_button("⬇️ Download Excel", excel_bytes.getvalue(), file_name="school_leads.xlsx")
