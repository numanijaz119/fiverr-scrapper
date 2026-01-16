import json
import argparse
import sys
import os
import re
import time
from pathlib import Path
from urllib.parse import quote_plus
from fiverr import session

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def sanitize_filename(filename):
    """Remove/replace invalid characters for Windows filenames."""
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    sanitized = sanitized.strip('. ')
    return sanitized[:100]


def extract_gig_urls_from_search(search_data):
    """Extract all gig URLs from search results JSON data."""
    gig_infos = []
    
    try:
        if 'listings' not in search_data or not search_data['listings']:
            print("⚠️  'listings' key not found or empty")
            return []
        
        listings = search_data['listings'][0]
        gigs = listings.get('gigs', [])
        
        if not gigs:
            print("⚠️  No gigs found in listings[0].gigs")
            return []
        
        print(f"✅ Found {len(gigs)} gig entries")
        
        for gig in gigs:
            gig_url = gig.get('gig_url', '')
            
            if gig_url:
                full_url = f"https://www.fiverr.com{gig_url}"
                
                gig_info = {
                    'url': full_url,
                    'title': gig.get('title', 'Unknown'),
                    'seller_name': gig.get('seller_name', ''),
                    'seller_url': gig.get('seller_url', ''),
                    'gig_id': gig.get('gig_id', ''),
                    'price': gig.get('price_i', 0),
                    'seller_level': gig.get('seller_level', ''),
                    'seller_rating': gig.get('seller_rating', {}).get('score', 0),
                    'seller_country': gig.get('seller_country', '')
                }
                
                gig_infos.append(gig_info)
        
        print(f"✅ Extracted {len(gig_infos)} gig URLs")
        
    except Exception as e:
        print(f"❌ Error extracting gig URLs: {e}")
        import traceback
        traceback.print_exc()
    
    return gig_infos


def extract_gig_details(gig_data):
    """
    Extract detailed information from a gig's JSON data.
    FIXED with correct paths from actual Fiverr response.
    """
    details = {
        'title': None,
        'description': None,
        'short_description': None,
        'seller_info': {},
        'packages': [],
        'pricing': {},
        'gig_info': {},
        'reviews': {},
        'orders_in_queue': None,
        'gallery': [],
        'tags': [],
        'metadata': [],
        'faqs': [],
        'raw_url': None
    }
    
    try:
        # === GENERAL INFO ===
        general = gig_data.get('general', {})
        details['gig_info']['gig_id'] = general.get('gigId', '')
        details['gig_info']['category_name'] = general.get('categoryName', '')
        details['gig_info']['sub_category_name'] = general.get('subCategoryName', '')
        details['gig_info']['is_pro'] = general.get('isPro', False)
        details['gig_info']['is_on_vacation'] = general.get('isOnVacation', False)
        
        # === OVERVIEW SECTION ===
        overview = gig_data.get('overview', {})
        gig_overview = overview.get('gig', {})
        
        details['title'] = gig_overview.get('title', '')
        details['gig_info']['rating'] = gig_overview.get('rating', 0)
        details['gig_info']['ratings_count'] = gig_overview.get('ratingsCount', 0)
        details['orders_in_queue'] = gig_overview.get('ordersInQueue', 0)
        details['gig_info']['is_restricted'] = gig_overview.get('isRestrictedByRegion', False)
        
        # Categories from overview
        categories = overview.get('categories', {})
        if categories:
            details['gig_info']['category'] = categories.get('category', {})
            details['gig_info']['sub_category'] = categories.get('subCategory', {})
            details['gig_info']['nested_sub_category'] = categories.get('nestedSubCategory', {})
        
        # Seller overview info
        seller_overview = overview.get('seller', {})
        if seller_overview:
            details['seller_info']['seller_id'] = seller_overview.get('id', '')
            details['seller_info']['username'] = seller_overview.get('username', '')
            details['seller_info']['is_pro'] = seller_overview.get('isPro', False)
            details['seller_info']['country_code'] = seller_overview.get('countryCode', '')
            details['seller_info']['profile_photo'] = seller_overview.get('profilePhoto', '')
            details['seller_info']['proficient_languages'] = seller_overview.get('proficientLanguages', [])
            details['seller_info']['achievement'] = seller_overview.get('achievement', 0)
        
        # === SELLER CARD (Additional seller info) ===
        seller_card = gig_data.get('sellerCard', {})
        if seller_card:
            details['seller_info'].update({
                'one_liner': seller_card.get('oneLiner', ''),
                'rating': seller_card.get('rating', 0),
                'ratings_count': seller_card.get('ratingsCount', 0),
                'member_since': seller_card.get('memberSince', ''),
                'response_time': seller_card.get('responseTime', 0),
                'recent_delivery': seller_card.get('recentDelivery', ''),
                'description': seller_card.get('description', ''),
                'pro_sub_categories': seller_card.get('proSubCategories', [])
            })
        
        # === DESCRIPTION (FIXED PATH) ===
        # CRITICAL FIX: Description is at description.content, NOT in aboutGig.sections
        description_obj = gig_data.get('description', {})
        if description_obj:
            # Full description (HTML content)
            details['description'] = description_obj.get('content', '')
            
            # Metadata attributes (can extract short description from here if needed)
            metadata_attrs = description_obj.get('metadataAttributes', [])
            details['metadata'] = metadata_attrs
            
            print("  ✅ Description extracted successfully")
        
        # === FAQS ===
        faqs_data = gig_data.get('faqs', {})
        faqs_list = faqs_data.get('list', [])
        if faqs_list:
            details['faqs'] = [
                {
                    'question': faq.get('question', ''),
                    'answer': faq.get('answer', '')
                }
                for faq in faqs_list
            ]
            print(f"  ✅ Found {len(details['faqs'])} FAQs")
        
        # === PACKAGES (FIXED PATH) ===
        # CRITICAL FIX: Packages are at packages.packageList[], NOT packages.packages[]
        packages_data = gig_data.get('packages', {})
        packages_list = packages_data.get('packageList', [])  # FIXED: was 'packages', now 'packageList'
        
        if packages_list:
            print(f"  ✅ Found {len(packages_list)} packages")
            
            package_names = ['Basic', 'Standard', 'Premium']
            for idx, package in enumerate(packages_list):
                revisions_data = package.get('revisions', {})
                extra_fast = package.get('extraFast', {})
                
                package_info = {
                    'id': package.get('id', idx + 1),
                    'name': package_names[idx] if idx < len(package_names) else f'Package {idx+1}',
                    'title': package.get('title', ''),
                    'description': package.get('description', ''),
                    'price': package.get('price', 0) / 100,  # Convert from cents to dollars
                    'delivery_time_days': package.get('duration', 0) / 24,  # Convert hours to days
                    'revisions': revisions_data.get('value', 0),
                    'revisions_unlimited': revisions_data.get('value', 0) == -1,
                    'extra_fast_delivery': {
                        'available': extra_fast.get('included', False) if extra_fast else False,
                        'duration_hours': extra_fast.get('duration', 0) if extra_fast else 0,
                        'price': extra_fast.get('price', 0) / 100 if extra_fast else 0
                    },
                    'features': []
                }
                
                # Extract features
                features = package.get('features', [])
                for feature in features:
                    package_info['features'].append({
                        'id': feature.get('id', ''),
                        'name': feature.get('name', ''),
                        'label': feature.get('label', ''),
                        'value': feature.get('value', 0),
                        'included': feature.get('included', False),
                        'type': feature.get('type', ''),
                        'price': feature.get('price', 0) / 100 if feature.get('price', 0) > 0 else 0
                    })
                
                details['packages'].append(package_info)
        else:
            print("  ⚠️  No packages found")
        
        # === PRICING SUMMARY ===
        if details['packages']:
            prices = [p['price'] for p in details['packages'] if p['price'] > 0]
            if prices:
                details['pricing'] = {
                    'starting_price': min(prices),
                    'highest_price': max(prices),
                    'currency': gig_data.get('currency', {}).get('name', 'USD'),
                    'has_packages': True
                }
        
        # === REVIEWS ===
        reviews_data = gig_data.get('reviews', {})
        if reviews_data:
            details['reviews'] = {
                'rating': reviews_data.get('rating', 0),
                'reviews_count': reviews_data.get('reviews_count', 0),
                'breakdown': reviews_data.get('breakdown', []),
                'star_summary': reviews_data.get('star_summary', {}),
                'recent_reviews': []
            }
            
            reviews_list = reviews_data.get('reviews', [])[:5]
            for review in reviews_list:
                seller_response = review.get('seller_response', {})
                details['reviews']['recent_reviews'].append({
                    'id': review.get('id', ''),
                    'comment': review.get('comment', ''),
                    'rating': review.get('value', 0),
                    'username': review.get('username', ''),
                    'country': review.get('reviewer_country', ''),
                    'country_code': review.get('reviewer_country_code', ''),
                    'created_at': review.get('created_at', ''),
                    'seller_response': {
                        'comment': seller_response.get('comment', ''),
                        'created_at': seller_response.get('created_at', '')
                    } if seller_response else None
                })
        
        # === GALLERY ===
        gallery_data = gig_data.get('gallery', {})
        slides = gallery_data.get('slides', [])
        
        for slide in slides:
            slide_data = slide.get('slide', {})
            media = slide_data.get('media', {})
            details['gallery'].append({
                'name': slide_data.get('name', ''),
                'src': slide_data.get('src', ''),
                'thumbnail': slide_data.get('thumbnail', ''),
                'is_video': slide_data.get('typeVideo', False),
                'media_small': media.get('small', ''),
                'media_medium': media.get('medium', ''),
                'media_original': media.get('original', '')
            })
        
        # === TAGS ===
        tags_data = gig_data.get('tags', {})
        tags_list = tags_data.get('tagsGigList', [])
        
        for tag in tags_list:
            details['tags'].append({
                'name': tag.get('name', ''),
                'slug': tag.get('slug', '')
            })
        
        # === TOP NAV INFO ===
        top_nav = gig_data.get('topNav', {})
        if top_nav:
            details['gig_info']['collected_count'] = top_nav.get('gigCollectedCount', 0)
        
        # === CURRENCY ===
        currency_data = gig_data.get('currency', {})
        if currency_data:
            details['pricing']['currency_symbol'] = currency_data.get('symbol', '$')
            details['pricing']['currency_template'] = currency_data.get('template', '${amount}')
        
        # Final status report
        print(f"  📊 Extraction Summary:")
        print(f"     - Title: {'✅' if details['title'] else '❌'}")
        print(f"     - Description: {'✅' if details['description'] else '❌'}")
        print(f"     - Packages: {'✅ (' + str(len(details['packages'])) + ')' if details['packages'] else '❌'}")
        print(f"     - Orders in Queue: {'✅ (' + str(details['orders_in_queue']) + ')' if details['orders_in_queue'] is not None else '❌'}")
        print(f"     - Reviews: ✅ ({len(details['reviews'].get('recent_reviews', []))})")
        print(f"     - Gallery: ✅ ({len(details['gallery'])})")
        
    except Exception as e:
        print(f"  ⚠️  Error extracting gig details: {e}")
        import traceback
        traceback.print_exc()
    
    return details


def scrape_gig_details(gig_info, delay=2):
    """Scrape detailed information from a single gig page."""
    try:
        time.sleep(delay)
        
        gig_url = gig_info['url']
        print(f"  🔄 Scraping: {gig_url}")
        
        response = session.get(gig_url)
        gig_data = response.props_json()
        
        # Extract details
        details = extract_gig_details(gig_data)
        details['raw_url'] = gig_url
        details['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Include preview data
        details['preview_data'] = {
            'title': gig_info.get('title', ''),
            'price': gig_info.get('price', 0),
            'seller_name': gig_info.get('seller_name', ''),
            'seller_level': gig_info.get('seller_level', ''),
            'seller_rating': gig_info.get('seller_rating', 0),
            'seller_country': gig_info.get('seller_country', '')
        }
        
        return details
        
    except Exception as e:
        print(f"  ❌ Error scraping {gig_url}: {e}")
        import traceback
        traceback.print_exc()
        return None


def search_and_scrape_fiverr(keyword, api_key=None, output_dir="gigs_data", 
                             max_pages=1, delay=2):
    """Search Fiverr and scrape all gigs from results."""
    if not api_key:
        api_key = os.getenv('SCRAPER_API_KEY')
    
    if not api_key:
        print("❌ Error: No ScraperAPI key found!")
        print("   Option 1: Create .env file with SCRAPER_API_KEY=your_key")
        print("   Option 2: Use --key argument")
        return 0
    
    session.set_scraper_api_key(api_key)
    
    keyword_dir = Path(output_dir) / sanitize_filename(keyword)
    keyword_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🔍 Searching Fiverr for: '{keyword}'")
    print(f"📁 Output directory: {keyword_dir}")
    print(f"📄 Max pages to scrape: {max_pages}")
    print("=" * 60)
    
    all_gig_infos = []
    
    # Scrape search results
    for page in range(1, max_pages + 1):
        try:
            encoded_keyword = quote_plus(keyword)
            search_url = f"https://www.fiverr.com/search/gigs?query={encoded_keyword}&page={page}"
            
            print(f"\n📄 Scraping search results page {page}...")
            
            if page > 1:
                time.sleep(delay)
            
            response = session.get(search_url)
            search_data = response.props_json()
            
            gig_infos = extract_gig_urls_from_search(search_data)
            
            if not gig_infos:
                print(f"⚠️  No gigs found on page {page}, stopping...")
                break
            
            all_gig_infos.extend(gig_infos)
            
        except Exception as e:
            print(f"❌ Error scraping search page {page}: {e}")
            break
    
    print(f"\n✅ Total gigs found: {len(all_gig_infos)}")
    print("=" * 60)
    
    # Scrape individual gigs
    scraped_count = 0
    
    for idx, gig_info in enumerate(all_gig_infos, 1):
        print(f"\n[{idx}/{len(all_gig_infos)}] Processing gig...")
        title_preview = gig_info['title'][:60]
        print(f"  📌 {title_preview}...")
        
        gig_details = scrape_gig_details(gig_info, delay=delay)
        
        if gig_details:
            gig_id = gig_info.get('gig_id', idx)
            seller_name = sanitize_filename(gig_info.get('seller_name', 'unknown'))
            filename = f"gig_{gig_id}_{seller_name}.json"
            filepath = keyword_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(gig_details, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Saved: {filename}")
            scraped_count += 1
        else:
            print(f"  ⚠️  Skipped (no data)")
    
    print("\n" + "=" * 60)
    print(f"🎉 Scraping complete!")
    print(f"   Total gigs scraped: {scraped_count}/{len(all_gig_infos)}")
    print(f"   Saved in: {keyword_dir}")
    print("=" * 60)
    
    return scraped_count


def main():
    parser = argparse.ArgumentParser(
        description='Fiverr Search Scraper - FIXED VERSION',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python fiverr_scraper_FIXED.py "custom website development"
  python fiverr_scraper_FIXED.py "logo design" --pages 2
  python fiverr_scraper_FIXED.py "python automation" --key YOUR_KEY --delay 3
        '''
    )
    
    parser.add_argument('keyword', nargs='?', help='Search keyword')
    parser.add_argument('--key', '-k', help='ScraperAPI key (optional, reads from .env)')
    parser.add_argument('--output', '-o', default='gigs_data', help='Output directory')
    parser.add_argument('--pages', '-p', type=int, default=1, help='Max pages to scrape')
    parser.add_argument('--delay', '-d', type=int, default=2, help='Delay between requests')
    
    args = parser.parse_args()
    
    if not args.keyword:
        print("📝 Usage: python fiverr_scraper_FIXED.py '<KEYWORD>'")
        print("\nExample: python fiverr_scraper_FIXED.py \"custom website development\"")
        parser.print_help()
        sys.exit(0)
    
    search_and_scrape_fiverr(
        keyword=args.keyword,
        api_key=args.key,
        output_dir=args.output,
        max_pages=args.pages,
        delay=args.delay
    )


if __name__ == '__main__':
    main()