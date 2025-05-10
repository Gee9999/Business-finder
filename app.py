
import streamlit as st, pandas as pd, asyncio, io
from scraper import scrape_location_async, enrich_with_hunter

st.set_page_config(page_title="Business Finder (DuckDuckGo)", layout="wide")
st.title("🏢 Business Finder – Free & Unlimited Edition")

st.markdown("""Search for schools, hotels, hospitals – any institution – by towns **or** countries.  
Uses **DuckDuckGo** (no API keys, unlimited) and asynchronous scraping for speed.
""")

# --- UI ---
kw_col, loc_col = st.columns(2)
with kw_col:
    keyword = st.text_input("Institution keyword", placeholder="e.g. schools")
with loc_col:
    location_input = st.text_input("Locations (comma‑separated towns or countries)",
                                   value="Cape Town, Durban, South Africa")

max_sites = st.slider("Websites per location", 5, 50, 10, 5)
hunter_key = st.text_input("Hunter.io API key (optional)", type="password")

# --- Main button ---
if st.button("🔎 Find leads"):
    if not keyword:
        st.error("Please enter a keyword.")
        st.stop()

    locations = [loc.strip() for loc in location_input.split(",") if loc.strip()]
    progress = st.progress(0)
    status = st.empty()

    async def runner():
        leads_all = []
        for idx, loc in enumerate(locations):
            status.info(f"Searching {loc} ...")
            loc_leads = await scrape_location_async(keyword, loc, max_sites)
            for lead in loc_leads:
                lead["location"] = loc
            leads_all.extend(loc_leads)
            progress.progress((idx + 1) / len(locations))
        return leads_all

    raw_leads = asyncio.new_event_loop().run_until_complete(runner())
    final_leads = enrich_with_hunter(raw_leads, hunter_key)
    df = pd.DataFrame(final_leads)

    st.success(f"Found {len(df)} leads across {', '.join(locations)}")
    st.dataframe(df, use_container_width=True)

    excel_bytes = io.BytesIO()
    with pd.ExcelWriter(excel_bytes, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    st.download_button("⬇️ Download Excel", excel_bytes.getvalue(), file_name="business_leads.xlsx")
