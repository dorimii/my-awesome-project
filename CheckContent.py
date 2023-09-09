import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import string

ZEITUNG_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno?aid={}"
ZEITSCHRIFT_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno-plus?aid={}&datum=1900"


def fetchPage(url):
    print(url)
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


def filterMagazines(magazine_links):
    if len(magazine_links) == 0:  # No publications found
        return
    # This is how we only get publications from 1890 to 1920
    filtered_links = [link for link in magazine_links if any(str(year) in link for year in range(1889, 1921))]

    return filtered_links


def getPublicationTitle(soup, mode):

    raw_publication_title = soup.title.string.strip()
    if mode == ZEITSCHRIFT_BASE_URL:
        prefix = "ÖNB-ANNO - "
    else:
        prefix = "ANNO-"

    publication_title = raw_publication_title.replace(prefix, "")
    return publication_title


def scrapeTextAndSave(mode, url):
    soup = fetchPage(url)

    # Cleaning up and filtering data before scraping individual editions
    if mode == ZEITSCHRIFT_BASE_URL:
        magazine_links = extractLinks(soup, ['anno-plus?', '&datum'])

    else:
        magazine_links = extractLinks(soup, ['anno?', '&datum'])

    filtered_links = filterMagazines(magazine_links)
    publication_title = getPublicationTitle(soup, mode)
    #print(filtered_links)
    #print(publication_title)

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
                page_url_new = page_links[0]
                pattern = r"window.open\('(.*?)',"
                extracted_link = extractText(page_url_new, pattern)
                # print(extracted_link)

                if extracted_link:
                    beginning_url_text = 'https://anno.onb.ac.at/cgi-content/'
                    new_text_url = urljoin(beginning_url_text, extracted_link)
                    text_soup = fetchPage(new_text_url)
                    text = text_soup.get_text()
                    printable_text = ''.join(char for char in text if char in string.printable)
                    # print(printable_text)
                else:
                    print('No match found.')
                    break
            else:
                print('No text links found.')
                break
        print("\nNEXT MAGAZINE\n")


def main():
    with open('validstubs.txt', 'r') as file:
        # Publication Level
        # for line in file:   When everything else is ready, we can loop through each magazine stub like this
        line = file.readline().strip()
        # sehr hübsche Lösung babe, ich bin entzückt <3
        # At the moment, we only read the first line in validstubs.txt
        if "anno-plus" in line:
            scrapeTextAndSave(ZEITSCHRIFT_BASE_URL, line)
        else:
            scrapeTextAndSave(ZEITUNG_BASE_URL, line)


if __name__ == "__main__":
    main()
