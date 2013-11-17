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
from dateutil.parser import parse as dateparse

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
    entries = trim_addresses(entries)
    entries = format_entries(entries)
    output_entries(entries, args.outfile)


def get_pages(soup):
    page_urls = set(e['href'] for e in soup.select('.paginate a'))
    return page_urls


def scrape_entries(soup):
    for row in soup.select('.searchresults tbody tr'):
        date_col, address_col, price_col = row.find_all('td')
        date = dateparse(date_col.find('strong').get_text().strip())
        price = price_col.get_text().strip()
        address = address_col.find('h2').get_text().strip()
        yield Entry(date, address, price)


def filter_entries(entries):
    for entry in entries:
        if 'Apartment' in entry.address:
            yield entry


def trim_addresses(entries):
    for entry in entries:
        apartment, number = entry.address.split(',', 1)[0].split()
        address = "{} {:>2}".format(apartment, number)
        yield Entry(entry.date, address, entry.price)


def format_entries(entries):
    addresses = set()
    house_prices = collections.defaultdict(dict)
    for entry in entries:
        addresses.add(entry.address)
        house_prices[entry.date][entry.address] = entry.price
    addresses = sorted(addresses)
    heading = ['Date'] + addresses
    yield heading
    for date in sorted(house_prices):
        row = [date.strftime("%Y-%m-%d")]
        for address in addresses:
            if address in house_prices[date]:
                row.append(house_prices[date][address])
            else:
                row.append(None)
        yield row


def output_entries(entries, outfile):
    writer = csv.writer(outfile)
    for entry in entries:
        writer.writerow(entry)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--outfile', nargs='?',
                        type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-d', '--debug', dest='loglevel', action='store_const',
                        const=logging.DEBUG, default=logging.WARN)
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    get_house_prices(args)
