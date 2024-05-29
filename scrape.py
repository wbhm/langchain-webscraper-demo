import argparse
import os
import re
import ssl

import requests
import urllib.request
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError, ContentTooShortError


parser = argparse.ArgumentParser()
parser.add_argument("--site", type=str, required=True)
parser.add_argument("--retries", type=int, default=0)

def cleanUrl(url: str):
    return url.replace("https://", "ssl.").replace("/", "=").replace(".", "_")

def download_and_save(url, user_agent='webscraper', num_retires=0 , charset='utf-8'):
    print ('Downloading', url)

    try:
        request = urllib.request.Request(url, headers={'User-Agent': user_agent})
        request.add_header('User-Agent', user_agent)
        gcontext = ssl.SSLContext()
        response = urllib.request.urlopen(request, context=gcontext)

        if not os.path.exists("./scrape"):
            os.mkdir("./scrape")
        cleaned_url = cleanUrl(url)
        cs = response.headers.get('char-set')
        if not cs:
            cs = charset
        with open("./scrape/" + cleaned_url + ".html", "w") as f:
            try:
                response_bytes = response.read()
                html = response_bytes.decode(charset)
                f.write(html)
            except Exception as e:
                print(e)
    except (URLError, HTTPError, ContentTooShortError) as e:
        print('Download Error: ', e.reason)
        if num_retires > 0 :
            if hasattr(e, 'code') and 500 <= e.code < 600 : # recursively retry 5XX HTTP Errors
                download_and_save(url, num_retires - 1)


def crawl_sitemap(url):
    # download site map xml
    sitemap = requests.get(url)
    #extract site mapp links
    links = re.findall(r'<loc>(.+?)</loc>', sitemap.text)
    # download each link
    for link in links:
        if parsed_url.netloc in link:
            download_and_save(link, retries)

    with open("./scrape/sitemap.xml", "w") as f:
        f.write(sitemap.text)

if __name__ == "__main__":
    args = parser.parse_args()
    url = args.site
    parsed_url = urlparse(url)
    retries = args.retries
    print('Crawling: ', url)
    crawl_sitemap(url)
