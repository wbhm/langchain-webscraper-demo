import argparse
import json
import os
import re
import ssl

import requests
import urllib.request
from urllib.parse import urlparse, urljoin
from urllib.error import URLError, HTTPError, ContentTooShortError


parser = argparse.ArgumentParser()
parser.add_argument("--site", type=str, required=True)
parser.add_argument("--retries", type=int, default=0)

def cleanUrl(url: str):
    return url.replace("https://", "").replace("/", "-").replace(".", "_")

def download_and_save(url, user_agent='webscraper', num_retires=0 , charset='utf-8'):
    print ('Downloading', url)

    try:
        request = urllib.request.Request(url, headers={'User-Agent': user_agent})
        request.add_header('User-Agent', user_agent)
        gcontext = ssl.SSLContext()
        response = urllib.request.urlopen(request, context=gcontext)

        if not os.path.exists("./scrape"):
            os.mkdir("./scrape")
        parsedUrl = cleanUrl(url)
        cs = response.headers.get('char-set')
        if not cs:
            cs = charset
        with open("./scrape/" + parsedUrl + ".html", "w") as f:
            try:
                response_bytes = response.read()
                html = response_bytes.decode(charset)
                f.write(html)
            except Exception as e:
                print(e)
                html = None
    except (URLError, HTTPError, ContentTooShortError) as e:
        print('Download Error: ', e.reason)
        html = None
        if num_retires > 0 :
            if hasattr(e, 'code') and 500 <= e.code < 600 : # recursively retry 5XX HTTP Errors
                return download_and_save(url, num_retires - 1)
    return html


def crawl_sitemap(url):
    # download site map xml
    sitemap = requests.get(url)
    #extract site mapp links
    links = re.findall(r'<loc>(.+?)</loc>', sitemap.text)
    # download each link
    for link in links:
        html = download_and_save(link, retries)
        #scrape html
    with open("./scrape/sitemap.xml", "w") as f:
        f.write(sitemap)

if __name__ == "__main__":
    args = parser.parse_args()
    url = args.site
    retries = args.retries
    print('Crawling: ', url)
    crawl_sitemap(url)
