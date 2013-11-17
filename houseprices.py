#!/usr/bin/env python

from bs4 import BeautifulSoup
import requests

URL = "http://www.primelocation.com/house-prices/london/tollington-road/?q=Tollington%20Road%2C%20London%20N7&search_source=house-prices"

def get_house_prices():
    response = requests.get(URL)
    soup = BeautifulSoup(response.content)
    entries = scrape_entries(soup)
    entries = filter_entries(entries)
    output_entries(entries)

    for next_page_url in get_pages(soup):
        entries = scrape_entries(soup)
        entries = filter_entries(entries)
        output_entries(entries)


def get_pages(soup):
    page_urls = set(e['href'] for e in soup.select('.paginate a'))
    return page_urls


def scrape_entries(soup):
    for row in soup.select('.searchresults tbody tr'):
        date_col, address_col, price_col = row.find_all('td')
        date = date_col.find('strong').get_text().strip()
        price = price_col.get_text().strip()
        address = address_col.find('h2').get_text().strip()
        yield (date, address, price)


def filter_entries(entries):
    for date, address, price in entries:
        if 'Apartment' in address:
            yield (date, address, price)


def output_entries(entries):
    for date, address, price in entries:
        print ", ".join([date, address, price])


if __name__ == '__main__':
    get_house_prices()
