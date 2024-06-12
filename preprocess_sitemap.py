import argparse
import re
import os
import logging
from lxml import etree
from collections import defaultdict


def count_file_types(sitemap_file_path):
    # Check if file exists
    if not os.path.isfile(sitemap_file_path):
        logging.error(f"File not found: {sitemap_file_path}")
        return

    # Define the namespace
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    file_types = defaultdict(list)

    try:
        # Use iterparse for efficient parsing of large files
        for _, element in etree.iterparse(sitemap_file_path, tag='{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            url = element.text
            ext = re.search(r'\.(\w+)$', url)  # Use regex to get file extension
            if ext:
                file_types[ext.group(1)].append(url)
            # It's safe to call clear() here because no descendants will be accessed
            element.clear()
    except etree.XMLSyntaxError as e:
        logging.error(f"Error parsing XML: {e}")
        return

    # Print each file type, the total number of files, and the URLs
    for file_type, urls in file_types.items():
        print(f'File type .{file_type} (Total: {len(urls)} files):')
        for url in urls:
            print(f'  {url}')
        print()

    return file_types


# Set up logging
logging.basicConfig(level=logging.INFO)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Count file types in a sitemap.')
parser.add_argument('file_path', help='The path to the sitemap file.')
args = parser.parse_args()

# Call the function with the file path argument
count_file_types(args.file_path)
