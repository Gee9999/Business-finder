
import asyncio, aiohttp, re
from duckduckgo_search import DDGS
import requests

NEGATIVE_TERMS = "-directory -directories -listing -yellowpages"

# Allowed suffixes
ALLOWED_SUFFIXES = (
    ".edu.za", ".school.za",
    ".co.za", ".org.za",
    ".edu", ".school",
    ".com"
)

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HEADERS = {"User-Agent": "Mozilla/5.0 DuckDuckBot"}
CONCURRENT = 15

def extract_emails(text: str):
    return EMAIL_REGEX.findall(text)

def is_school_domain(domain: str, strict: bool):
    domain_lower = domain.lower()
    suffix_ok = domain_lower.endswith(ALLOWED_SUFFIXES)
    keyword_ok = ("school" in domain_lower)
    return suffix_ok or (keyword_ok and not strict)

def ddg_search(query: str, max_results: int, strict: bool):
    full_query = f"{query} {NEGATIVE_TERMS}"
    with DDGS() as ddgs:
        raw = ddgs.text(full_query, max_results=max_results)
        urls = [r["href"] for r in raw if r.get("href", "").startswith("http")]
    # filter
    filtered = []
    for url in urls:
        try:
            domain = url.split("/")[2]
        except IndexError:
            continue
        if is_school_domain(domain, strict):
            filtered.append(url)
    return filtered

async def fetch_site(session, url, max_bytes=120_000):
    try:
        await session.head(url, timeout=3)
        async with session.get(url, timeout=3) as resp:
            return await resp.content.read(max_bytes)
    except Exception:
        return b""

async def scrape_site(session, url):
    html_bytes = await fetch_site(session, url)
    emails = ", ".join(set(extract_emails(html_bytes.decode("utf-8", errors="ignore"))))
    return {"website": url, "emails_found": emails}

async def scrape_location_async(keyword: str, location: str, max_sites: int, strict: bool):
    sites = ddg_search(f"{keyword} {location}", max_sites, strict)
    sem = asyncio.Semaphore(CONCURRENT)
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async def worker(u):
            async with sem:
                return await scrape_site(session, u)
        return await asyncio.gather(*(worker(s) for s in sites))

def enrich_with_hunter(leads, api_key):
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
