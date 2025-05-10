import re, asyncio, aiohttp, requests, os
from googleapiclient.discovery import build

NEGATIVE={"directory","yellowpages","listing","schoolguide","educonnect"}
EMAIL_RE=re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

API_KEY=os.getenv("GOOGLE_API_KEY")
CX_ID=os.getenv("GOOGLE_CX")

def google_first_site(name:str,max_results:int=3)->str:
    if not API_KEY or not CX_ID:
        return ""
    service=build("customsearch","v1",developerKey=API_KEY,cache_discovery=False)
    try:
        res=service.cse().list(q=f'"{name}" official site',cx=CX_ID,num=max_results).execute()
        for item in res.get("items",[]):
            url=item["link"]
            dom=url.split("/")[2]
            if not any(b in dom for b in NEGATIVE):
                return url
    except Exception:
        pass
    return ""

async def fetch_html(session,url,max_bytes=120_000):
    try:
        async with session.get(url,timeout=4) as r:
            return (await r.content.read(max_bytes)).decode("utf-8",errors="ignore")
    except Exception:
        return ""

async def hunter(domain,key):
    try:
        r=requests.get("https://api.hunter.io/v2/domain-search",params={"domain":domain,"api_key":key},timeout=4)
        if r.status_code==200:
            emails=[e["value"] for e in r.json().get("data",{}).get("emails",[])]
            return ", ".join(emails)
    except Exception:
        pass
    return ""

async def map_school(name:str,hunter_key:str,max_results:int=3)->dict:
    url=google_first_site(name,max_results)
    emails=""
    if url:
        async with aiohttp.ClientSession(headers={"User-Agent":"Mozilla/5.0"}) as s:
            html=await fetch_html(s,url)
            emails=", ".join(set(EMAIL_RE.findall(html)))
    if not emails and hunter_key and url:
        emails=await asyncio.get_event_loop().run_in_executor(None,hunter,url.split("/")[2],hunter_key)
    return {"website":url,"emails_found":emails}
