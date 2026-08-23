# AI prompt guide: building `craigslist_bot.py`

Use these prompts in order with a coding AI to recreate the current local scraper. Replace bracketed values with your own values. Do not put real proxy credentials in a prompt or source file; store them only in `.env`.

## 1. Create the project skeleton

```text
Create a Python 3 project named Craigslist with a main script named craigslist_bot.py.

Use Playwright's asynchronous Python API. Keep all project paths relative to the directory containing craigslist_bot.py. The project should use this structure:

Craigslist/
├── craigslist_bot.py
├── .env
├── input/
│   ├── locations.txt
│   ├── categories.txt
│   └── queries.txt
└── output/
    └── craigslist_listings.csv

Use pathlib.Path for paths. Do not hard-code an absolute local path.
```

## 2. Add private proxy configuration

```text
In craigslist_bot.py, load PROXY_SERVER, PROXY_USERNAME, and PROXY_PASSWORD from a .env file beside the script.

Do not require python-dotenv; write a small loader for simple KEY=VALUE lines. Ignore blank lines and # comments, trim surrounding single or double quotes from values, and do not overwrite environment variables that are already set by the operating system.

Raise a clear FileNotFoundError when .env is absent and a ValueError listing missing proxy settings when any required setting is empty. Return a Playwright-compatible proxy dictionary with server, username, and password keys.
```

## 3. Read plain-text search inputs

```text
Use three plain-text files in input/: locations.txt, categories.txt, and queries.txt.

Each non-empty line is one value. There is no CSV header and no comma parsing. Read the files as UTF-8 with BOM support, trim whitespace from every line, ignore blank lines, and raise a clear error if a file is missing or contains no usable values.

Create a load_searches() function that returns every Cartesian-product combination of location × category × query as dictionaries with location, category, and query keys.
```

## 4. Build exact-phrase Craigslist URLs

```text
Create build_search_url(location, category, query) for Craigslist URLs in this format:

https://www.craigslist.org/search/area/{location}?cat={category}&query={query}

Strip surrounding whitespace and slashes from location. Treat every query as an exact quoted phrase: remove only outer double quotes if they already exist, then add one pair of double quotes. URL-encode parameters so spaces become %20 and quotes become %22, not +. For example, location=newyork, category=jjj, query=business partner wanted must produce:

https://www.craigslist.org/search/area/newyork?cat=jjj&query=%22business%20partner%20wanted%22
```

## 5. Implement the Playwright scraper

```text
Create an async function scrape_craigslist_housing(url, max_listings, proxy) using async_playwright.

Launch Chromium with the supplied authenticated proxy. For development, use headless=False. Create a browser context and page, go to the URL with wait_until="domcontentloaded" and a 30-second timeout, wait briefly, then wait up to 10 seconds for div.result-info.

Implement controlled infinite scrolling: stop when max_listings is loaded, no new listings appear after a scroll, or 50 scroll attempts are reached. Print the current number of loaded listings.

For every listing, extract location, title, listing URL, date, price, and bedrooms/housing metadata. Use fallback CSS selectors because Craigslist markup can vary. Turn relative listing hrefs into absolute URLs with urllib.parse.urljoin. If one listing cannot be extracted, skip that listing and continue. Close the browser and return a list of dictionaries.
```

## 6. Define output CSV behavior

```text
Create save_to_csv(data) to write output/craigslist_listings.csv. Create output/ automatically if it does not exist.

Write UTF-8 CSV with this exact column order:

search_location, search_category, search, location, title, date, price, bedrooms, url

Do not include a search_query column. The search column must be the original query text with every double quote (") replaced by a pipe (|). For example, "business partner wanted" "for" becomes |business partner wanted| |for|.
```

## 7. Connect the complete workflow

```text
Create async main() for the Craigslist scraper.

1. Load and validate the proxy configuration.
2. Load all location × category × query combinations.
3. Set max_listings to 100 per generated search URL.
4. For each combination, build the URL, print it, and call the async scraper.
5. Add search_location, search_category, and the pipe-formatted search value to every returned listing.
6. Combine all listing results.
7. If no listings were found, print a message and do not create an output file; otherwise write output/craigslist_listings.csv.

Run main() only when the file is executed directly, using asyncio.run(main()).
```

## 8. Add verification and documentation

```text
Verify the script with python3 -m py_compile craigslist_bot.py. Add a small unit-style check, without running a live browser, that confirms:

- text input files create the expected search combinations;
- a query with spaces produces %20 in the URL;
- a quoted query becomes a pipe-formatted search output value;
- the CSV output field list does not contain search_query.

Write a README.md explaining setup, Playwright installation, .env variables, the three text input files, exact quoted URL generation, output columns, and how to run the script. Keep .env and input/ untracked by Git.
```

## Single all-in-one prompt

If you prefer one request, use this condensed prompt:

```text
Build a Python async Playwright Craigslist scraper named craigslist_bot.py. Load authenticated proxy values from a private co-located .env file with PROXY_SERVER, PROXY_USERNAME, and PROXY_PASSWORD. Read locations.txt, categories.txt, and queries.txt from input/, with one trimmed non-empty value per line and no headers. Scrape every location × category × query combination.

Build URLs as https://www.craigslist.org/search/area/{location}?cat={category}&query={query}. Each query must be an exact quoted phrase and URL-encoded with spaces as %20 and quotes as %22. Launch Chromium through the proxy, load div.result-info listings, scroll until enough results load or no new results appear, and collect location, title, date, price, bedrooms, and absolute listing URL.

Write output/craigslist_listings.csv with exactly these columns: search_location, search_category, search, location, title, date, price, bedrooms, url. Set search to the source query with every double quote replaced by |. Do not write a search_query column. Create output/ when needed, validate missing config/input files clearly, use pathlib paths, and use asyncio.run(main()) as the entry point. Also create a README.md with setup and usage instructions.
```
