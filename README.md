# Craigslist Search Scraper

`craigslist_bot.py` runs Craigslist searches through an authenticated proxy, collects the loaded listings, and writes them to a CSV file. Searches are controlled with three small CSV files, so you can change locations, categories, and phrases without editing Python code.

## What the script does

For every combination of a location, category, and query from the input files, the script:

1. Builds a Craigslist search URL.
2. Opens it in Chromium through the configured proxy.
3. Scrolls until it has loaded the requested number of listings (up to 100 per search).
4. Extracts each listing's location, title, date, price, housing details, and URL.
5. Saves all results to `output/craigslist_listings.csv`.

The output also includes the input location, category, and query that produced every row.

## Requirements

- Python 3.9 or later
- Playwright for Python
- A Chromium browser installed for Playwright
- A working proxy account

Install the Python dependency and browser from the project directory:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

## Proxy configuration

Create a `.env` file beside `craigslist_bot.py`. This file is intentionally ignored by Git because it contains secrets.

```dotenv
PROXY_SERVER=http://gate.decodo.com:7000
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password
```

The script reads these values when it starts. It stops with a clear error if the file or a required value is missing.

## Search inputs

Put the three input CSV files in the `input/` folder. Each file needs the exact header shown below and one value per subsequent row.

### `input/locations.csv`

```csv
location
newyork
```

Use Craigslist area names such as `newyork`.

### `input/categories.csv`

```csv
category
jjj
ggg
```

Use Craigslist category codes such as `jjj`.

### `input/queries.csv`

```csv
query
business partner wanted
```

Queries are always searched as exact quoted phrases. For example, `business partner wanted` produces:

```text
https://www.craigslist.org/search/area/newyork?cat=jjj&query=%22business%20partner%20wanted%22
```

Quotation marks already included in a query are not doubled.

### How combinations work

The script runs the full location × category × query combination. For example, 2 locations, 3 categories, and 4 queries create 24 searches.

## Run the scraper

From the project directory:

```bash
python3 craigslist_bot.py
```

The script currently opens Chromium visibly (`headless=False`), which can be useful for observing the search. Change that value to `True` in `craigslist_bot.py` if you want it to run without a browser window.

## Output

When listings are found, the script creates `output/craigslist_listings.csv` with these columns:

| Column | Description |
| --- | --- |
| `search_location` | Location value from `locations.csv` |
| `search_category` | Category value from `categories.csv` |
| `search_query` | Query value from `queries.csv` |
| `location` | Listing location shown by Craigslist |
| `title` | Listing title |
| `date` | Posted date text |
| `price` | Listing price, when available |
| `bedrooms` | Housing metadata, when available |
| `url` | Link to the listing |

Generated output files are not tracked by Git.

## Common issues

- **`ModuleNotFoundError: playwright`**: run `python3 -m pip install playwright`.
- **Browser executable missing**: run `python3 -m playwright install chromium`.
- **Missing `.env` value**: check all three proxy settings in `.env`.
- **Missing input CSV or column**: confirm the filenames, folder, and header names exactly match the examples above.
- **No listings found**: verify the proxy credentials and test the generated Craigslist URL in a browser.

## Source

The original scraping approach was adapted from [Decodo's Craigslist scraping guide](https://decodo.com/blog/scrape-craigslist), then configured and documented for this project.
