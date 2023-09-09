import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import string

ZEITUNG_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno?aid={}"
ZEITSCHRIFT_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno-plus?aid={}&datum=1900"


def fetchPage(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def extractLinks(soup, conditions):
    extracted_links = []
    for link in soup.find_all('a'):
        bool_conditions = True
        href = link.get('href')
        if href:
            for condition in conditions:
                if condition not in href:
                    bool_conditions = False
                    break
            if bool_conditions:
                extracted_links.append(href)
    return extracted_links


def extractText(text_url, pattern):
    match = re.search(pattern, text_url)
    if match.group(1):
        return match.group(1)
    else:
        return None


def scrapeTextAndSave(mode, url):
    soup = fetchPage(url)
    # print(soup)

    # Cleaning up and filtering data before scraping individual editions
    if mode == ZEITSCHRIFT_BASE_URL:
        magazine_links = extractLinks(soup, ['anno-plus?', '&datum'])
        if len(magazine_links) == 0:  # No publications found for 1900 (current link structure demands the year 1900)
            return
        # Eventually we want to create folders automatically named after the publication,
        # we can later use publication_title for this
        raw_publication_title = soup.title.string.strip()
        prefix = "ÖNB-ANNO - "
        publication_title = raw_publication_title.replace(prefix, "")

    else:
        magazine_links = extractLinks(soup, ['anno-plus?', '&datum'])  # TODO

    # Magazine Level
    for magazine in magazine_links:
        combined_url = urljoin(url, magazine)
        magazine_soup = fetchPage(combined_url)
        page_links = extractLinks(magazine_soup, ['page'])
        for page in page_links:
            page_url = page
            # print(test_page_url)
            # test_page_url = './anno-plus?aid=kse&datum=1900&page=1&size=45'
            combined_page_url = urljoin(combined_url, page_url)
            page_soup = fetchPage(combined_page_url)
            # print(page_soup)
            page_links = extractLinks(page_soup, ['window.open(\'annoshow'])
            # print(page_links)

            if page_links:
                url = page_links[0]
                pattern = r"window.open\('(.*?)',"
                extracted_link = extractText(url, pattern)
                # print(extracted_link)

                if extracted_link:
                    beginning_url_text = 'https://anno.onb.ac.at/cgi-content/'
                    new_text_url = urljoin(beginning_url_text, extracted_link)
                    text_soup = fetchPage(new_text_url)
                    text = text_soup.get_text()
                    printable_text = ''.join(char for char in text if char in string.printable)
                    print(printable_text)
                else:
                    print('No match found.')
            else:
                print('No text links found.')
        print("\nNEXT MAGAZINE\n")


def main():
    with open('validstubs.txt', 'r') as file:
        # Publication Level
        # for line in file:   When everything else is ready, we can loop through each magazine stub like this
        line = file.readline().strip()
        # At the moment, we only read the first line in validstubs.txt
        if "anno-plus" in line:
            scrapeTextAndSave(ZEITSCHRIFT_BASE_URL, line)
        else:
            scrapeTextAndSave(ZEITUNG_BASE_URL, line)


if __name__ == "__main__":
    main()
