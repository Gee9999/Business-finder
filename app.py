import streamlit as st, pandas as pd, io, asyncio
from mapper import map_school

st.set_page_config(page_title="School Website Mapper (Google API)", layout="wide")
st.title("🏫 School Website & Email Mapper – Google 100‑free‑search Edition")

st.markdown("Upload SA EMIS schools list (Excel/CSV) and map each school to its likely official website using Google Programmable Search (100 free queries/day).")

file=st.file_uploader("📄 Upload EMIS XLSX / CSV", type=["xlsx","csv"])
hunter_key=st.text_input("Hunter.io API key (optional)", type="password")
max_sites=st.slider("Google results to scan per school",1,5,2)

if file:
    df=pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file, encoding="utf-8", on_bad_lines="skip")
    df.columns=[c.lower() for c in df.columns]
    required={"province","district","school name"}
    if not required.issubset(df.columns):
        st.error(f"File must contain columns: {', '.join(required)}")
        st.stop()
    st.write(f"Loaded {len(df)} schools")
    if st.button("🔎 Map websites"):
        progress=st.progress(0)
        status=st.empty()
        results=[]
        async def runner():
            for i,row in df.iterrows():
                status.info(f"Processing {row['school name']} ({i+1}/{len(df)})")
                mapped=await map_school(row['school name'], hunter_key, max_sites)
                mapped.update({"province":row['province'],"district":row['district'],"school name":row['school name']})
                results.append(mapped)
                progress.progress((i+1)/len(df))
        asyncio.new_event_loop().run_until_complete(runner())
        resdf=pd.DataFrame(results)
        st.success(f"Websites found for {resdf['website'].astype(bool).sum()} of {len(resdf)} schools")
        st.dataframe(resdf,use_container_width=True)
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as w:
            resdf.to_excel(w,index=False,sheet_name="Websites")
        st.download_button("⬇️ Download Excel", buf.getvalue(), file_name="school_websites.xlsx")
