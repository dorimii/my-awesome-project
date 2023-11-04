# This script scrapes *all* archived contents published by ANNO from a set timeframe based on the stubs found by
# StubScrape.py and saves it on disk. ANNO only provides OCR scanned text files from the individual page level,
# so for any given year to be scraped over a million calls have to be made to the site to combine the texts.
# For the year 1900, this script saved 2.4GB of plaintext in 18.022 individual editions, which amounts to roughly
# 400 million words (assuming an average of 5 characters per word), a plausible sum for the time.

import csv
import os
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import threading
import queue
from unidecode import unidecode
from urllib3.exceptions import MaxRetryError

NUM_THREADS = 24  # 24 threads seem to produce the most efficient rate
MODE_ZEITUNG_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno?aid={}"
MODE_ZEITSCHRIFT_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno-plus?aid={}&datum=1900"
ANNO_URL = "https://anno.onb.ac.at/cgi-content/"

treffer_times = [time.gmtime(0)] * NUM_THREADS
treffer_lock = threading.Lock()
stubs_file_lock = threading.Lock()


def notTrefferLog(type, publication_name):

    with open("NotTrefferLogs.csv", 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        if type == "NoEditionForYear":
            row = [publication_name, "", "", ""]
        if type == "NoLinkForYear":
            row = ["", publication_name, "", ""]
        if type == "NoEditionName":
            row = ["", "", publication_name, ""]
        if type == "UnfetchableURL":
            row = ["", "", "", publication_name]

        csv_writer.writerow(row)


def calculateScrapingSpeed():

    # This is a (maybe dumb) way of tracking how fast we are scraping the site. This func is called every time a
    # magazine is saved to disk. It temporarily logs the timestamp and returns an approx rate of saves per minute

    with treffer_lock:
        treffer_times[1:] = treffer_times[:-1]
        treffer_times[0] = time.gmtime()
        time_diff_seconds = time.mktime(treffer_times[0]) - time.mktime(treffer_times[NUM_THREADS - 1])

        return 60 / (time_diff_seconds / NUM_THREADS)


def fetchPage(url):

    max_retries = 10
    retry_delay = 60

    for attempt in range(1, max_retries):
        try:
            response = requests.get(url)
            return BeautifulSoup(response.text, 'html.parser')

        except Exception as e:
            if isinstance(e, MaxRetryError):
                print(f"MaxRetryError for {url}. {e}")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Max retries reached. Giving up.")
                    notTrefferLog("UnfetchableURL", url)
            else:
                notTrefferLog("UnfetchableURL", url)


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
    # This is how we only get publications from 1890 to 1920, can be adapted at will
    filtered_links = [link for link in magazine_links if any(str(year) in link for year in range(1889, 1921))]

    return filtered_links


def cleanString(text):
    illegal_characters = r':'
    ascii_text = unidecode(text)  # maybe redundant
    cleaned_string = ''.join(char if char not in illegal_characters else '' for char in ascii_text)
    cleaned_string = ''.join(char if char.isprintable() else '_' for char in cleaned_string)
    cleaned_string = re.sub(r'_+', '_', cleaned_string)
    return cleaned_string


def saveToFile(year, publication_mode, magazine_name, edition, text):
    directory_name = "ANNO"
    directory = os.path.join(directory_name, publication_mode, magazine_name, year)
    # clean directory name
    directory = cleanString(directory)
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_name = year + edition
    # clean file name
    file_name = cleanString(file_name)
    with open(os.path.join(directory, file_name), "w", encoding='utf-8', errors='replace') as file:
        file.write(text)

    clean_magazine_name = cleanString(magazine_name)
    current_scraping_rate = calculateScrapingSpeed()

    print(clean_magazine_name + " " + file_name + ". Curr scraping rate is " + str(current_scraping_rate) + "mags/min."
          + " Number of active threads: {}".format(threading.active_count() - 1))


def getPublicationTitle(raw_publication_title, mode):

    if mode == MODE_ZEITSCHRIFT_BASE_URL:
        prefix = "ÖNB-ANNO - "
    else:
        prefix = "ANNO-"

    publication_title = raw_publication_title.replace(prefix, "")
    publication_title = publication_title.replace(" ", "_")
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

    try:
        soup = fetchPage(url)
    except Exception:
        notTrefferLog("NoLinkForYear", url)
        return

    if soup is None:  # Empty URL, shouldn't happen but betta 2 b safe
        return
    else:
        try:
            soup_title = soup.title.string.strip()  # No title tag usually means publication is just a pamphlet
        except Exception:
            return

    publication_title = getPublicationTitle(soup_title, mode)

    magazine_links = getDiffPublicationModeLinks(mode, soup, ['anno-plus?', '&datum'], ['anno?', '&datum'])

    filtered_links = filterMagazinesByYearRange(magazine_links)

    if filtered_links is None:  # No publications found
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

        with stubs_file_lock:
            with open('stubsyettoscrape.txt', 'r') as file:
                lines = file.readlines()

            # Filter out line containing url
            lines = [line for line in lines if url not in line]

            # Write the updated content back to the file
            with open('stubsyettoscrape.txt', 'w') as file:
                file.writelines(lines)


def main():
    publications_queue = queue.Queue()

    # Publication Level
    with open('stubsyettoscrape.txt', 'r') as file:
        for line in file:
            # Load all previously scraped urls into a queue for threads to scrape their content
            url = line.strip()
            publications_queue.put(url)

        threads = []
        for i in range(NUM_THREADS):
            thread = threading.Thread(target=worker, args=(publications_queue,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


if __name__ == "__main__":
    main()
