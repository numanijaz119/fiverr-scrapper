# Fiverr Scraping API

A Python-based web scraping tool for collecting and analyzing Fiverr gig data. This project scrapes Fiverr search results and individual gig information, storing the data in JSON format for further analysis.

## 🎯 Features

- **Web Scraping**: Scrape Fiverr gig listings from search results
- **Data Extraction**: Extract comprehensive gig information including:
  - Pricing details (starting price, packages)
  - Seller information and ratings
  - Gig descriptions and details
  - Reviews and statistics
- **Data Analysis**: Built-in analysis tools for:
  - Pricing statistics (average, min, max, median)
  - Seller ratings analysis
  - Review sentiment analysis
  - Category breakdowns
- **JSON Export**: Store scraped data in structured JSON format
- **HTML Export**: Generate HTML reports from scraped data
- **Filename Sanitization**: Automatic Windows-compatible filename generation

## 📋 Project Structure

├── Fiverr_search-Scrapper.py # Main scraper script
├── Analyze_gig.py # Legacy analysis utilities
├── analyze_keyword.py # Keyword market research & consolidation
├── requirements.txt # Python dependencies
├── fiverr/ # Custom Fiverr API module
│ ├── **init**.py # Session export
│ └── utils/
│ ├── **init**.py # Utilities package
│ ├── req.py # Request handling & session management
│ └── scrape_utils.py # HTML parsing utilities
├── gigs_data/ # Scraped gig data (JSON files by keyword)
├── output/ # Generated reports
│ ├── gigs.html # HTML report
│ └── gigs.json # Aggregated JSON data
├── .env # Environment variables
├── .git/ # Git repository
└── env/ # Python virtual environment

## 🛠️ Installation

### Module Architecture

The `fiverr/` package provides a custom API layer for scraping Fiverr:

- **`fiverr/__init__.py`** - Exports the `session` object for use in scripts
- **`fiverr/utils/req.py`** - Custom HTTP Session class that:
  - Handles Fiverr-specific requests
  - Validates URLs to ensure they're Fiverr domains
  - Integrates with ScraperAPI for reliable scraping
  - Returns custom Response objects with HTML parsing
- **`fiverr/utils/scrape_utils.py`** - Helper function to extract JSON data from HTML using BeautifulSoup

### Installation Steps

1. **Clone or extract the project**

   ```bash
   cd fiverr-scraping-api
   ```

2. **Create and activate virtual environment** (optional but recommended)

   ```bash
   python -m venv env
   # On Windows:
   env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## 📦 Dependencies

- **beautifulsoup4**: HTML parsing and web scraping
- **requests**: HTTP requests for fetching web pages
- **html5lib**: HTML5 parser
- **urllib3**: HTTP client library
- **charset-normalizer**: Character encoding detection
- **certifi**: SSL certificates

## 🚀 Usage

### Basic Scraping

Run the main scraper to collect Fiverr gig data:

```bash
python Fiverr_search-Scrapper.py --keyword "web development" --pages 5
```

**Options:**

- `--keyword`: Search keyword (e.g., "web development", "logo design")
- `--pages`: Number of pages to scrape (default: 1)
- `--output`: Output directory for JSON files (default: `gigs_data/`)

### Data Analysis

Analyze the scraped gig data and generate market research insights:

```bash
# Analyze a specific keyword directory
python analyze_keyword.py "gigs_data/custom website development"

# Analyze multiple keywords
python analyze_keyword.py "gigs_data/keyword1" "gigs_data/keyword2"

# Specify custom output directory
python analyze_keyword.py "gigs_data/logo design" --output my_analysis
```

This generates a consolidated JSON file with:

- **Overall Statistics**: Total gigs, pro seller percentages
- **Pricing Analysis**: Average, min, max, median prices
- **Rating Analysis**: Average seller ratings and customer satisfaction
- **Delivery Time Analysis**: Standard delivery times and variations
- **Order Metrics**: Average orders in queue, market demand indicators
- **Popular Tags**: Top 20 most common tags/skills
- **Individual Gig Data**: Consolidated data for each gig with all metrics

**Output**: Creates `{keyword_name}_analysis.json` with complete market research data

### Legacy Analysis

The original `Analyze_gig.py` script provides simpler analysis:

```bash
python Analyze_gig.py
```

### Sample Data

Scraped gigs are organized in directories by keyword:

```
gigs_data/
└── custom website development/
    ├── gig_103098199_shahab01.json
    ├── gig_114330473_seanv602.json
    └── ...
```

Each JSON file contains complete gig information with:

- Gig metadata (title, ID, URL)
- Seller details and ratings
- Pricing packages and features
- Ratings and customer reviews
- Description and categories
- Gallery/media content

### Analysis Output

The `analyze_keyword.py` script creates consolidated analysis files:

```
keyword_analysis/
└── custom_website_development_analysis.json
```

The analysis JSON includes:

- Aggregated market statistics
- Per-gig consolidated metrics
- Pricing distributions
- Seller quality indicators
- Popular skills/tags

## 📊 Data Schema

### Gig Data Structure

```json
{
  "gig_id": 12345678,
  "title": "I will create a professional website",
  "seller": {
    "username": "seller_name",
    "rating": 4.8,
    "reviews_count": 150
  },
  "pricing": {
    "starting_price": 99.0,
    "packages": [
      {
        "name": "Basic",
        "price": 99.0,
        "description": "..."
      }
    ]
  },
  "description": {
    "content": "Full gig description..."
  },
  "category": "Web Development",
  "url": "https://www.fiverr.com/gigs/..."
}
```

## 🔧 Configuration

Set environment variables or configuration options:

```bash
# Create .env file (optional)
API_TIMEOUT=30
OUTPUT_DIR=./gigs_data
```

## 📝 Examples

### Example 1: Complete Workflow - Web Development Gigs

```bash
# 1. Scrape gigs for "web development"
python Fiverr_search-Scrapper.py --keyword "web development" --pages 5

# 2. Analyze the scraped data
python analyze_keyword.py "gigs_data/web development" --output analysis_results

# Results in: analysis_results/web_development_analysis.json
```

### Example 2: Compare Multiple Markets

```bash
# Scrape multiple keywords
python Fiverr_search-Scrapper.py --keyword "logo design" --pages 3
python Fiverr_search-Scrapper.py --keyword "ui design" --pages 3

# Analyze both markets
python analyze_keyword.py "gigs_data/logo design" "gigs_data/ui design" --output market_analysis

# Results in:
# - market_analysis/logo_design_analysis.json
# - market_analysis/ui_design_analysis.json
```

### Example 3: Quick Market Research

```bash
python Fiverr_search-Scrapper.py --keyword "python automation" --pages 2 --delay 1
python analyze_keyword.py "gigs_data/python automation"
```

## ⚠️ Important Notes

- **Terms of Service**: Ensure compliance with Fiverr's Terms of Service and robots.txt
- **Rate Limiting**: The scraper includes delays to avoid overwhelming servers
- **Data Accuracy**: Scraped data may vary based on Fiverr's page structure changes
- **Windows Compatibility**: Filenames are automatically sanitized for Windows systems

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**

   - Check internet connection
   - Verify Fiverr website is accessible
   - Check if IP is rate-limited

2. **JSON Parse Errors**

   - Fiverr's page structure may have changed
   - Clear `gigs_data/` and rescrape

3. **Encoding Issues**

   - Ensure UTF-8 encoding is used
   - Update beautifulsoup4 and html5lib

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Feel free to submit issues or improvements.

## 📞 Support

For issues or questions, refer to the error messages in the console output. The scraper includes detailed logging for debugging.

---

**Last Updated**: January 2026
