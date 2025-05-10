
import streamlit as st, pandas as pd, io, asyncio
from mapper import map_school

st.set_page_config(page_title="School Website Mapper", layout="wide")
st.title("🏫 School Website & Email Mapper")

st.markdown("""Upload the SA EMIS schools list (Excel or CSV), and I'll try to find each school's official website and scrape contact e‑mails automatically.""")

file = st.file_uploader("📄 Upload EMIS XLSX / CSV", type=["xlsx", "csv"])
hunter_key = st.text_input("Hunter.io API key (optional)", type="password")
max_sites = st.slider("Max websites to scan per school", 1, 5, 2)

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file, encoding="utf-8", on_bad_lines="skip")
    else:
        df = pd.read_excel(file, engine="openpyxl")
    df.columns = [c.lower() for c in df.columns]
    required = {"province", "district", "school name"}
    if not required.issubset(df.columns):
        st.error(f"CSV/XLSX must contain columns: {', '.join(required)}")
        st.stop()
    st.write(f"Loaded {len(df)} rows.")

    if st.button("🔎 Map websites & emails"):
        progress = st.progress(0)
        status = st.empty()
        results = []

        async def runner():
            for idx, row in df.iterrows():
                status.info(f"Searching {row['school name']} ({idx+1}/{len(df)})")
                mapped = await map_school(row['school name'], hunter_key, max_sites)
                mapped.update({
                    "province": row['province'],
                    "district": row['district'],
                    "school name": row['school name']
                })
                results.append(mapped)
                progress.progress((idx + 1) / len(df))
            return results

        asyncio.new_event_loop().run_until_complete(runner())
        resdf = pd.DataFrame(results)
        st.success(f"Found websites for {resdf['website'].astype(bool).sum()} of {len(resdf)} schools.")
        st.dataframe(resdf, use_container_width=True)

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            resdf.to_excel(writer, index=False, sheet_name="Websites")
        st.download_button("⬇️ Download Excel", buf.getvalue(), file_name="school_websites.xlsx")
