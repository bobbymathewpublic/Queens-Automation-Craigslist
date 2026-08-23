import asyncio
import csv
import os
from itertools import product
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin

from playwright.async_api import async_playwright


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOCATIONS_FILE = INPUT_DIR / "locations.txt"
CATEGORIES_FILE = INPUT_DIR / "categories.txt"
QUERIES_FILE = INPUT_DIR / "queries.txt"
OUTPUT_FILE = OUTPUT_DIR / "craigslist_listings.csv"


def load_dotenv(path):
    """Load simple KEY=VALUE entries without an extra package."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing configuration file: {path}")

    with path.open(encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_proxy_config():
    load_dotenv(ENV_FILE)
    keys = ("PROXY_SERVER", "PROXY_USERNAME", "PROXY_PASSWORD")
    missing = [key for key in keys if not os.environ.get(key)]
    if missing:
        raise ValueError(f"Missing required .env value(s): {', '.join(missing)}")
    return {
        "server": os.environ["PROXY_SERVER"],
        "username": os.environ["PROXY_USERNAME"],
        "password": os.environ["PROXY_PASSWORD"],
    }


def load_values(path):
    """Read one non-empty value per line from a plain-text input file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing input text file: {path}")

    with path.open(encoding="utf-8-sig") as input_file:
        values = [line.strip() for line in input_file if line.strip()]
    if not values:
        raise ValueError(f"{path.name} has no values.")
    return values


def load_searches():
    """Return one search for every location × category × query combination."""
    locations = load_values(LOCATIONS_FILE)
    categories = load_values(CATEGORIES_FILE)
    queries = load_values(QUERIES_FILE)
    return [
        {"location": location, "category": category, "query": query}
        for location, category, query in product(locations, categories, queries)
    ]


def build_search_url(location, category, query):
    """Build a URL whose query is an exact quoted phrase."""
    location = location.strip().strip("/")
    exact_query = f'"{query.strip().strip(chr(34))}"'
    params = urlencode({"cat": category, "query": exact_query}, quote_via=quote)
    return f"https://www.craigslist.org/search/area/{location}?{params}"


async def scrape_craigslist_housing(url, max_listings, proxy):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, proxy=proxy)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        await page.wait_for_selector("div.result-info", timeout=10000)

        previous_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 50
        while scroll_attempts < max_scroll_attempts:
            current_count = len(await page.query_selector_all("div.result-info"))
            print(f"Loaded {current_count} listings (target: {max_listings})")
            if current_count >= max_listings or current_count == previous_count:
                break
            previous_count = current_count
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            scroll_attempts += 1

        listing_elements = (await page.query_selector_all("div.result-info"))[:max_listings]
        print(f"Processing {len(listing_elements)} listings")
        results = []
        for listing in listing_elements:
            try:
                location_elem = await listing.query_selector("div:first-child")
                location = await location_elem.inner_text() if location_elem else ""

                title = listing_url = ""
                for selector in ["div.title-blob > a", "a.posting-title", ".result-title", "a"]:
                    title_elem = await listing.query_selector(selector)
                    if title_elem:
                        title = await title_elem.inner_text()
                        listing_url = urljoin(url, await title_elem.get_attribute("href") or "")
                        break

                date = ""
                for selector in ["div.meta > span:first-child", "time", ".result-date", "span.meta"]:
                    elem = await listing.query_selector(selector)
                    if elem:
                        date = await elem.inner_text()
                        break

                price = ""
                for selector in ["div.meta > span.priceinfo", ".result-price", "span.priceinfo", "span.price"]:
                    elem = await listing.query_selector(selector)
                    if elem:
                        price = await elem.inner_text()
                        break

                bedrooms = ""
                for selector in ["div.meta > span.housing-meta > span", ".housing", "span.housing"]:
                    elem = await listing.query_selector(selector)
                    if elem:
                        bedrooms = await elem.inner_text()
                        break

                results.append({"location": location.strip(), "title": title.strip(),
                                "date": date.strip(), "price": price.strip(),
                                "bedrooms": bedrooms.strip(), "url": listing_url.strip()})
            except Exception:
                continue

        await browser.close()
        return results


def save_to_csv(data, filename=OUTPUT_FILE):
    fields = ["search_location", "search_category", "search",
              "location", "title", "date", "price", "bedrooms", "url"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} listings to {filename}")


async def main():
    proxy = get_proxy_config()
    searches = load_searches()

    max_listings = 100
    all_listings = []
    for search in searches:
        url = build_search_url(**search)
        print(f"Scraping {url} (target: {max_listings})...")
        listings = await scrape_craigslist_housing(url, max_listings, proxy)
        for listing in listings:
            listing.update({"search_location": search["location"],
                            "search_category": search["category"],
                            "search": search["query"].replace('"', "|")})
        all_listings.extend(listings)

    if not all_listings:
        print("No listings found.")
        return
    save_to_csv(all_listings)


if __name__ == "__main__":
    asyncio.run(main())
