#!/usr/bin/env python

import argparse
import collections
import csv
import itertools
import logging
import operator
import urllib.parse

import sys
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

URL = "http://www.primelocation.com/house-prices/london/tollington-road/?q=Tollington%20Road%2C%20London%20N7&search_source=house-prices"  # NOQA


Entry = collections.namedtuple("Entry", ['date', 'address', 'price'])


def get_house_prices(args):
    response = requests.get(URL)
    soup = BeautifulSoup(response.content)
    entries = scrape_entries(soup)
    for next_page_url in get_pages(soup):
        url = urllib.parse.urljoin(URL, next_page_url)
        response = requests.get(url)
        soup = BeautifulSoup(response.content)
        next_page_entries = scrape_entries(soup)
        entries = itertools.chain(entries, next_page_entries)
    entries = filter_entries(entries)
    entries = format_entries(entries)
    output_entries(entries, args.outfile)


def get_pages(soup):
    page_urls = set(e['href'] for e in soup.select('.paginate a'))
    return page_urls


def scrape_entries(soup):
    for row in soup.select('.searchresults tbody tr'):
        date_col, address_col, price_col = row.find_all('td')
        date = date_col.find('strong').get_text().strip()
        price = price_col.get_text().strip()
        address = address_col.find('h2').get_text().strip()
        yield Entry(date, address, price)


def filter_entries(entries):
    for entry in entries:
        if 'Apartment' in entry.address:
            yield entry


def trim_addresses(entries):
    for entry in entries:
        address = entry.address.split(',', 1)[0]
        yield Entry(entry.date, address, entry.price)


def format_entries(entries):
    keyfunc = lambda e: (e.address, e.date)
    entries = sorted(trim_addresses(entries), key=keyfunc)
    grouped = itertools.groupby(entries, operator.attrgetter('address'))
    for address, group_entries in grouped:
        row = [address]
        for entry in group_entries:
            row.extend([entry.date, entry.price])
        yield row


def output_entries(entries, outfile):
    writer = csv.writer(outfile)
    for entry in entries:
        writer.writerow(entry)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    get_house_prices(args)
