import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# URL of the page
url = 'https://anno.onb.ac.at/cgi-content/anno-plus?aid=kse&datum=1900'

# Perform an HTTP GET request to fetch the raw HTML content
response = requests.get(url)

# Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all anchor tags in the HTML
links = soup.find_all('a')

content = []

# Loop through the anchor tags and add the href attributes to list
for link in links:
    href = link.get('href')
    if href and 'anno-plus?' in href and '&datum' in href: # Check if the href attribute exists
        content.append(href)

# print(content)

new_url = './anno-plus?aid=kse&datum=1900&pos=1&size=45'

combined_url = urljoin(url, new_url)
# print(combined_url)

new_response = requests.get(combined_url)
new_soup = BeautifulSoup(new_response.text, 'html.parser')
new_links = new_soup.find_all('a')
for link in new_links:
    new_href = link.get('href')
    if new_href and 'page' in new_href:
     pass
     #print(new_href)

# test link for text
test_url = './anno-plus?aid=kse&datum=1900&page=1&size=45'
combined_test = urljoin(combined_url, test_url)
test_response = requests.get(combined_test)
test_soup = BeautifulSoup(test_response.text, 'html.parser')
test_links = test_soup.find_all('a')
text_url = 0
for link in test_links:
   test_href = link.get('href')
   if test_href and '|X|' in test_href:
      # print(test_href)
      text_url = test_href

beginning_url_text = 'https://anno.onb.ac.at/cgi-content/'

# Regular expression to match the desired part
pattern = r"window.open\('(.*?)',"

# Use regex to find the match
match = re.search(pattern, text_url)

if match:
    extracted_part = match.group(1)
    # print('Extracted Part:', extracted_part)
else:
    print('No match found.')

new_text_url = urljoin(beginning_url_text, extracted_part)
# print(new_text_url)

response = requests.get(new_text_url)
soup = BeautifulSoup(response.text, 'html.parser')

text_content = soup.get_text()

print(text_content)
