
import asyncio, aiohttp, re
from duckduckgo_search import DDGS
import requests

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HEADERS = {"User-Agent": "Mozilla/5.0 DuckDuckBot"}
CONCURRENT = 15

def extract_emails(text: str):
    return EMAIL_REGEX.findall(text)

def ddg_search(query: str, max_results: int = 10):
    with DDGS() as ddgs:
        return [r["href"] for r in ddgs.text(query, max_results=max_results)
                if r.get("href", "").startswith("http")]

async def fetch_site(session: aiohttp.ClientSession, url: str, max_bytes: int = 120_000):
    try:
        await session.head(url, timeout=3)
        async with session.get(url, timeout=3) as resp:
            return await resp.content.read(max_bytes)
    except Exception:
        return b""

async def scrape_site(session: aiohttp.ClientSession, url: str):
    html_bytes = await fetch_site(session, url)
    emails = ", ".join(set(extract_emails(html_bytes.decode("utf-8", errors="ignore"))))
    return {"website": url, "emails_found": emails}

async def scrape_location_async(keyword: str, location: str, max_sites: int):
    query = f"{keyword} {location}"
    sites = ddg_search(query, max_results=max_sites)
    sem = asyncio.Semaphore(CONCURRENT)
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async def worker(u):
            async with sem:
                return await scrape_site(session, u)
        return await asyncio.gather(*(worker(s) for s in sites))

def enrich_with_hunter(leads: list, api_key: str):
    if not api_key:
        return leads
    for lead in leads:
        if lead["emails_found"]:
            continue
        try:
            domain = lead["website"].split("/")[2]
            r = requests.get("https://api.hunter.io/v2/domain-search",
                             params={"domain": domain, "api_key": api_key},
                             timeout=3)
            if r.status_code == 200:
                emails = [e["value"] for e in r.json().get("data", {}).get("emails", [])]
                if emails:
                    lead["emails_found"] = ", ".join(emails)
        except Exception:
            pass
    return leads
