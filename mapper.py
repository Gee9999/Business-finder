
"""Mapper helpers: find likely website & emails for a school name."""
import re, requests, asyncio, aiohttp
from duckduckgo_search import DDGS

NEGATIVE = {"directory", "yellowpages", "listing", "schoolguide", "educonnect"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")

def ddg_first_site(name: str, max_results: int = 3) -> str:
    q = f'"{name}" official site -facebook -{" -".join(NEGATIVE)}'
    with DDGS() as ddgs:
        for r in ddgs.text(q, max_results=max_results):
            url = r.get("href", "")
            dom = url.split("/")[2] if "//" in url else ""
            if dom and not any(b in dom for b in NEGATIVE):
                return url
    return ""

async def fetch_html(session: aiohttp.ClientSession, url: str, max_bytes: int = 120_000) -> str:
    try:
        await session.head(url, timeout=4)
        async with session.get(url, timeout=4) as r:
            return (await r.content.read(max_bytes)).decode("utf-8", errors="ignore")
    except Exception:
        return ""

async def hunter(domain: str, key: str) -> str:
    try:
        r = requests.get("https://api.hunter.io/v2/domain-search",
                         params={"domain": domain, "api_key": key}, timeout=4)
        if r.status_code == 200:
            emails = [e["value"] for e in r.json().get("data", {}).get("emails", [])]
            return ", ".join(emails)
    except Exception:
        pass
    return ""

async def map_school(name: str, hunter_key: str, max_results: int = 3) -> dict:
    url = ddg_first_site(name, max_results)
    emails = ""
    if url:
        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            html = await fetch_html(session, url)
            emails = ", ".join(set(EMAIL_RE.findall(html)))
    if not emails and hunter_key and url:
        emails = await asyncio.get_event_loop().run_in_executor(None, hunter, url.split("/")[2], hunter_key)
    return {"website": url, "emails_found": emails}
