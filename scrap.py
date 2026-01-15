import json
import argparse
import sys
import os
import re
from pathlib import Path
from fiverr_api import session

# Try to load from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Or provide API key with --key argument\n")

def sanitize_filename(filename):
    """Remove/replace invalid characters for Windows filenames."""
    # Replace invalid characters with underscore
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    return sanitized[:50]  # Limit to 50 chars

def scrape_fiverr(url, api_key=None, output_dir="output", formats=None):
    """
    Scrape Fiverr URL and save response to files.
    
    Args:
        url (str): Fiverr URL to scrape
        api_key (str): ScraperAPI key (optional, can load from .env)
        output_dir (str): Directory to save files
        formats (list): List of formats to save ('json', 'html', 'both')
    
    Returns:
        dict: JSON data from the page
    """
    if formats is None:
        formats = ['both']
    
    # Load API key from .env if not provided
    if not api_key:
        api_key = os.getenv('SCRAPER_API_KEY')
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # Set API key
        if api_key:
            session.set_scraper_api_key(api_key)
        else:
            print("⚠️  Warning: No API key found (not in --key arg or .env file)")
            print("   Create .env file with: SCRAPER_API_KEY=your_key_here")
            print("   Or use: python scrap.py '<URL>' --key YOUR_KEY\n")
        
        print(f"🔄 Scraping: {url}")
        response = session.get(url)
        
        # Extract data
        json_data = response.props_json()
        html_content = response.text
        
        # Generate filename from URL - extract last meaningful part
        filename = url.split('/')[-1] if '/' in url else 'fiverr_data'
        if '?' in filename:
            filename = filename.split('?')[0]
        if not filename or filename.startswith('http'):
            filename = 'fiverr_data'
        
        # Sanitize filename for Windows
        filename = sanitize_filename(filename)
        
        # Save JSON
        if 'json' in formats or 'both' in formats:
            json_file = Path(output_dir) / f"{filename}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON saved: {json_file}")
        
        # Save HTML
        if 'html' in formats or 'both' in formats:
            html_file = Path(output_dir) / f"{filename}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML saved: {html_file}")
        
        print(f"📊 Data extracted: {len(json_data)} keys in JSON")
        return json_data
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Fiverr Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python scrap.py "https://www.fiverr.com/search/gigs?query=python"
  python scrap.py "https://www.fiverr.com/search/gigs?query=design" --format json
  python scrap.py "https://www.fiverr.com/username/gig" -o results/ --format both
  
Setup .env file:
  Create a .env file with: SCRAPER_API_KEY=your_actual_key_here
  Then you won't need to pass --key every time
        '''
    )
    
    parser.add_argument('url', nargs='?', help='Fiverr URL to scrape')
    parser.add_argument('--key', '-k', help='ScraperAPI key (optional, reads from .env if not provided)')
    parser.add_argument('--output', '-o', default='output', help='Output directory (default: output)')
    parser.add_argument('--format', '-f', choices=['json', 'html', 'both'], default='both',
                        help='Output format (default: both)')
    
    args = parser.parse_args()
    
    # If no URL provided, show help
    if not args.url:
        print("📝 Usage: python scrap.py '<URL>' [OPTIONS]")
        print("\n📋 Example URLs:")
        print("  - Search: https://www.fiverr.com/search/gigs?query=python")
        print("  - Seller: https://www.fiverr.com/john_smith")
        print("\n🔑 Setup API Key:")
        print("  Option 1: Create .env file with SCRAPER_API_KEY=your_key")
        print("  Option 2: Use --key YOUR_KEY argument")
        print("\n  Get free key: https://www.scraperapi.com/?fp_ref=enable-fiverr-api")
        parser.print_help()
        sys.exit(0)
    
    scrape_fiverr(args.url, args.key, args.output, [args.format])

if __name__ == '__main__':
    main()

def main():
    parser = argparse.ArgumentParser(
        description='Fiverr Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python scrap.py "https://www.fiverr.com/search/gigs?query=python"
  python scrap.py "https://www.fiverr.com/search/gigs?query=design" --format json
  python scrap.py "https://www.fiverr.com/username/gig" -o results/ --format both
  
Setup .env file:
  Create a .env file with: SCRAPER_API_KEY=your_actual_key_here
  Then you won't need to pass --key every time
        '''
    )
    
    parser.add_argument('url', nargs='?', help='Fiverr URL to scrape')
    parser.add_argument('--key', '-k', help='ScraperAPI key (optional, reads from .env if not provided)')
    parser.add_argument('--output', '-o', default='output', help='Output directory (default: output)')
    parser.add_argument('--format', '-f', choices=['json', 'html', 'both'], default='both',
                        help='Output format (default: both)')
    
    args = parser.parse_args()
    
    # If no URL provided, show help
    if not args.url:
        print("📝 Usage: python scrap.py '<URL>' [OPTIONS]")
        print("\n📋 Example URLs:")
        print("  - Search: https://www.fiverr.com/search/gigs?query=python")
        print("  - Seller: https://www.fiverr.com/john_smith")
        print("\n🔑 Setup API Key:")
        print("  Option 1: Create .env file with SCRAPER_API_KEY=your_key")
        print("  Option 2: Use --key YOUR_KEY argument")
        print("\n  Get free key: https://www.scraperapi.com/?fp_ref=enable-fiverr-api")
        parser.print_help()
        sys.exit(0)
    
    scrape_fiverr(args.url, args.key, args.output, [args.format])

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()