import csv
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import threading
import queue

MODE_ZEITUNG_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno?aid={}"
MODE_ZEITSCHRIFT_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno-plus?aid={}&datum=1900"
ANNO_URL = "https://anno.onb.ac.at/cgi-content/"


def notTrefferLog(type, publication_name):

    with open("NotTrefferLogs.csv", 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        if type == "NoEditionForYear":
            row = [publication_name, "", ""]
        if type == "NoLinkForYear":
            row = ["", publication_name, ""]
        if type == "NoEditionName":
            row = ["", "", publication_name]

        csv_writer.writerow(row)


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


def filterMagazinesByYearRange(magazine_links):
    if len(magazine_links) == 0:  # No publications found
        return
    # This is how we only get publications from 1890 to 1920
    filtered_links = [link for link in magazine_links if any(str(year) in link for year in range(1889, 1921))]

    return filtered_links


def saveToFile(year, publication_mode, magazine_name, edition, text):
    directory_name = "ANNO"
    directory = os.path.join(directory_name, publication_mode, magazine_name, year)
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_name = year + edition

    with open(os.path.join(directory, file_name), "w", encoding='utf-8') as file:
        file.write(text)

    print(magazine_name + year + edition)


def getPublicationTitle(soup, mode):

    raw_publication_title = soup.title.string.strip()
    if mode == MODE_ZEITSCHRIFT_BASE_URL:
        prefix = "ÖNB-ANNO - "
    else:
        prefix = "ANNO-"

    publication_title = raw_publication_title.replace(prefix, "")
    publication_title = publication_title.replace(" ", "_") # maybe better like that
    publication_title = publication_title.replace("/", "_")  # maybe better like that
    return publication_title


def getDiffPublicationModeLinks(mode, soup, content_zeitschrift, content_zeitung):
    # Again different based on the two datasets
    if mode == MODE_ZEITSCHRIFT_BASE_URL:
        magazine_links = extractLinks(soup, content_zeitschrift)

    else:
        magazine_links = extractLinks(soup, content_zeitung)

    return magazine_links


def getEditionNames(mode, magazine_soup, publication_title):
    global exception_counter

    if mode == MODE_ZEITSCHRIFT_BASE_URL:
        try:
            h1 = magazine_soup.find('h1').text
            h1_without_year = h1.split(": ")
            h1_replace = h1_without_year[-1].replace(" ", "") # we had the year in the title twice before - we could also just remove the year
            edition = h1_replace.replace(":", "")
        except Exception:
            notTrefferLog("NoEditionName", publication_title)
            return
    else:
        try:
            soup_title = magazine_soup.find('title').text  # edition is now publication date
            title_parts = soup_title.split(", ")
            edition = title_parts[-1]
            edition = edition.split("-")
            edition = "-" + "-".join(edition[1:]) # unfortunately rather ugly, might fix later

        except Exception:
            notTrefferLog("NoEditionName", publication_title)
            return

    return edition


def scrapeTextAndSave(mode, url):
    soup = fetchPage(url)

    publication_title = getPublicationTitle(soup, mode)

    magazine_links = getDiffPublicationModeLinks(mode, soup, ['anno-plus?', '&datum'], ['anno?', '&datum'])

    filtered_links = filterMagazinesByYearRange(magazine_links)

    if len(filtered_links) == 0:  # No publications found
        notTrefferLog("NoEditionForYear", publication_title)
        return

    # Eventually, we'll loop thru all years in the YearRange, but for now we stay in 1900
    try:
        year_index = filtered_links.index(next(link for link in filtered_links if "1900" in link))
    except Exception:
        notTrefferLog("NoLinkForYear", publication_title)
        return

    year_link = filtered_links[year_index]
    year_url = urljoin(ANNO_URL, year_link)
    year = "1900"  # TODO get year from year array
    #print(year_url)

    year_soup = fetchPage(year_url)
    year_magazine_links = getDiffPublicationModeLinks(mode, year_soup, ['anno-plus?', '&datum'], ['anno?', '&datum'])

    # Magazine Level
    for index, magazine in enumerate(year_magazine_links):
        combined_url = urljoin(year_url, magazine)
        magazine_soup = fetchPage(combined_url)

        edition = getEditionNames(mode, magazine_soup, publication_title)
        if not edition:
            return
        edition = edition.replace(" ", "")
        edition = edition.replace("/", "")

        text = []

        page_links = getDiffPublicationModeLinks(mode, magazine_soup, ['page'], ['seite'])

        # Page Level
        for page in page_links:
            page_url = page

            combined_page_url = urljoin(combined_url, page_url)
            page_soup = fetchPage(combined_page_url)

            text_links = getDiffPublicationModeLinks(mode, page_soup, ['window.open(\'annoshow'],
                                                     ['window.open(\'/cgi-content/annoshow'])

            if text_links:
                text_url = text_links[0]
                pattern = r"window.open\('(.*?)',"
                extracted_text_link = extractText(text_url, pattern)

                if extracted_text_link:
                    beginning_url_text = 'https://anno.onb.ac.at/cgi-content/'
                    new_text_url = urljoin(beginning_url_text, extracted_text_link)

                    text_soup = fetchPage(new_text_url)
                    page_text = text_soup.get_text()
                    text.append(page_text)

        magazine_text = "".join(text)

        if mode == MODE_ZEITSCHRIFT_BASE_URL:
            publication_mode = "Zeitschriften"

        else:
            publication_mode = "Zeitungen"

        saveToFile(year, publication_mode, publication_title, edition, magazine_text)


# Worker function for each thread
def worker(publications_queue):
    while not publications_queue.empty():
        try:
            # Get an argument from the queue
            url = publications_queue.get_nowait()
        except queue.Empty:
            return

        # Call the sample function with the argument
        if "anno-plus" in url:
            scrapeTextAndSave(MODE_ZEITSCHRIFT_BASE_URL, url)
        else:
            scrapeTextAndSave(MODE_ZEITUNG_BASE_URL, url)


def main():
    publications_queue = queue.Queue()

    # Publication Level
    with open('validstubsshort.txt', 'r') as file:
        for line in file:
            # Load all previously scraped urls into a queue for threads to scrape their content
            url = line.strip()
            publications_queue.put(url)

        # sehr hübsche Lösung babe, ich bin entzückt <3
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(publications_queue,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


if __name__ == "__main__":
    main()
