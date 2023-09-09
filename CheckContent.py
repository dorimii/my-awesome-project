import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import string

ZEITUNG_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno?aid={}"
ZEITSCHRIFT_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno-plus?aid={}&datum=1900"
ANNO_URL = "https://anno.onb.ac.at/cgi-content/"


def fetchPage(url):
    # print(url)
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


def filterMagazinesByYearRange(magazine_links):
    if len(magazine_links) == 0:  # No publications found
        return
    # This is how we only get publications from 1890 to 1920
    filtered_links = [link for link in magazine_links if any(str(year) in link for year in range(1889, 1921))]

    # TODO: There's a "nicht erschienen" class for years that have valid links but no actual data. Filter dem shits :)

    return filtered_links


def saveToFile(publication_mode, magazine_name, page, text):
    directory_name = "1900"
    directory = os.path.join(directory_name, publication_mode, magazine_name, str(page))
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, "text.txt"), "w", encoding='utf-8') as file:
        file.write(text)


def getPublicationTitle(soup, mode):

    raw_publication_title = soup.title.string.strip()
    if mode == ZEITSCHRIFT_BASE_URL:
        prefix = "ÖNB-ANNO - "
    else:
        prefix = "ANNO-"

    publication_title = raw_publication_title.replace(prefix, "")
    return publication_title


def getLinks(mode, soup):
    # Again different based on the two datasets
    if mode == ZEITSCHRIFT_BASE_URL:
        magazine_links = extractLinks(soup, ['anno-plus?', '&datum'])

    else:
        magazine_links = extractLinks(soup, ['anno?', '&datum'])

    return magazine_links


def scrapeTextAndSave(mode, url):
    soup = fetchPage(url)

    publication_title = getPublicationTitle(soup, mode)

    magazine_links = getLinks(mode, soup)

    filtered_links = filterMagazinesByYearRange(magazine_links)
    if len(filtered_links) == 0:  # No publications found
        print("Dis empty!")
        return

    # Eventually, we'll loop thru all years in the YearRange, but for now we stay in 1900
    year_index = filtered_links.index(next(link for link in filtered_links if "1900" in link))
    year_link = filtered_links[year_index]
    year_url = urljoin(ANNO_URL, year_link)

    year_soup = fetchPage(year_url)
    year_magazine_links = getLinks(mode, year_soup)
    # print(year_magazine_links)

    # Magazine Level
    for magazine in year_magazine_links:
        combined_url = urljoin(year_url, magazine)
        # print(combined_url)
        magazine_soup = fetchPage(combined_url)
        if mode == ZEITSCHRIFT_BASE_URL:
            page_links = extractLinks(magazine_soup, ['page'])
        else:
            page_links = extractLinks(magazine_soup, ['seite'])
        #print(page_links)

        # Page Level
        for index, page in enumerate(page_links):
            page_url = page

            combined_page_url = urljoin(combined_url, page_url)
            page_soup = fetchPage(combined_page_url)

            if mode == ZEITSCHRIFT_BASE_URL:
                text_links = extractLinks(page_soup, ['window.open(\'annoshow'])
            else:
                text_links = extractLinks(page_soup, ['window.open(\'/cgi-content/annoshow'])

            if text_links:
                text_url = text_links[0]
                pattern = r"window.open\('(.*?)',"
                extracted_text_link = extractText(text_url, pattern)


                if extracted_text_link:
                    beginning_url_text = 'https://anno.onb.ac.at/cgi-content/'
                    new_text_url = urljoin(beginning_url_text, extracted_text_link)
                    # print(new_text_url)
                    text_soup = fetchPage(new_text_url)
                    text = text_soup.get_text()
                    printable_text = ''.join(char for char in text if char in string.printable)
                    print(printable_text)
                    if mode == ZEITSCHRIFT_BASE_URL:
                        publication_mode = "Zeitschrift"
                    else:
                        publication_mode = "Zeitung"
                    saveToFile(publication_mode, publication_title, index + 1, text)

        print("\nNEXT MAGAZINE\n")


def main():
    with open('validstubs.txt', 'r') as file:
        # Publication Level
        # for line in file:   When everything else is ready, we can loop through each magazine stub like this
        # line = file.readline().strip()
        line = "https://anno.onb.ac.at/cgi-content/anno?aid=aog"
        # sehr hübsche Lösung babe, ich bin entzückt <3
        # At the moment, we only read the first line in validstubs.txt
        if "anno-plus" in line:
            scrapeTextAndSave(ZEITSCHRIFT_BASE_URL, line)
        else:
            scrapeTextAndSave(ZEITUNG_BASE_URL, line)


if __name__ == "__main__":
    main()
