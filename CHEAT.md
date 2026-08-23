# `craigslist_bot.py` cheat sheet

This is a project-specific reference for the code in `craigslist_bot.py`. Line numbers refer to the current script. Blank lines only separate sections, so they are omitted below.

## Imports (lines 1–8)

| Lines | Code | What it does here |
| --- | --- | --- |
| 1 | `import asyncio` | Enables asynchronous waits, browser calls, and the `asyncio.run()` program entry point. |
| 2 | `import csv` | Reads the three input CSVs and writes the listings CSV. |
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
| 15–17 | `LOCATIONS_FILE`, `CATEGORIES_FILE`, `QUERIES_FILE` | Define the three separate source CSV paths. |
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

## Single-column CSV reader — `load_values` (lines 49–68)

| Lines | Code | What it does here |
| --- | --- | --- |
| 49–50 | Function and docstring | Defines a reusable reader for a CSV such as `locations.csv`, containing one required column. |
| 51–53 | Path normalization and check | Converts the supplied path and raises a clear error if the input file is missing. |
| 55 | `encoding="utf-8-sig"` | Accepts normal UTF-8 and UTF-8 CSVs saved by Excel that include a byte-order mark. `newline=""` lets Python’s CSV reader handle line endings correctly. |
| 56 | `csv.DictReader(search_file)` | Treats the header row as column names and returns each later row as a dictionary. |
| 57–58 | Header validation | Requires the requested header—`location`, `category`, or `query`—to be present. |
| 60 | `values = []` | Starts the list of accepted values. |
| 61 | `enumerate(..., start=2)` | Iterates data rows, counting from spreadsheet row 2. `row_number` is retained for potential diagnostics. |
| 62 | `row.get(...) or ""` | Gets the target cell, treating missing cells as an empty string, then trims whitespace. |
| 63–64 | Empty value check | Ignores empty rows rather than turning them into invalid searches. |
| 65 | `values.append(value)` | Keeps each non-empty value. |
| 66–67 | Final validation | Stops if the file contained no usable values at all. |
| 68 | `return values` | Returns the cleaned list to the caller. |

## Search combinations — `load_searches` (lines 71–79)

| Lines | Code | What it does here |
| --- | --- | --- |
| 71–72 | Function and docstring | Defines the complete search plan. The multiplication symbol means every possible combination. |
| 73–75 | `load_values(...)` calls | Loads locations, categories, and queries from their separate files with the correct required header. |
| 76–79 | List comprehension with `product(...)` | Converts each Cartesian-product combination into a dictionary like `{"location": "newyork", "category": "jjj", "query": "business partner"}`. For 2 locations, 3 categories, and 4 queries, it creates 24 dictionaries. |

## Craigslist URL builder — `build_search_url` (lines 82–87)

| Lines | Code | What it does here |
| --- | --- | --- |
| 82–83 | Function and docstring | Defines the conversion from one input combination into a Craigslist search URL. |
| 84 | `strip().strip("/")` | Removes accidental spaces and leading/trailing slashes from a location such as `/newyork/`. |
| 85 | `exact_query = ...` | Trims the query, removes existing outer double quotes, then adds exactly one pair of double quotes. This requests an exact phrase search. `chr(34)` is the `"` character. |
| 86 | `urlencode(..., quote_via=quote)` | URL-encodes the category and quoted phrase. `quote_via=quote` encodes spaces as `%20` instead of `+`; quotation marks become `%22`. |
| 87 | F-string URL | Produces URLs like `https://www.craigslist.org/search/area/newyork?cat=jjj&query=%22business%20partner%22`. |

## Browser scraping — `scrape_craigslist_housing` (lines 90–156)

| Lines | Code | What it does here |
| --- | --- | --- |
| 90 | `async def ...` | Defines an asynchronous function that scrapes one generated Craigslist URL. |
| 91 | `async with async_playwright()` | Starts Playwright and guarantees its resources are cleaned up after this scrape. |
| 92 | `p.chromium.launch(...)` | Starts Chromium with the proxy dictionary. `headless=False` shows the browser window; change it to `True` to hide it. |
| 93 | `browser.new_context()` | Creates an isolated browser session for the search. |
| 94 | `context.new_page()` | Opens a new tab. |
| 95 | `page.goto(...)` | Navigates to the search URL, waits until the DOM is available, and fails after 30 seconds. |
| 96 | `asyncio.sleep(3)` | Gives dynamically loaded Craigslist content three additional seconds to appear. |
| 97 | `wait_for_selector(...)` | Requires at least one `div.result-info` listing element before continuing; it waits up to 10 seconds. |
| 99–101 | Scroll state variables | Track the prior listing count, number of scrolls made, and hard maximum of 50 scroll attempts. |
| 102 | `while scroll_attempts < ...` | Starts the controlled infinite-scroll loop. |
| 103 | `query_selector_all(...)` | Finds all currently loaded listing containers and counts them. |
| 104 | `print(...)` | Shows live progress in the terminal. |
| 105–106 | Stop condition | Stops if the requested number has loaded or another scroll produced no new listings. |
| 107 | `previous_count = current_count` | Remembers the count for the next loop comparison. |
| 108 | `page.evaluate(...)` | Runs JavaScript in the page to scroll to its bottom. |
| 109 | `sleep(2)` | Gives the page time to load more results after scrolling. |
| 110 | Counter increment | Records this scroll attempt. |
| 112 | Slice `[:max_listings]` | Re-reads listing elements and limits processing to the requested maximum. |
| 113 | Processing message | Reports how many elements will be extracted. |
| 114–115 | Results list and loop | Creates an output list and handles each listing individually. |
| 116–118 | Location extraction | Uses the first child `div` as a location candidate; if it is absent, stores an empty string. |
| 120 | `title = listing_url = ""` | Initializes both fields before trying multiple selectors. |
| 121–126 | Title and URL selector fallback | Tries several possible Craigslist title link selectors in order. On the first match it reads the title, turns its `href` into an absolute URL with `urljoin`, then stops trying. |
| 128–133 | Date selector fallback | Initializes an empty date, tries several date selectors, and keeps the first value found. |
| 135–140 | Price selector fallback | Uses the same fallback pattern for price. |
| 142–147 | Bedrooms selector fallback | Uses the same fallback pattern for housing/bedroom metadata. |
| 149–151 | `results.append({...})` | Adds one normalized listing dictionary. `strip()` removes unwanted surrounding whitespace from every text field. |
| 152–153 | Broad exception handling | If extraction of a single listing fails, skips that listing and continues scraping the rest. |
| 155 | `await browser.close()` | Closes Chromium after processing the search. |
| 156 | `return results` | Returns that search’s listing dictionaries to `main()`. |

## Output writer — `save_to_csv` (lines 159–167)

| Lines | Code | What it does here |
| --- | --- | --- |
| 159 | Function definition | Writes a list of listing dictionaries to the output CSV. Its default path is `OUTPUT_FILE`. |
| 160–161 | `fields` list | Fixes the CSV column order, including the three search-input columns for traceability. |
| 162 | `OUTPUT_DIR.mkdir(...)` | Creates the `output/` directory if it does not exist. `parents=True` also creates missing parent folders; `exist_ok=True` avoids an error if it already exists. |
| 163 | `open(..., newline="", encoding="utf-8")` | Opens the output file with correct CSV newlines and UTF-8 text encoding. |
| 164 | `csv.DictWriter(...)` | Maps each listing dictionary to the named CSV columns. |
| 165 | `writeheader()` | Writes the first row of column labels. |
| 166 | `writerows(data)` | Writes every listing dictionary as one CSV row. |
| 167 | Save message | Reports the number of saved listings and the file path. |

## Program workflow — `main` and entry point (lines 170–193)

| Lines | Code | What it does here |
| --- | --- | --- |
| 170 | `async def main():` | Defines the program’s main asynchronous workflow. |
| 171 | `get_proxy_config()` | Loads and validates proxy credentials before opening the browser. |
| 172 | `load_searches()` | Loads the three input files and creates all search combinations. |
| 174 | `max_listings = 100` | Sets the maximum listings to collect per individual search URL. |
| 175 | `all_listings = []` | Creates the combined result list for every search. |
| 176 | `for search in searches:` | Runs the browser scraper once per combination. |
| 177 | `build_search_url(**search)` | Unpacks a search dictionary into the `location`, `category`, and `query` function arguments. |
| 178 | Progress message | Prints the exact Craigslist URL being scraped. |
| 179 | `await scrape_...` | Runs one asynchronous scrape and waits for its listings. |
| 180–183 | `listing.update(...)` | Adds the originating location, category, and query to each listing so results can be traced back to their source inputs. |
| 184 | `all_listings.extend(listings)` | Adds the current search’s listings to the complete output list. |
| 186–188 | Empty-result check | Avoids creating an output file when no search returned a listing. |
| 189 | `save_to_csv(all_listings)` | Writes the combined results to `output/craigslist_listings.csv`. |
| 192 | `if __name__ == "__main__":` | Ensures the scraper runs only when this file is executed directly, not when imported by another script. |
| 193 | `asyncio.run(main())` | Starts Python’s asynchronous event loop and runs the program. |

## Files this script expects and creates

```text
Craigslist/
├── craigslist_bot.py
├── .env                         # Private proxy credentials; not committed
├── input/
│   ├── locations.csv             # Header: location
│   ├── categories.csv            # Header: category
│   └── queries.csv               # Header: query
└── output/
    └── craigslist_listings.csv   # Created after a successful scrape
```
