# `craigslist_bot.py` cheat sheet

This is a project-specific reference for the code in `craigslist_bot.py`. Line numbers refer to the current script. Blank lines only separate sections, so they are omitted below.

## Imports (lines 1–8)

| Lines | Code | What it does here |
| --- | --- | --- |
| 1 | `import asyncio` | Enables asynchronous waits, browser calls, and the `asyncio.run()` program entry point. |
| 2 | `import csv` | Writes the listings output CSV. The three search inputs are plain-text files. |
| 3 | `import os` | Accesses environment variables loaded from `.env`. |
| 4 | `from itertools import product` | Produces every location × category × query search combination. |
| 5 | `from pathlib import Path` | Safely builds file-system paths relative to this script. |
| 6 | `quote`, `urlencode`, `urljoin` | URL-encodes search parameters and converts Craigslist listing links to complete URLs. |
| 8 | `async_playwright` | Starts Playwright’s asynchronous Chromium automation API. |

## File paths (lines 11–18)

| Lines | Code | What it does here |
| --- | --- | --- |
| 11 | `BASE_DIR = Path(__file__).resolve().parent` | Finds the directory containing this Python file, regardless of the terminal’s current directory. |
| 12 | `ENV_FILE` | Points to the private proxy configuration file: `.env`. |
| 13–14 | `INPUT_DIR`, `OUTPUT_DIR` | Define the `input/` and `output/` folders beside the script. |
| 15–17 | `LOCATIONS_FILE`, `CATEGORIES_FILE`, `QUERIES_FILE` | Define the three separate plain-text source paths: `locations.txt`, `categories.txt`, and `queries.txt`. |
| 18 | `OUTPUT_FILE` | Defines the generated results file: `output/craigslist_listings.csv`. |

## `.env` loader — `load_dotenv` (lines 21–33)

| Lines | Code | What it does here |
| --- | --- | --- |
| 21 | `def load_dotenv(path):` | Defines the small built-in `.env` reader; no `python-dotenv` package is needed. |
| 22 | Docstring | States that the function expects simple `KEY=VALUE` lines. |
| 23 | `path = Path(path)` | Accepts either a string or `Path` object, then standardizes it as a `Path`. |
| 24–25 | `if not path.exists()` / `FileNotFoundError` | Stops early with the exact missing configuration path. |
| 27 | `with path.open(...) as env_file:` | Opens `.env` as UTF-8 and automatically closes it when finished. |
| 28–29 | `for raw_line...` / `strip()` | Reads each line and removes surrounding whitespace. |
| 30–31 | Skip condition | Ignores blank lines, comment lines beginning with `#`, and malformed lines without `=`. |
| 32 | `line.split("=", 1)` | Separates the variable name from its value only at the first equals sign; values may therefore contain `=`. |
| 33 | `os.environ.setdefault(...)` | Saves the value as an environment variable only if the same variable was not already supplied by the operating system. It removes surrounding single or double quotes from the value. |

## Proxy settings — `get_proxy_config` (lines 36–46)

| Lines | Code | What it does here |
| --- | --- | --- |
| 36 | `def get_proxy_config():` | Builds the Playwright proxy configuration dictionary. |
| 37 | `load_dotenv(ENV_FILE)` | Loads proxy settings from the project’s `.env`. |
| 38 | `keys = (...)` | Lists the three required settings: server, username, and password. |
| 39 | List comprehension | Identifies any required setting that is absent or empty. |
| 40–41 | Validation error | Prevents the browser from starting with incomplete proxy credentials. |
| 42–46 | `return {...}` | Returns the exact `server`, `username`, and `password` dictionary expected by Playwright. |

## Plain-text input reader — `load_values` (lines 49–59)

| Lines | Code | What it does here |
| --- | --- | --- |
| 49–50 | Function and docstring | Defines a reusable reader for a plain-text input file such as `locations.txt`, containing one value per non-empty line. |
| 51–53 | Path normalization and check | Converts the supplied path and raises a clear error if the input file is missing. |
| 55 | `encoding="utf-8-sig"` | Opens the file as UTF-8 and tolerates a byte-order mark from an editor such as Excel. |
| 56 | List comprehension | Reads each line, removes surrounding whitespace, and retains only non-empty lines. There is no header row or CSV parsing. |
| 57–58 | Final validation | Stops if the text file contains no usable values. |
| 59 | `return values` | Returns the cleaned list to the caller. |

## Search combinations — `load_searches` (lines 62–70)

| Lines | Code | What it does here |
| --- | --- | --- |
| 62–63 | Function and docstring | Defines the complete search plan. The multiplication symbol means every possible combination. |
| 64–66 | `load_values(...)` calls | Loads locations, categories, and queries from their separate `.txt` files. |
| 67–70 | List comprehension with `product(...)` | Converts each Cartesian-product combination into a dictionary like `{"location": "newyork", "category": "jjj", "query": "business partner"}`. For 2 locations, 3 categories, and 4 queries, it creates 24 dictionaries. |

## Craigslist URL builder — `build_search_url` (lines 73–78)

| Lines | Code | What it does here |
| --- | --- | --- |
| 73–74 | Function and docstring | Defines the conversion from one input combination into a Craigslist search URL. |
| 75 | `strip().strip("/")` | Removes accidental spaces and leading/trailing slashes from a location such as `/newyork/`. |
| 76 | `exact_query = ...` | Trims the query, removes existing outer double quotes, then adds exactly one pair of double quotes. This requests an exact phrase search. `chr(34)` is the `"` character. |
| 77 | `urlencode(..., quote_via=quote)` | URL-encodes the category and quoted phrase. `quote_via=quote` encodes spaces as `%20` instead of `+`; quotation marks become `%22`. |
| 78 | F-string URL | Produces URLs like `https://www.craigslist.org/search/area/newyork?cat=jjj&query=%22business%20partner%22`. |

## Browser scraping — `scrape_craigslist_housing` (lines 81–147)

| Lines | Code | What it does here |
| --- | --- | --- |
| 81 | `async def ...` | Defines an asynchronous function that scrapes one generated Craigslist URL. |
| 82 | `async with async_playwright()` | Starts Playwright and guarantees its resources are cleaned up after this scrape. |
| 83 | `p.chromium.launch(...)` | Starts Chromium with the proxy dictionary. `headless=False` shows the browser window; change it to `True` to hide it. |
| 84 | `browser.new_context()` | Creates an isolated browser session for the search. |
| 85 | `context.new_page()` | Opens a new tab. |
| 86 | `page.goto(...)` | Navigates to the search URL, waits until the DOM is available, and fails after 30 seconds. |
| 87 | `asyncio.sleep(3)` | Gives dynamically loaded Craigslist content three additional seconds to appear. |
| 88 | `wait_for_selector(...)` | Requires at least one `div.result-info` listing element before continuing; it waits up to 10 seconds. |
| 90–92 | Scroll state variables | Track the prior listing count, number of scrolls made, and hard maximum of 50 scroll attempts. |
| 93 | `while scroll_attempts < ...` | Starts the controlled infinite-scroll loop. |
| 94 | `query_selector_all(...)` | Finds all currently loaded listing containers and counts them. |
| 95 | `print(...)` | Shows live progress in the terminal. |
| 96–97 | Stop condition | Stops if the requested number has loaded or another scroll produced no new listings. |
| 98 | `previous_count = current_count` | Remembers the count for the next loop comparison. |
| 99 | `page.evaluate(...)` | Runs JavaScript in the page to scroll to its bottom. |
| 100 | `sleep(2)` | Gives the page time to load more results after scrolling. |
| 101 | Counter increment | Records this scroll attempt. |
| 103 | Slice `[:max_listings]` | Re-reads listing elements and limits processing to the requested maximum. |
| 104 | Processing message | Reports how many elements will be extracted. |
| 105–106 | Results list and loop | Creates an output list and handles each listing individually. |
| 107–109 | Location extraction | Uses the first child `div` as a location candidate; if it is absent, stores an empty string. |
| 111 | `title = listing_url = ""` | Initializes both fields before trying multiple selectors. |
| 112–117 | Title and URL selector fallback | Tries several possible Craigslist title link selectors in order. On the first match it reads the title, turns its `href` into an absolute URL with `urljoin`, then stops trying. |
| 119–124 | Date selector fallback | Initializes an empty date, tries several date selectors, and keeps the first value found. |
| 126–131 | Price selector fallback | Uses the same fallback pattern for price. |
| 133–138 | Bedrooms selector fallback | Uses the same fallback pattern for housing/bedroom metadata. |
| 140–142 | `results.append({...})` | Adds one normalized listing dictionary. `strip()` removes unwanted surrounding whitespace from every text field. |
| 143–144 | Broad exception handling | If extraction of a single listing fails, skips that listing and continues scraping the rest. |
| 146 | `await browser.close()` | Closes Chromium after processing the search. |
| 147 | `return results` | Returns that search’s listing dictionaries to `main()`. |

## Output writer — `save_to_csv` (lines 150–158)

| Lines | Code | What it does here |
| --- | --- | --- |
| 150 | Function definition | Writes a list of listing dictionaries to the output CSV. Its default path is `OUTPUT_FILE`. |
| 151–152 | `fields` list | Fixes the CSV column order, including the source location/category columns and `search`, which is the query with quotation marks replaced by pipes. |
| 153 | `OUTPUT_DIR.mkdir(...)` | Creates the `output/` directory if it does not exist. `parents=True` also creates missing parent folders; `exist_ok=True` avoids an error if it already exists. |
| 154 | `open(..., newline="", encoding="utf-8")` | Opens the output file with correct CSV newlines and UTF-8 text encoding. |
| 155 | `csv.DictWriter(...)` | Maps each listing dictionary to the named CSV columns. |
| 156 | `writeheader()` | Writes the first row of column labels. |
| 157 | `writerows(data)` | Writes every listing dictionary as one CSV row. |
| 158 | Save message | Reports the number of saved listings and the file path. |

## Program workflow — `main` and entry point (lines 161–184)

| Lines | Code | What it does here |
| --- | --- | --- |
| 161 | `async def main():` | Defines the program’s main asynchronous workflow. |
| 162 | `get_proxy_config()` | Loads and validates proxy credentials before opening the browser. |
| 163 | `load_searches()` | Loads the three input text files and creates all search combinations. |
| 165 | `max_listings = 100` | Sets the maximum listings to collect per individual search URL. |
| 166 | `all_listings = []` | Creates the combined result list for every search. |
| 167 | `for search in searches:` | Runs the browser scraper once per combination. |
| 168 | `build_search_url(**search)` | Unpacks a search dictionary into the `location`, `category`, and `query` function arguments. |
| 169 | Progress message | Prints the exact Craigslist URL being scraped. |
| 170 | `await scrape_...` | Runs one asynchronous scrape and waits for its listings. |
| 171–174 | `listing.update(...)` | Adds the originating location and category to each listing. It also creates `search` by replacing every `"` in the query with `|`, so a query such as `"business partner" "for"` becomes `|business partner| |for|`. |
| 175 | `all_listings.extend(listings)` | Adds the current search’s listings to the complete output list. |
| 177–179 | Empty-result check | Avoids creating an output file when no search returned a listing. |
| 180 | `save_to_csv(all_listings)` | Writes the combined results to `output/craigslist_listings.csv`. |
| 183 | `if __name__ == "__main__":` | Ensures the scraper runs only when this file is executed directly, not when imported by another script. |
| 184 | `asyncio.run(main())` | Starts Python’s asynchronous event loop and runs the program. |

## Files this script expects and creates

```text
Craigslist/
├── craigslist_bot.py
├── .env                         # Private proxy credentials; not committed
├── input/
│   ├── locations.txt             # One location per non-empty line
│   ├── categories.txt            # One category per non-empty line
│   └── queries.txt               # One query per non-empty line
└── output/
    └── craigslist_listings.csv   # Created after a successful scrape
```
