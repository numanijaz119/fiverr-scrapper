"""
Fiverr Keyword Analysis - Data Consolidation Script
Extracts all important market research data from scraped gigs
and consolidates into a single JSON file per keyword
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re


def extract_gig_data(gig):
    """
    Extract all important data from a gig for market research.
    Returns a clean, consolidated data structure.
    """
    
    # === SELLER INFORMATION ===
    seller_info = gig.get('seller_info', {})
    preview_data = gig.get('preview_data', {})
    
    # Handle rating which can be either a dict or a direct value or None
    rating_value = seller_info.get('rating')
    if isinstance(rating_value, dict):
        rating = rating_value.get('score', 0)
        rating_count = rating_value.get('count', 0)
    else:
        rating = rating_value if rating_value is not None else 0
        rating_count = seller_info.get('ratings_count', 0)
    
    # Get seller_level from preview_data (more reliable) or seller_info
    seller_level = preview_data.get('seller_level', '') or seller_info.get('level', '') or seller_info.get('seller_level', '')
    
    # Get seller description and convert to plain text
    seller_desc = seller_info.get('description', '')
    if seller_desc:
        seller_desc_plain = re.sub(r'<[^>]+>', '', seller_desc)
        seller_desc_plain = re.sub(r'\s+', ' ', seller_desc_plain).strip()
    else:
        seller_desc_plain = ''
    
    seller_data = {
        'username': seller_info.get('username', '') or preview_data.get('seller_name', ''),
        'display_name': seller_info.get('display_name', ''),
        'seller_id': seller_info.get('seller_id', ''),
        'seller_level': seller_level,  # Now gets it from preview_data first!
        'rating': rating,
        'ratings_count': rating_count,
        'completed_orders': seller_info.get('completed_orders', 0),
        'is_pro': seller_info.get('is_pro', False),
        'country': seller_info.get('country', '') or seller_info.get('country_code', '') or preview_data.get('seller_country', ''),
        'member_since': seller_info.get('member_since', ''),
        'response_time': seller_info.get('response_time', 0),
        'languages': [lang.get('code', '') for lang in seller_info.get('languages', [])],
        'one_liner': seller_info.get('one_liner', ''),
        'description': seller_desc_plain,
        'certifications_count': len(seller_info.get('certifications', [])),
        'education_count': len(seller_info.get('education', [])),
        'portfolio_count': seller_info.get('portfolios', {}).get('totalCount', 0)
    }
    
    # === GIG INFORMATION ===
    gig_info = gig.get('gig_info', {})
    gig_data = {
        'gig_id': gig_info.get('gig_id', ''),
        'title': gig.get('title', ''),
        'rating': gig_info.get('rating', 0),
        'ratings_count': gig_info.get('ratings_count', 0),
        'orders_in_queue': gig.get('orders_in_queue', 0),
        'collected_count': gig_info.get('collected_count', 0),  # favorites/saves
        'category': gig_info.get('category', {}).get('name', ''),
        'sub_category': gig_info.get('sub_category', {}).get('name', ''),
        'nested_sub_category': gig_info.get('nested_sub_category', {}).get('name', ''),
        'is_restricted': gig_info.get('is_restricted', False),
        'gig_url': gig.get('raw_url', '')
    }
    
    # === DESCRIPTION - PLAIN TEXT ONLY ===
    description = gig.get('description', '')
    if description:
        # Remove HTML tags for analysis
        plain_description = re.sub(r'<[^>]+>', '', description)
        plain_description = re.sub(r'\s+', ' ', plain_description).strip()
    else:
        plain_description = ''
    
    description_data = {
        'description': plain_description,  # Just plain text
        'word_count': len(plain_description.split()) if plain_description else 0,
        'short_description': gig.get('short_description', '')
    }
    
    # === TAGS ===
    tags = gig.get('tags', [])
    tags_list = [tag.get('name', '') for tag in tags if tag.get('name')]
    
    # === PACKAGES ===
    packages = gig.get('packages', [])
    packages_data = []
    
    for package in packages:
        pkg = {
            'tier': package.get('name', ''),
            'title': package.get('title', ''),
            'description': package.get('description', ''),
            'price': package.get('price', 0) or 0,
            'delivery_time_days': package.get('delivery_time_days', 0) or 0,
            'revisions': package.get('revisions', 0) or 0,
            'revisions_unlimited': package.get('revisions_unlimited', False),
            'features': {}  # Will be populated as clean dict
        }
        
        # Extract features - SIMPLIFIED to key-value pairs
        features_dict = {}
        for feature in package.get('features', []):
            feature_name = feature.get('label', '') or feature.get('name', '')
            feature_value = feature.get('value', 0)
            feature_type = feature.get('type', '')
            
            # Convert to simple readable format
            if feature_type == 'BOOLEAN':
                features_dict[feature_name] = True if feature.get('included', False) else False
            elif feature_type == 'NUMERIC':
                features_dict[feature_name] = feature_value
            else:
                # For other types, just include if it's marked as included
                if feature.get('included', False):
                    features_dict[feature_name] = feature_value if feature_value else True
        
        pkg['features'] = features_dict  # Now a clean dict instead of array
        
        # Extra fast delivery - simplified
        extra_fast = package.get('extra_fast_delivery', {})
        if extra_fast and extra_fast.get('available'):
            pkg['extra_fast_delivery_hours'] = extra_fast.get('duration_hours', 0)
            pkg['extra_fast_delivery_price'] = extra_fast.get('price', 0)
        
        packages_data.append(pkg)
    
    # === PRICING ===
    pricing = gig.get('pricing', {})
    pricing_data = {
        'starting_price': pricing.get('starting_price', 0) or 0,
        'highest_price': pricing.get('highest_price', 0) or 0,
        'currency': pricing.get('currency', 'USD'),
        'currency_symbol': pricing.get('currency_symbol', '$'),
        'has_packages': pricing.get('has_packages', False)
    }
    
    # Calculate price per day (value metric)
    if packages_data and packages_data[0].get('delivery_time_days', 0) > 0 and packages_data[0].get('price', 0) > 0:
        pricing_data['basic_price_per_day'] = round(packages_data[0]['price'] / packages_data[0]['delivery_time_days'], 2)
    else:
        pricing_data['basic_price_per_day'] = 0
    
    # === REVIEWS SUMMARY ===
    reviews = gig.get('reviews', {})
    reviews_data = {
        'rating': reviews.get('rating', 0),
        'reviews_count': reviews.get('reviews_count', 0),
        'star_breakdown': reviews.get('breakdown', []),
        'star_summary': reviews.get('star_summary', {})
    }
    
    # === FAQS ===
    faqs = gig.get('faqs', [])
    faqs_data = [
        {
            'question': faq.get('question', ''),
            'answer': faq.get('answer', '')
        }
        for faq in faqs
    ]
    
    # === GALLERY - SIMPLIFIED ===
    gallery = gig.get('gallery', [])
    gallery_data = {
        'total_items': len(gallery),
        'has_video': any(item.get('is_video', False) for item in gallery),
        'video_count': len([item for item in gallery if item.get('is_video', False)]),
        'image_count': len([item for item in gallery if not item.get('is_video', False)])
    }
    
    # === METADATA - SIMPLIFIED ===
    metadata = gig.get('metadata', [])
    metadata_data = {}
    for meta in metadata:
        meta_name = meta.get('name', '')
        options = meta.get('options', [])
        
        if options:
            # Extract just the labels from options
            if isinstance(options, list):
                labels = []
                for opt in options:
                    if isinstance(opt, dict):
                        label = opt.get('label', '') or opt.get('value', '')
                        if label:
                            labels.append(label)
                    elif isinstance(opt, str):
                        labels.append(opt)
                
                if labels:
                    metadata_data[meta_name] = labels
            else:
                metadata_data[meta_name] = options
    
    # === SCRAPING INFO ===
    scraping_info = {
        'scraped_at': gig.get('scraped_at', ''),
        'data_source': 'fiverr_api_scraper'
    }
    
    # === PREVIEW DATA (from search results) ===
    preview = gig.get('preview_data', {})
    preview_data = {
        'search_price': preview.get('price', 0),
        'seller_rating_in_search': preview.get('seller_rating', 0)
    }
    
    # === CONSOLIDATED GIG DATA ===
    consolidated = {
        'seller': seller_data,
        'gig': gig_data,
        'description': description_data,
        'tags': tags_list,
        'packages': packages_data,
        'pricing': pricing_data,
        'reviews': reviews_data,
        'faqs': faqs_data,
        'gallery': gallery_data,
        'metadata': metadata_data,
        'preview_data': preview_data,
        'scraping_info': scraping_info
    }
    
    return consolidated


def calculate_keyword_statistics(all_gigs_data):
    """
    Calculate overall statistics for the keyword.
    """
    if not all_gigs_data:
        return {}
    
    # Pricing statistics
    prices = [gig['pricing']['starting_price'] for gig in all_gigs_data 
              if gig['pricing'].get('starting_price') and gig['pricing']['starting_price'] > 0]
    
    pricing_stats = {}
    if prices:
        pricing_stats = {
            'average_price': round(sum(prices) / len(prices), 2),
            'min_price': min(prices),
            'max_price': max(prices),
            'median_price': round(sorted(prices)[len(prices)//2], 2),
            'price_ranges': {
                'under_50': len([p for p in prices if p < 50]),
                '50_to_100': len([p for p in prices if 50 <= p < 100]),
                '100_to_250': len([p for p in prices if 100 <= p < 250]),
                '250_to_500': len([p for p in prices if 250 <= p < 500]),
                'over_500': len([p for p in prices if p >= 500])
            }
        }
    
    # Seller level distribution (counts only, not averages)
    levels = defaultdict(int)
    for gig in all_gigs_data:
        level = gig['seller']['seller_level']  # FIXED: was 'level'
        if level:
            levels[level] += 1
    
    # Rating distribution
    ratings = [gig['seller']['rating'] for gig in all_gigs_data 
               if gig['seller']['rating'] is not None and gig['seller']['rating'] > 0]
    rating_stats = {}
    if ratings:
        rating_stats = {
            'average_seller_rating': round(sum(ratings) / len(ratings), 2),
            'min_rating': min(ratings),
            'max_rating': max(ratings)
        }
    
    # Orders in queue
    orders = [gig['gig']['orders_in_queue'] for gig in all_gigs_data 
              if gig['gig'].get('orders_in_queue') is not None]
    orders_stats = {
        'average_orders_in_queue': round(sum(orders) / len(orders), 2) if orders else 0,
        'max_orders_in_queue': max(orders) if orders else 0,
        'total_orders_in_queue': sum(orders) if orders else 0
    }
    
    # Delivery time statistics
    delivery_times = []
    for gig in all_gigs_data:
        if gig['packages']:
            basic_package = next((p for p in gig['packages'] if p['tier'].lower() == 'basic'), None)
            if basic_package:
                delivery_time = basic_package.get('delivery_time_days')
                if delivery_time and delivery_time > 0:
                    delivery_times.append(delivery_time)
    
    delivery_stats = {}
    if delivery_times:
        delivery_stats = {
            'average_delivery_time': round(sum(delivery_times) / len(delivery_times), 2),
            'min_delivery_time': min(delivery_times),
            'max_delivery_time': max(delivery_times)
        }
    
    # Pro sellers count
    pro_count = sum(1 for gig in all_gigs_data if gig['seller']['is_pro'])
    
    # Tag frequency
    all_tags = []
    for gig in all_gigs_data:
        all_tags.extend(gig['tags'])
    
    tag_frequency = defaultdict(int)
    for tag in all_tags:
        tag_frequency[tag] += 1
    
    # Sort tags by frequency
    top_tags = sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:20]
    
    # Category distribution
    categories = defaultdict(int)
    for gig in all_gigs_data:
        cat = gig['gig']['category']
        if cat:
            categories[cat] += 1
    
    statistics = {
        'total_gigs': len(all_gigs_data),
        'pricing': pricing_stats,
        'seller_levels': dict(levels),
        'ratings': rating_stats,
        'orders': orders_stats,
        'delivery_times': delivery_stats,
        'pro_sellers_count': pro_count,
        'pro_sellers_percentage': round((pro_count / len(all_gigs_data)) * 100, 2),
        'top_20_tags': [{'tag': tag, 'count': count} for tag, count in top_tags],
        'category_distribution': dict(categories)
    }
    
    return statistics


def process_keyword_directory(keyword_dir):
    """
    Process all gig JSON files in a keyword directory.
    Returns consolidated data for all gigs.
    """
    keyword_path = Path(keyword_dir)
    
    if not keyword_path.exists():
        print(f"❌ Directory not found: {keyword_path}")
        return None, None
    
    print(f"\n📁 Processing directory: {keyword_path}")
    
    all_gigs_data = []
    processed_count = 0
    error_count = 0
    
    # Get all JSON files (exclude debug files)
    json_files = [f for f in keyword_path.glob("gig_*.json") if not f.name.startswith("debug_")]
    
    if not json_files:
        print(f"❌ No gig JSON files found in {keyword_path}")
        return None, None
    
    print(f"📄 Found {len(json_files)} gig files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                gig = json.load(f)
            
            # Extract consolidated data
            consolidated_data = extract_gig_data(gig)
            all_gigs_data.append(consolidated_data)
            processed_count += 1
            
            if processed_count % 10 == 0:
                print(f"  ✓ Processed {processed_count}/{len(json_files)} gigs...")
                
        except Exception as e:
            print(f"  ⚠️  Error processing {json_file.name}: {e}")
            error_count += 1
    
    print(f"\n✅ Successfully processed: {processed_count}/{len(json_files)} gigs")
    if error_count > 0:
        print(f"⚠️  Errors: {error_count}")
    
    # Calculate statistics
    statistics = calculate_keyword_statistics(all_gigs_data)
    
    return all_gigs_data, statistics


def save_consolidated_data(keyword_name, all_gigs_data, statistics, output_dir):
    """
    Save consolidated data to a single JSON file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create the consolidated data structure
    consolidated = {
        'keyword': keyword_name,
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'statistics': statistics,
        'gigs': all_gigs_data
    }
    
    # Save to JSON file
    output_file = output_path / f"{keyword_name}_analysis.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Consolidated data saved: {output_file}")
    print(f"   File size: {output_file.stat().st_size / 1024:.2f} KB")
    
    return output_file


def print_summary(keyword_name, statistics):
    """
    Print a summary of the analysis.
    """
    print("\n" + "="*60)
    print(f"📊 KEYWORD ANALYSIS SUMMARY: {keyword_name}")
    print("="*60)
    
    stats = statistics
    
    print(f"\n📈 Overall Statistics:")
    print(f"   Total Gigs: {stats['total_gigs']}")
    print(f"   Pro Sellers: {stats['pro_sellers_count']} ({stats['pro_sellers_percentage']}%)")
    
    if stats.get('pricing'):
        print(f"\n💰 Pricing:")
        print(f"   Average: ${stats['pricing']['average_price']:.2f}")
        print(f"   Range: ${stats['pricing']['min_price']:.2f} - ${stats['pricing']['max_price']:.2f}")
        print(f"   Median: ${stats['pricing']['median_price']:.2f}")
    
    if stats.get('ratings'):
        print(f"\n⭐ Ratings:")
        print(f"   Average Seller Rating: {stats['ratings']['average_seller_rating']:.2f}/5.0")
    
    if stats.get('orders'):
        print(f"\n📋 Orders:")
        print(f"   Average Orders in Queue: {stats['orders']['average_orders_in_queue']:.1f}")
        print(f"   Total Orders in Queue: {stats['orders']['total_orders_in_queue']}")
    
    if stats.get('delivery_times'):
        print(f"\n⏱️  Delivery Times:")
        print(f"   Average: {stats['delivery_times']['average_delivery_time']:.1f} days")
        print(f"   Range: {stats['delivery_times']['min_delivery_time']:.0f} - {stats['delivery_times']['max_delivery_time']:.0f} days")
    
    print(f"\n🏷️  Top 10 Tags:")
    for i, tag_info in enumerate(stats.get('top_20_tags', [])[:10], 1):
        print(f"   {i:2}. {tag_info['tag']:30} ({tag_info['count']} gigs)")
    
    print("\n" + "="*60)


def main():
    """
    Main function - processes keyword directories and creates consolidated JSON files.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Consolidate Fiverr gigs data into a single JSON per keyword',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python analyze_keyword_consolidated.py gigs_data/custom_website_development
  python analyze_keyword_consolidated.py gigs_data/logo_design --output analysis_results
  
  # Process multiple keywords
  python analyze_keyword_consolidated.py gigs_data/keyword1 gigs_data/keyword2
        '''
    )
    
    parser.add_argument('directories', nargs='+', help='Keyword directory/directories to process')
    parser.add_argument('--output', '-o', default='keyword_analysis', 
                       help='Output directory for consolidated JSON files')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔍 FIVERR KEYWORD ANALYSIS - DATA CONSOLIDATION")
    print("="*60)
    
    for keyword_dir in args.directories:
        # Extract keyword name from directory
        keyword_name = Path(keyword_dir).name
        
        # Process the directory
        all_gigs_data, statistics = process_keyword_directory(keyword_dir)
        
        if all_gigs_data and statistics:
            # Save consolidated data
            output_file = save_consolidated_data(
                keyword_name, 
                all_gigs_data, 
                statistics, 
                args.output
            )
            
            # Print summary
            print_summary(keyword_name, statistics)
        else:
            print(f"❌ Failed to process {keyword_dir}")
        
        print("\n" + "-"*60)
    
    print("\n✨ Analysis complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()