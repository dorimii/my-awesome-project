import os

from bs4 import BeautifulSoup
from langchain.llms import OpenAI
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("OPENAI")

# url = "https://anno.onb.ac.at/cgi-content/annoshow?text=bbr|19000701|1"
# response = requests.get(url)

# llm = OpenAI(temperature=0.9, openai_api_key=key, model_name="gpt-3.5-turbo-0613")

# print(llm("Why do people prefer Mario over Luigi? In 10 words or fewer:"))

base_url = "https://anno.onb.ac.at/cgi-content/anno-plus?aid=bdv&datum=1900"
response = requests.get(base_url)
soup = BeautifulSoup(response.content, 'html.parser')
print(soup)
