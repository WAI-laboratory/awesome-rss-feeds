#!/usr/bin/env python3
"""
OPML to CSV Converter
Converts OPML files from the with_category directory to a CSV file.
"""

import os
import xml.etree.ElementTree as ET
import csv
import glob
import re
from pathlib import Path
import html

def fix_xml_encoding(xml_content):
    """
    Fix common XML encoding issues in OPML files.
    
    Args:
        xml_content (str): Raw XML content
        
    Returns:
        str: Fixed XML content
    """
    # Fix unescaped ampersands that are not already part of entity references
    # This regex looks for & that are not followed by common entity patterns
    xml_content = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', r'&amp;', xml_content)
    
    # Fix other common issues
    xml_content = xml_content.replace('&nbsp;', ' ')  # Replace non-breaking space
    xml_content = xml_content.replace('\u2019', "'")  # Replace curly apostrophe
    xml_content = xml_content.replace('\u201c', '"')  # Replace curly quotes
    xml_content = xml_content.replace('\u201d', '"')  # Replace curly quotes
    xml_content = xml_content.replace('\u2013', '-')  # Replace en dash
    xml_content = xml_content.replace('\u2014', '-')  # Replace em dash
    
    # Fix problematic characters that might cause XML parsing issues
    xml_content = xml_content.replace('\u00a0', ' ')  # Non-breaking space
    xml_content = xml_content.replace('\u2026', '...')  # Ellipsis
    xml_content = xml_content.replace('\u2018', "'")  # Left single quotation mark
    xml_content = xml_content.replace('\u2019', "'")  # Right single quotation mark
    xml_content = xml_content.replace('\u201c', '"')  # Left double quotation mark
    xml_content = xml_content.replace('\u201d', '"')  # Right double quotation mark
    
    return xml_content

def parse_opml_file(file_path):
    """
    Parse an OPML file and extract RSS feed information.
    
    Args:
        file_path (str): Path to the OPML file
        
    Returns:
        list: List of dictionaries containing feed information
    """
    feeds = []
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
        
        # Fix XML encoding issues
        xml_content = fix_xml_encoding(xml_content)
        
        # Parse the XML content
        root = ET.fromstring(xml_content)
        
        # Get the category name from the filename (remove .opml extension)
        category = Path(file_path).stem
        
        # Find all outline elements that contain RSS feeds
        for outline in root.findall('.//outline'):
            # Check if this outline has xmlUrl (indicates it's a feed)
            xml_url = outline.get('xmlUrl')
            if xml_url:
                # Extract feed information
                title = outline.get('text') or outline.get('title', '')
                description = outline.get('description', '')
                feed_type = outline.get('type', 'rss')
                
                # Clean up the extracted text
                title = html.unescape(title) if title else ''
                description = html.unescape(description) if description else ''
                
                feeds.append({
                    'title': title,
                    'description': description,
                    'url': xml_url,
                    'type': feed_type,
                    'category': category
                })
    
    except ET.ParseError as e:
        print(f"Error parsing {file_path}: {e}")
        # Try to extract what we can with a more lenient approach
        try:
            feeds.extend(parse_opml_file_fallback(file_path))
        except Exception as fallback_e:
            print(f"Fallback parsing also failed for {file_path}: {fallback_e}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return feeds

def parse_opml_file_fallback(file_path):
    """
    Fallback parsing method using regex for severely malformed XML.
    
    Args:
        file_path (str): Path to the OPML file
        
    Returns:
        list: List of dictionaries containing feed information
    """
    feeds = []
    category = Path(file_path).stem
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Use regex to find outline elements with xmlUrl
        # This regex looks for outline elements and captures attributes in any order
        pattern = r'<outline\s+[^>]*?xmlUrl="([^"]*)"[^>]*?>'
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            # Extract the full outline element text
            outline_text = match.group(0)
            xml_url = match.group(1)
            
            # Extract individual attributes from the outline element
            title = ''
            description = ''
            feed_type = 'rss'
            
            # Extract text attribute
            text_match = re.search(r'text="([^"]*)"', outline_text)
            if text_match:
                title = text_match.group(1)
            
            # Extract title attribute (fallback if text is empty)
            if not title:
                title_match = re.search(r'title="([^"]*)"', outline_text)
                if title_match:
                    title = title_match.group(1)
            
            # Extract description attribute
            desc_match = re.search(r'description="([^"]*)"', outline_text)
            if desc_match:
                description = desc_match.group(1)
            
            # Extract type attribute
            type_match = re.search(r'type="([^"]*)"', outline_text)
            if type_match:
                feed_type = type_match.group(1)
            
            if xml_url:  # Only add if we have a URL
                feeds.append({
                    'title': html.unescape(title) if title else '',
                    'description': html.unescape(description) if description else '',
                    'url': xml_url,
                    'type': feed_type,
                    'category': category
                })
    
    except Exception as e:
        print(f"Fallback parsing failed for {file_path}: {e}")
    
    return feeds

def convert_opml_to_csv(input_dir='recommended/with_category', output_file='rss_feeds.csv'):
    """
    Convert all OPML files in the input directory to a CSV file.
    
    Args:
        input_dir (str): Directory containing OPML files
        output_file (str): Output CSV file name
    """
    all_feeds = []
    
    # Find all OPML files in the directory
    opml_pattern = os.path.join(input_dir, '*.opml')
    opml_files = glob.glob(opml_pattern)
    
    if not opml_files:
        print(f"No OPML files found in {input_dir}")
        return
    
    print(f"Found {len(opml_files)} OPML files")
    
    # Process each OPML file
    for opml_file in opml_files:
        print(f"Processing: {os.path.basename(opml_file)}")
        feeds = parse_opml_file(opml_file)
        all_feeds.extend(feeds)
        print(f"  Extracted {len(feeds)} feeds")
    
    # Write to CSV file
    if all_feeds:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'description', 'url', 'type', 'category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write all feeds
            for feed in all_feeds:
                writer.writerow(feed)
        
        print(f"\nSuccessfully converted {len(all_feeds)} feeds to {output_file}")
    else:
        print("No feeds found to convert")

def main():
    """Main function to run the converter."""
    print("OPML to CSV Converter")
    print("=" * 50)
    
    # Check if the input directory exists
    input_dir = 'recommended/with_category'
    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' not found!")
        return
    
    # Convert OPML files to CSV
    convert_opml_to_csv(input_dir)
    
    print("\nConversion completed!")

if __name__ == "__main__":
    main() 