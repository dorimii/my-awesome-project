import os
import pandas as pd
import matplotlib.pyplot as plt
from transformers import GPT2TokenizerFast
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain
import requests
import sys
from bs4 import BeautifulSoup
import nltk
import tensorflow as tf
from transformers import MarianMTModel, MarianTokenizer
from autocorrect import Speller



url = "https://ia600203.us.archive.org/31/items/dieauslndische01espe/dieauslndische01espe_hocr.html"

response = requests.get(url)


# Check if the request was successful
if response.status_code == 200:
    # Get the content of the file
    html_content = response.text
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all "ocrx_word" elements
    ocr_words = soup.find_all("span", class_="ocrx_word")
    
    # Extract and print the text content of each word
    for word in ocr_words:
        # Use 'utf-8' encoding to avoid UnicodeEncodeError
        sys.stdout.buffer.write(word.text.encode('utf-8'))
        sys.stdout.buffer.write(b' ')  # Add a space between words
else:
    print("Failed to download the file. Status code:", response.status_code)


def uebersetze_alte_rechtschreibung(text):
    spell = Speller(lang='de')
    return spell(text)

alte_rechtschreibung = "Dieses Haus ist ein sch\x94nes Beispiel daf\x94r, wie man fr\x9cher geschrieben hat."
moderne_rechtschreibung = uebersetze_alte_rechtschreibung(alte_rechtschreibung)
print(moderne_rechtschreibung)