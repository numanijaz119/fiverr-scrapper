"""
Example script to analyze scraped Fiverr gigs data
Shows common data analysis patterns on the scraped JSON files
"""

import json
from pathlib import Path
from collections import defaultdict


def load_all_gigs(keyword_dir):
    """Load all gig JSON files from a directory."""
    gigs = []
    keyword_path = Path(keyword_dir)
    
    if not keyword_path.exists():
        print(f"❌ Directory not found: {keyword_path}")
        return []
    
    for json_file in keyword_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                gig = json.load(f)
                gigs.append(gig)
        except Exception as e:
            print(f"⚠️  Error loading {json_file.name}: {e}")
    
    return gigs


def analyze_pricing(gigs):
    """Analyze pricing statistics."""
    print("\n" + "="*60)
    print("💰 PRICING ANALYSIS")
    print("="*60)
    
    prices = [g['pricing']['starting_price'] for g in gigs 
              if g.get('pricing', {}).get('starting_price')]
    
    if not prices:
        print("No pricing data available")
        return
    
    print(f"Total gigs analyzed: {len(prices)}")
    print(f"Average price: ${sum(prices)/len(prices):.2f}")
    print(f"Minimum price: ${min(prices):.2f}")
    print(f"Maximum price: ${max(prices):.2f}")
    print(f"Median price: ${sorted(prices)[len(prices)//2]:.2f}")
    
    # Price ranges
    ranges = {
        "Under $50": len([p for p in prices if p < 50]),
        "$50-$100": len([p for p in prices if 50 <= p < 100]),
        "$100-$250": len([p for p in prices if 100 <= p < 250]),
        "$250-$500": len([p for p in prices if 250 <= p < 500]),
        "$500+": len([p for p in prices if p >= 500])
    }
    
    print("\n📊 Price Distribution:")
    for range_name, count in ranges.items():
        percentage = (count / len(prices)) * 100
        print(f"  {range_name:12} : {count:3} gigs ({percentage:5.1f}%)")


def analyze_sellers(gigs):
    """Analyze seller statistics."""
    print("\n" + "="*60)
    print("👥 SELLER ANALYSIS")
    print("="*60)
    
    # Seller levels
    levels = defaultdict(int)
    for gig in gigs:
        level = gig.get('seller_info', {}).get('level_name', 'Unknown')
        levels[level] += 1
    
    print("\n📊 Seller Levels:")
    for level, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(gigs)) * 100
        print(f"  {level:20} : {count:3} ({percentage:5.1f}%)")
    
    # Top rated sellers
    print("\n⭐ Top 10 Rated Sellers:")
    top_sellers = sorted(
        gigs, 
        key=lambda x: (
            x.get('seller_info', {}).get('rating', 0),
            x.get('seller_info', {}).get('rating_count', 0)
        ),
        reverse=True
    )[:10]
    
    for i, gig in enumerate(top_sellers, 1):
        seller = gig.get('seller_info', {})
        print(f"  {i:2}. {seller.get('username', 'N/A'):20} "
              f"| {seller.get('rating', 0):.1f}★ "
              f"({seller.get('rating_count', 0)} reviews) "
              f"| {seller.get('level_name', 'N/A')}")
    
    # Pro sellers
    pro_count = sum(1 for g in gigs if g.get('seller_info', {}).get('is_pro', False))
    print(f"\n🏆 Pro Sellers: {pro_count}/{len(gigs)} ({(pro_count/len(gigs)*100):.1f}%)")


def analyze_delivery_times(gigs):
    """Analyze delivery time statistics."""
    print("\n" + "="*60)
    print("⏱️  DELIVERY TIME ANALYSIS")
    print("="*60)
    
    delivery_times = []
    for gig in gigs:
        packages = gig.get('packages', [])
        if packages:
            # Get basic package delivery time
            basic = next((p for p in packages if p['name'].lower() == 'basic'), None)
            if basic and basic.get('delivery_time'):
                delivery_times.append(basic['delivery_time'])
    
    if not delivery_times:
        print("No delivery time data available")
        return
    
    print(f"Average delivery time: {sum(delivery_times)/len(delivery_times):.1f} days")
    print(f"Minimum delivery time: {min(delivery_times)} days")
    print(f"Maximum delivery time: {max(delivery_times)} days")
    
    # Delivery time ranges
    ranges = {
        "1-2 days": len([d for d in delivery_times if d <= 2]),
        "3-5 days": len([d for d in delivery_times if 3 <= d <= 5]),
        "6-10 days": len([d for d in delivery_times if 6 <= d <= 10]),
        "11-20 days": len([d for d in delivery_times if 11 <= d <= 20]),
        "20+ days": len([d for d in delivery_times if d > 20])
    }
    
    print("\n📊 Delivery Time Distribution:")
    for range_name, count in ranges.items():
        percentage = (count / len(delivery_times)) * 100
        print(f"  {range_name:12} : {count:3} gigs ({percentage:5.1f}%)")


def analyze_orders_in_queue(gigs):
    """Analyze orders in queue."""
    print("\n" + "="*60)
    print("📋 ORDERS IN QUEUE ANALYSIS")
    print("="*60)
    
    orders = [g.get('orders_in_queue', 0) for g in gigs]
    
    if not orders:
        print("No orders in queue data available")
        return
    
    print(f"Average orders in queue: {sum(orders)/len(orders):.1f}")
    print(f"Maximum orders in queue: {max(orders)}")
    
    # Most in-demand gigs
    print("\n🔥 Most In-Demand Gigs (Top 5):")
    top_demand = sorted(gigs, key=lambda x: x.get('orders_in_queue', 0), reverse=True)[:5]
    
    for i, gig in enumerate(top_demand, 1):
        title = gig.get('title', 'N/A')[:50]
        orders = gig.get('orders_in_queue', 0)
        seller = gig.get('seller_info', {}).get('username', 'N/A')
        print(f"  {i}. {title:50} | {orders} orders | {seller}")


def analyze_packages(gigs):
    """Analyze package offerings."""
    print("\n" + "="*60)
    print("📦 PACKAGE ANALYSIS")
    print("="*60)
    
    gigs_with_packages = [g for g in gigs if g.get('packages')]
    
    print(f"Gigs offering packages: {len(gigs_with_packages)}/{len(gigs)} "
          f"({(len(gigs_with_packages)/len(gigs)*100):.1f}%)")
    
    # Average prices per package type
    package_prices = defaultdict(list)
    for gig in gigs_with_packages:
        for package in gig.get('packages', []):
            pkg_type = package.get('name', '').lower()
            price = package.get('price', 0)
            if price:
                package_prices[pkg_type].append(price)
    
    print("\n💵 Average Package Prices:")
    for pkg_type in ['basic', 'standard', 'premium']:
        if pkg_type in package_prices:
            avg = sum(package_prices[pkg_type]) / len(package_prices[pkg_type])
            print(f"  {pkg_type.capitalize():10} : ${avg:.2f}")


def export_csv(gigs, output_file="gigs_summary.csv"):
    """Export summary data to CSV."""
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Title', 'Seller', 'Level', 'Rating', 'Reviews', 
            'Starting Price', 'Orders in Queue', 'Country'
        ])
        
        for gig in gigs:
            writer.writerow([
                gig.get('title', '')[:100],
                gig.get('seller_info', {}).get('username', ''),
                gig.get('seller_info', {}).get('level_name', ''),
                gig.get('seller_info', {}).get('rating', 0),
                gig.get('seller_info', {}).get('rating_count', 0),
                gig.get('pricing', {}).get('starting_price', 0),
                gig.get('orders_in_queue', 0),
                gig.get('seller_info', {}).get('country', '')
            ])
    
    print(f"\n✅ CSV exported: {output_file}")


def main():
    # Example usage
    print("\n" + "="*60)
    print("🔍 FIVERR GIGS DATA ANALYSIS")
    print("="*60)
    
    # Change this to your scraped data directory
    keyword_dir = "gigs_data/custom_website_development"
    
    print(f"\n📁 Loading data from: {keyword_dir}")
    gigs = load_all_gigs(keyword_dir)
    
    if not gigs:
        print("\n❌ No gigs found. Please check the directory path.")
        print("\nExample: python analyze_gigs.py")
        print("Then edit the keyword_dir variable in the script.")
        return
    
    print(f"✅ Loaded {len(gigs)} gigs")
    
    # Run all analyses
    analyze_pricing(gigs)
    analyze_sellers(gigs)
    analyze_delivery_times(gigs)
    analyze_orders_in_queue(gigs)
    analyze_packages(gigs)
    
    # Export to CSV
    export_csv(gigs)
    
    print("\n" + "="*60)
    print("✨ Analysis complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()