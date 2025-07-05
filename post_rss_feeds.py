#!/usr/bin/env python3
"""
RSS Feed Poster
Reads rss_feeds.csv and posts each feed to the API endpoint.
"""

import csv
import requests
import time
from urllib.parse import urlparse
import sys

def extract_domain(url):
    """
    Extract the domain from a URL.
    
    Args:
        url (str): The full URL
        
    Returns:
        str: The domain part of the URL
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return url  # Return original URL if parsing fails

def post_rss_feed(api_url, title, feed_url, domain, category_name):
    """
    Post a single RSS feed to the API.
    
    Args:
        api_url (str): The API endpoint URL
        title (str): Feed title
        feed_url (str): Feed URL
        domain (str): Domain name
        category_name (str): Category name
        
    Returns:
        bool: True if successful, False otherwise
    """
    payload = {
        "title": title,
        "feedUrl": feed_url,
        "domain": domain,
        "categoryName": category_name
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            print(f"✅ Successfully posted: {title}")
            return True
        else:
            print(f"❌ Failed to post {title}: HTTP {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error posting {title}: {e}")
        return False

def post_all_feeds(csv_file='rss_feeds.csv', api_url='https://api.sobabear.com/rss/category', delay=0.5):
    """
    Read CSV file and post all feeds to the API.
    
    Args:
        csv_file (str): Path to the CSV file
        api_url (str): API endpoint URL
        delay (float): Delay between requests in seconds
    """
    successful_posts = 0
    failed_posts = 0
    total_feeds = 0
    
    print(f"RSS Feed Poster")
    print(f"=" * 50)
    print(f"Reading from: {csv_file}")
    print(f"Posting to: {api_url}")
    print(f"Delay between requests: {delay}s")
    print()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Count total rows first
            rows = list(reader)
            total_feeds = len(rows)
            print(f"Found {total_feeds} feeds to process")
            print()
            
            for i, row in enumerate(rows, 1):
                title = row['title'].strip()
                feed_url = row['url'].strip()
                category_name = row['category'].strip()
                
                # Skip rows with empty required fields
                if not title or not feed_url or not category_name:
                    print(f"⚠️  Skipping row {i}: Missing required fields")
                    continue
                
                # Extract domain from the feed URL
                domain = extract_domain(feed_url)
                
                print(f"[{i}/{total_feeds}] Processing: {title} ({category_name})")
                
                # Post to API
                success = post_rss_feed(api_url, title, feed_url, domain, category_name)
                
                if success:
                    successful_posts += 1
                else:
                    failed_posts += 1
                
                # Add delay between requests to be respectful to the API
                if i < total_feeds:  # Don't delay after the last request
                    time.sleep(delay)
                    
    except FileNotFoundError:
        print(f"❌ Error: Could not find file '{csv_file}'")
        return
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return
    
    print()
    print("Summary:")
    print(f"Total feeds processed: {total_feeds}")
    print(f"Successful posts: {successful_posts}")
    print(f"Failed posts: {failed_posts}")
    
    if failed_posts > 0:
        print(f"\n⚠️  {failed_posts} feeds failed to post. Check the error messages above.")
    else:
        print("\n🎉 All feeds posted successfully!")

def main():
    """Main function with command line argument support."""
    csv_file = 'rss_feeds.csv'
    api_url = 'https://api.sobabear.com/rss/category'
    delay = 0.5  # 500ms delay between requests
    
    # Check if custom CSV file is provided
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    # Check if custom API URL is provided
    if len(sys.argv) > 2:
        api_url = sys.argv[2]
    
    # Check if custom delay is provided
    if len(sys.argv) > 3:
        try:
            delay = float(sys.argv[3])
        except ValueError:
            print("Warning: Invalid delay value, using default 0.5 seconds")
            delay = 0.5
    
    # Confirm before proceeding
    print(f"About to post {csv_file} to {api_url}")
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        post_all_feeds(csv_file, api_url, delay)
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main() 