#!/usr/bin/env python3
"""Test CSV formatting fix by scraping a small batch"""

from scraper.playwright_scraper import TwitterScraper
import time

def test_csv_formatting():
    print("🧪 Testing CSV formatting fix...")
    
    # Create scraper and test with 10 tweets
    scraper = TwitterScraper()
    result_filename = scraper.scrape(
        keyword="technology",
        num_tweets=10,
        job_id="csv_format_test"
    )
    
    if result_filename:
        print(f"✅ Scrape completed: {result_filename}")
        
        # Check the first few lines to see if formatting is fixed
        import csv
        csv_path = f'scraped_data/{result_filename}'
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                lines = list(reader)
                
            print(f"\n📊 CSV Analysis:")
            print(f"Total rows: {len(lines)}")
            print(f"Header: {lines[0] if lines else 'No header'}")
            
            if len(lines) > 1:
                print(f"\nFirst data row fields: {len(lines[1])}")
                print(f"Text field (sanitized): {lines[1][5][:100]}..." if len(lines[1]) > 5 else "No text field")
                
                # Check if any text contains newlines (should be cleaned)
                for i, row in enumerate(lines[1:6]):  # Check first 5 data rows
                    if len(row) > 5 and '\\n' in row[5]:
                        print(f"⚠️  Row {i+1} still contains newlines in text field")
                    elif len(row) > 5:
                        print(f"✅ Row {i+1} text field properly formatted")
                        
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
    else:
        print("❌ Scraping failed")

if __name__ == "__main__":
    test_csv_formatting()