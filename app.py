
import streamlit as st, pandas as pd, asyncio, io, os
from mapper import find_school_websites

st.set_page_config(page_title="School Mapper", layout="wide")
st.title("🏫 School Website Mapper – Official Registry Edition")

st.markdown("""Upload the **official South African schools CSV** (EMIS list).  
The app will attempt to find each school's official website automatically.

*Steps*  
1. Upload CSV.  
2. Select provinces / districts if you want a subset.  
3. Click **Map websites** – the app searches DuckDuckGo for each school, filters out directories, and returns likely websites + e‑mails.  
4. Download the Excel output.
""")

uploaded = st.file_uploader("📄 Upload school list CSV", type=["csv"])
if uploaded:
    schools_df = pd.read_csv(uploaded, encoding="utf-8", on_bad_lines="skip")

    # Guess column names (adjust if needed)
    cols = [c.lower() for c in schools_df.columns]
    if "province" in cols and "district" in cols and "school name" in cols:
        schools_df.columns = cols
    else:
        st.error("CSV must contain columns: 'Province', 'District', 'School Name'")
        st.stop()

    provinces = st.multiselect("Province filter (blank = all)", options=sorted(schools_df["province"].unique()))
    if provinces:
        schools_df = schools_df[schools_df["province"].isin(provinces)]

    districts = st.multiselect("District filter (blank = all)", options=sorted(schools_df["district"].unique()))
    if districts:
        schools_df = schools_df[schools_df["district"].isin(districts)]

    st.write(f"**{len(schools_df)} schools selected**")
    max_per_school = st.slider("Max websites to scan per school", 1, 5, 2)
    hunter_key = st.text_input("Hunter.io API key (optional email enrichment)", type="password")

    if st.button("🔎 Map websites"):
        progress = st.progress(0)
        status = st.empty()

        async def runner():
            leads = []
            for idx, row in schools_df.iterrows():
                status.info(f"Searching {row['school name']} …")
                result = await find_school_websites(row['school name'], max_per_school, hunter_key)
                result.update({
                    "province": row['province'],
                    "district": row['district'],
                    "school name": row['school name']
                })
                leads.append(result)
                progress.progress((idx + 1) / len(schools_df))
            return leads

        mapped = asyncio.new_event_loop().run_until_complete(runner())
        df = pd.DataFrame(mapped)
        st.success(f"Completed – {df['website'].astype(bool).sum()} websites found.")
        st.dataframe(df, use_container_width=True)

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Websites")
        st.download_button("⬇️ Download Excel", buf.getvalue(), file_name="school_websites.xlsx")
