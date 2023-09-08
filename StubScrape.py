import requests
import itertools
import string
from bs4 import BeautifulSoup

ZEITUNG_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno?aid={}"
ZEITSCHRIFT_BASE_URL = "https://anno.onb.ac.at/cgi-content/anno-plus?aid={}&datum=1900"


def scrapeStubs(base_url):

    # Generate the next all valid three letter combinations in alphabetical order starting from the one specified here
    start_combination = ('a', 'a', 'a')
    combinations = [''.join(comb) for comb in itertools.islice(itertools.product(string.ascii_lowercase, repeat=3),
                                                               list(itertools.product(string.ascii_lowercase,
                                                                                      repeat=3)).index(
                                                                   start_combination), None)]

    filename = "validstubs.json"

    x = 0
    for comb in combinations:
        response = requests.get(base_url.format(comb))

        soup = BeautifulSoup(response.content, 'html.parser')

        try:
            # Extract the content of the title tag
            title_content = soup.title.string.strip()
            #print(title_content)

            # Check if the title content contains a valid title
            # (ANNO doesn't return an error if the page is blank. so have to analyze the contents)
            # Also, the formatting is different between "Zeitung" and "Zeitschrift" yet again.
            if base_url == ZEITSCHRIFT_BASE_URL:
                if title_content != "ÖNB-ANNO -" and not soup.find("h3", class_="not_exists"):
                    # Write the valid stub to file as full link
                    with open(filename, 'a') as file:
                        file.write("https://anno.onb.ac.at/cgi-content/anno-plus?aid=" + comb + "&datum=1900" + '\n')
                    print("Found one!")

            elif base_url == ZEITUNG_BASE_URL:
                if title_content != "ÖNB/ANNO AustriaN Newspaper Online" and not soup.find("h3", class_="not_exists"):
                    with open(filename, 'a') as file:
                        file.write("https://anno.onb.ac.at/cgi-content/anno?aid=" + comb + '\n')
                    print("Found one!")

        except AttributeError:
            continue

        print("Checked " + comb + " as combination No. " + str(x))
        x += 1


def main():
    # ANNO has different structures for "Zeitschriften" and "Zeitungen". So we can swap what hardcoded base url
    # we want to pass deepending on what type of publication we want to get the stubs for here
    scrapeStubs(ZEITUNG_BASE_URL)


if __name__ == "__main__":
    main()
