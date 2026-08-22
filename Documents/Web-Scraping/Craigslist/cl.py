import asyncio
from playwright.async_api import async_playwright
import csv
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import quote_plus

# Proxy configuration
PROXY_USERNAME = "spra6q3w3h"
PROXY_PASSWORD = "8v0A1mcgk3Bt+SSdod"
PROXY_SERVER = "gate.decodo.com:10000"

async def scrape_craigslist_jobs(url, max_listings=100):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": PROXY_SERVER}
        )
        
        context = await browser.new_context(
            proxy={
                "server": PROXY_SERVER,
                "username": PROXY_USERNAME,
                "password": PROXY_PASSWORD
            }
        )
        
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        # Wait for initial listings to load
        await page.wait_for_selector('div.result-info', timeout=10000)
        
        # Infinite scroll to load more listings
        previous_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 50
        
        while scroll_attempts < max_scroll_attempts:
            # Get current listing count
            current_listings = await page.query_selector_all('div.result-info')
            current_count = len(current_listings)
            
            print(f"Loaded {current_count} listings (target: {max_listings})")
            
            # Stop if we have enough listings or no new content loaded
            if current_count >= max_listings or current_count == previous_count:
                break
            
            previous_count = current_count
            
            # Scroll to bottom
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
            
            scroll_attempts += 1
        
        # Get all loaded listings
        listings = await page.query_selector_all('div.result-info')
        print(f"\nFound {len(listings)} total listings")
        
        # Limit to max_listings
        listings = listings[:max_listings]
        print(f"Processing {len(listings)} listings")
        
        results = []
        for listing in listings:
            try:
                # Extract location
                location_elem = await listing.query_selector('div:first-child')
                location = await location_elem.inner_text() if location_elem else ""
                
                # Extract title and URL
                title_selectors = ['div.title-blob > a', 'a.posting-title', '.result-title']
                title = ""
                listing_url = ""
                for sel in title_selectors:
                    title_elem = await listing.query_selector(sel)
                    if title_elem:
                        title_span = await title_elem.query_selector('span')
                        title = await title_span.inner_text() if title_span else await title_elem.inner_text()
                        href = await title_elem.get_attribute('href') or ""
                        listing_url = urljoin(url, href)
                        break
                
                # Extract date
                date_elem = await listing.query_selector('div.meta > span:first-child')
                date = await date_elem.inner_text() if date_elem else ""
                
                # Extract compensation and company by getting text nodes between separators
                meta_elem = await listing.query_selector('div.meta')
                
                compensation_company_parts = []
                if meta_elem:
                    # Get all child nodes after the first span (date)
                    children = await meta_elem.evaluate_handle('''
                        (element) => {
                            const parts = [];
                            let foundFirstSpan = false;
                            
                            for (let node of element.childNodes) {
                                // Skip the first span (date)
                                if (!foundFirstSpan && node.nodeName === 'SPAN' && !node.classList.contains('separator')) {
                                    foundFirstSpan = true;
                                    continue;
                                }
                                
                                if (foundFirstSpan) {
                                    // Stop at button
                                    if (node.nodeName === 'BUTTON') break;
                                    
                                    // Add separator dot for separator spans
                                    if (node.nodeName === 'SPAN' && node.classList.contains('separator')) {
                                        parts.push(' ⸱ ');
                                    }
                                    // Add text content for text nodes and other spans
                                    else if (node.textContent && node.textContent.trim()) {
                                        parts.push(node.textContent.trim());
                                    }
                                }
                            }
                            
                            return parts.join('');
                        }
                    ''')
                    
                    compensation_company = await children.json_value()
                    # Remove leading separator if present
                    compensation_company = compensation_company.strip()
                    if compensation_company.startswith('⸱'):
                        compensation_company = compensation_company[1:].strip()
                    compensation_company = compensation_company if compensation_company else "N/A"
                else:
                    compensation_company = "N/A"
                
                results.append({
                    'location': location.strip(),
                    'title': title.strip(),
                    'date': date.strip(),
                    'compensation_company': compensation_company,
                    'url': listing_url.strip()
                })
                
            except Exception as e:
                continue
        
        await browser.close()
        return results

def read_csv_values(filename, column_name):
    """Return non-empty values from a one-column CSV file.

    The CSV should have a header matching ``column_name`` (for example,
    ``location`` or ``query``).  A headerless one-column CSV is accepted too.
    """
    path = Path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"Required input file not found: {path}")

    with path.open(newline='', encoding='utf-8-sig') as file:
        rows = list(csv.reader(file))

    if not rows:
        return []

    first_value = rows[0][0].strip() if rows[0] else ''
    data_rows = rows[1:] if first_value.lower() == column_name.lower() else rows
    return [row[0].strip() for row in data_rows if row and row[0].strip()]


def save_to_csv(data, filename='craigslist_jobs.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'craigslist_location', 'search_query', 'location', 'title',
                'craigslist_category', 'date', 'compensation_company', 'url'
            ]
        )
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} listings to {filename}")

async def main():
    base_dir = Path(__file__).resolve().parent
    locations = read_csv_values(base_dir / 'locations.csv', 'location')
    queries = read_csv_values(base_dir / 'queries.csv', 'query')
    categories = read_csv_values(base_dir / 'categories.csv', 'category')

    if not locations or not queries or not categories:
        raise ValueError(
            'locations.csv, queries.csv, and categories.csv must each contain at least one value.'
        )

    max_listings = 100
    all_listings = []

    # Run every location/category/query combination as an independent search.
    for craigslist_location in locations:
        for craigslist_category in categories:
            for query in queries:
                encoded_query = quote_plus(query)
                url = (
                    f"https://{craigslist_location}.craigslist.org/search/{craigslist_category}"
                    f"?query={encoded_query}#search=1~thumb~0"
                )
                print(
                    f"\nScraping location={craigslist_location!r}, "
                    f"category={craigslist_category!r}, query={query!r} "
                    f"(target: {max_listings})..."
                )
                listings = await scrape_craigslist_jobs(url, max_listings)

                for listing in listings:
                    listing['craigslist_location'] = craigslist_location
                    listing['craigslist_category'] = craigslist_category
                    listing['search_query'] = query
                all_listings.extend(listings)
                print(f"Found {len(listings)} listings for this search.")

    if not all_listings:
        print('No listings found.')
        return

    save_to_csv(all_listings, base_dir / 'craigslist_jobs.csv')

if __name__ == "__main__":
    asyncio.run(main())
