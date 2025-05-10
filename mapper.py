
import aiohttp, asyncio, re, requests
from duckduckgo_search import DDGS

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DIR_BLOCK = {"directory", "yellowpages", "listing", "schools. co. za", "schoolguide", "schooldirectory"}

async def fetch(session, url):
    try:
        async with session.get(url, timeout=4) as r:
            return await r.text()
    except Exception:
        return ""

def ddg_first_domain(school_name, max_results=3):
    query = f'"{school_name}" official site -facebook -directory'
    with DDGS() as ddgs:
        res = ddgs.text(query, max_results=max_results)
        for r in res:
            url = r.get("href", "")
            domain = url.split("/")[2] if "://" in url else ""
            if domain and not any(block in domain for block in DIR_BLOCK):
                return url
    return ""

async def enrich_hunter(domain, api_key):
    try:
        r = requests.get("https://api.hunter.io/v2/domain-search",
                         params={"domain": domain, "api_key": api_key},
                         timeout=4)
        if r.status_code == 200:
            data = r.json()
            emails = [e["value"] for e in data.get("data", {}).get("emails", [])]
            return ", ".join(emails)
    except Exception:
        pass
    return ""

async def find_school_websites(school_name, max_sites, hunter_key):
    url = ddg_first_domain(school_name, max_results=max_sites)
    if not url:
        return {"website": "", "emails_found": ""}

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        html = await fetch(session, url)
        emails = ", ".join(set(EMAIL_REGEX.findall(html)))
    if not emails and hunter_key:
        emails = await asyncio.get_event_loop().run_in_executor(
            None, enrich_hunter, url.split("/")[2], hunter_key
        )
    return {"website": url, "emails_found": emails}
