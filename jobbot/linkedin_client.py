import random
import re
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
import urllib3

from jobbot.models import Job

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

DEFAULT_HEADERS = {
    "authority": "www.linkedin.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _extract_job_id(href: str) -> Optional[str]:
    href = href.split("?")[0]
    m = re.search(r"-(\d+)$", href)
    if m:
        return m.group(1)
    m2 = re.search(r"/jobs/view/(\d+)", href)
    return m2.group(1) if m2 else None


def fetch_jobs(
    keywords: str,
    location: str,
    hours: int,
    experience_levels: str = "",
    f_WT: str = "",
    easy_apply: bool = False,
    company_ids: List[int] = None,
    filter_out_companies: List[str] = None,
    max_results: int = 50,
) -> List[Job]:
    """
    Scrapes LinkedIn for jobs using strict API filters and localized exclusions.
    """
    if company_ids is None:
        company_ids = []
    if filter_out_companies is None:
        filter_out_companies = []

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    jobs: List[Job] = []
    seen_ids: set[str] = set()
    start_offset = 0
    seconds_old = hours * 3600

    print(
        f"[*] Scraping LinkedIn for '{keywords}' in '{location}' (Past {hours} hours)..."
    )

    while len(jobs) < max_results and start_offset < 1000:
        params = {
            "keywords": keywords,
            "location": location,
            "start": start_offset,
            "f_TPR": f"r{seconds_old}",
        }

        if experience_levels:
            params["f_E"] = experience_levels
        if f_WT:
            params["f_WT"] = f_WT
        if easy_apply:
            params["f_AL"] = "true"
        if company_ids:
            params["f_C"] = ",".join(str(x) for x in company_ids)

        try:
            resp = session.get(SEARCH_URL, params=params, timeout=12, verify=False)
        except Exception as e:
            print(f"[!] Network error: {e}")
            break

        if resp.status_code == 429:
            print("[!] Rate limited by LinkedIn (429).")
            break
        if resp.status_code >= 400:
            print(f"[!] HTTP Error {resp.status_code}.")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.find_all("div", class_="base-search-card")

        if not job_cards:
            break

        for card in job_cards:
            link_tag = card.find("a", class_="base-card__full-link")
            if not link_tag:
                continue

            job_url = link_tag.get("href", "")
            job_id = _extract_job_id(job_url)

            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title_tag = card.find("span", class_="sr-only")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            company_tag = card.find("h4", class_="base-search-card__subtitle")
            company = company_tag.get_text(strip=True) if company_tag else "N/A"

            # Filter out companies by name if requested (case-insensitive substring match)
            if filter_out_companies:
                comp_lower = company.lower()
                blocked = any(
                    block.lower().strip() in comp_lower
                    for block in filter_out_companies
                    if block
                )
                if blocked:
                    print(f"[-] Skipping filtered company: {company}")
                    continue

            jobs.append(
                Job(
                    job_id=job_id,
                    job_url=job_url.split("?")[0],
                    title=title,
                    company_name=company,
                )
            )

            if len(jobs) >= max_results:
                break

        start_offset += len(job_cards)
        time.sleep(2.5 + random.random() * 1.5)

    return jobs


def fetch_description(job_url: str) -> Optional[str]:
    """
    Fetches the full text description.
    This will be called by the pipeline ONLY for brand new, non-duplicate jobs.
    """
    try:
        resp = requests.get(job_url, headers=DEFAULT_HEADERS, timeout=12, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")

        div = soup.find(
            "div", class_=lambda x: x and "show-more-less-html__markup" in x
        )
        if not div:
            return None

        text = soup.get_text(separator=" ")
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return None
