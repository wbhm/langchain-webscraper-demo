import argparse
import os
import re
import ssl
import logging
import concurrent.futures

import requests
import urllib.request
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError, ContentTooShortError
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--site", type=str, required=True)
parser.add_argument("--retries", type=int, default=0)
parser.add_argument("--threads", type=int, default=20)


def cleanUrl(url: str):
    return url.replace("https://", "ssl.").replace("/", "=").replace(".", "_")


def download_and_save(url, user_agent='webscraper', retries=0, charset='utf-8'):
    logging.info('Downloading %s', url)

    try:
        request = urllib.request.Request(url, headers={'User-Agent': user_agent})
        request.add_header('User-Agent', user_agent)
        gcontext = ssl.SSLContext()
        response = urllib.request.urlopen(request, context=gcontext)
        scrape_dir = os.getenv("SCRAPE_DIR", './scrape')

        cleaned_url = cleanUrl(url)
        cs = response.headers.get('char-set')
        if not cs:
            cs = charset
        with open(scrape_dir + "/" + cleaned_url + ".html", "w") as f:
            try:
                response_bytes = response.read()
                html = response_bytes.decode(charset)
                f.write(html)
            except Exception as e:
                logging.error(e)
    except (URLError, HTTPError, ContentTooShortError) as e:
        logging.error('Download Error: %s', e.reason)
        if retries > 0:
            # recursively retry 5XX HTTP Errors
            if hasattr(e, 'code') and 500 <= e.code < 600:
                download_and_save(url, retries - 1)


def crawl_sitemap(url, retries=0, threads=20):
    parsed_url = urlparse(url)

    # download site map xml
    try:
        sitemap = requests.get(url)
    except Exception as e:
        logging.error('Failed to get sitemap: %s', e)
        return

    # extract site map links
    links = re.findall(r'<loc>(.+?)</loc>', sitemap.text)

    # download each link
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        for link in links:
            if parsed_url.netloc in link:
                executor.submit(download_and_save, link, retries=retries)

    with open("./scrape/sitemap.xml", "w") as f:
        f.write(sitemap.text)


def main():
    load_dotenv()
    args = parser.parse_args()
    retries = args.retries
    threads = args.threads
    url = args.site
    logging.info('Crawling: %s', url)
    scrape_dir = os.getenv("SCRAPE_DIR", './scrape')
    if not os.path.exists(scrape_dir):
        os.mkdir(scrape_dir)
    crawl_sitemap(url, retries, threads)


if __name__ == "__main__":
    main()