import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


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


def main():
    # Publication Level
    base_url = 'https://anno.onb.ac.at/cgi-content/anno-plus?aid=kse&datum=1900'
    soup = fetchPage(base_url)
    #print(soup)

    # Magazine Level
    magazine_links = extractLinks(soup, ['anno-plus?', '&datum'])
    #print(magazine_links)
    magazine_url = './anno-plus?aid=kse&datum=1900&pos=1&size=45'
    combined_url = urljoin(base_url, magazine_url)
    magazine_soup = fetchPage(combined_url)
    #print(magazine_soup)

    # Page Level
    page_links = extractLinks(magazine_soup, ['page'])
    test_page_url = './anno-plus?aid=kse&datum=1900&page=1&size=45'
    combined_test_page_url = urljoin(combined_url, test_page_url)
    test_page_soup = fetchPage(combined_test_page_url)
    #print(test_page_soup)
    test_page_links = extractLinks(test_page_soup, ['window.open(\'annoshow'])
    print(test_page_links)

    if test_page_links:
        url = test_page_links[0]
        pattern = r"window.open\('(.*?)',"
        extracted_link = extractText(url, pattern)
        # print(extracted_link)

        if extracted_link:
            beginning_url_text = 'https://anno.onb.ac.at/cgi-content/'
            new_text_url = urljoin(beginning_url_text, extracted_link)
            text_soup = fetchPage(new_text_url)
            #print(text_soup.get_text())
        else:
            print('No match found.')
    else:
        print('No text links found.')


if __name__ == "__main__":
    main()
