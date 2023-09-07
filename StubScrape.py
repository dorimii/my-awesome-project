import requests
import itertools
import string

from bs4 import BeautifulSoup


def main():
    # Generate the next ten three-letter combinations starting from "bdh"
    combinations = [''.join(comb) for comb in itertools.product(string.ascii_lowercase, repeat=3)]

    base_url = "https://anno.onb.ac.at/cgi-content/anno-plus?aid={}&datum=1900"
    filename = "validstubs.json"

    x = 0

    for comb in combinations:
        response = requests.get(base_url.format(comb))

        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the content of the title tag
        title_content = soup.title.string.strip()

        # Check if the title content is more than just "ÖNB-ANNO - "
        if title_content != "ÖNB-ANNO -":
            # Write the valid combination to a file
            with open(filename, 'a') as file:
                file.write("https://anno.onb.ac.at/cgi-content/anno-plus?aid=" + comb + "&datum=1900" + '\n')
                print("Found one!")

        print("Checked " + comb + " as combination " + str(x))
        x += 1

    # This will print out the ten combinations checked for reference
    # print("Checked combinations:", combinations)


if __name__ == "__main__":
    main()
