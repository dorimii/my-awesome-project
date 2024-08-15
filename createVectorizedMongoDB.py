import os
from pymongo import MongoClient
from datetime import datetime
import re

client = MongoClient('mongodb://localhost:27017/')
db = client['vectorized_anno_db']
issues = db['vectorized_issues']
publications = db['vectorized_publications']

base_dir = "ANNO Cleaned/Zeitungen"
chunk_id = 1  # Initialize a global chunk_id

if "Zeitungen" in base_dir:
    mode = "Zeitungen"
elif "Zeitschriften" in base_dir:
    mode = "Zeitschriften"
else:
    mode = "Unknown"


def clean_publication_name(name):
    for char in "()":
        name = name.replace(char, "")
    return name


def format_zeitschriften_date(filename):
    # Insert a space after the first four characters (year)
    formatted_date = filename[:4] + " " + filename[4:]
    return formatted_date


# Split content of all editions into chunks fo 2048 characters, which is on the large side for RAG but smaller than that
# would take ages for a db of this size. Overlap of 64 to avoid context loss mid sentence.
def chunk_text(text, max_chars=2048, overlap=64):
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + max_chars
        if end >= text_length:
            chunk = text[start:].ljust(max_chars)
            chunks.append(chunk)
            break

        if text[end] != ' ':
            last_space = text.rfind(' ', start, end)
            if last_space != -1:
                end = last_space

        chunk = text[start:end].ljust(max_chars)
        chunks.append(chunk)
        start = end - overlap

    return chunks


# Think it's nice for the LLM to be able to state what page of an edition it's found information on it's replying with.
def extract_pages(text):
    # Pattern to match and remove the header, keeping only "Seite X"
    page_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} - \d{8} - (Seite \d+)"
    pages = re.split(page_pattern, text)

    cleaned_pages = []
    for i in range(1, len(pages), 2):
        page_header = pages[i].strip()  # This will be "Seite X"
        page_content = pages[i + 1].strip()
        cleaned_pages.append(f"{page_header}\n{page_content}")

    return cleaned_pages


for publication in os.listdir(base_dir):
    clean_name = clean_publication_name(publication)

    if publications.count_documents({"name": clean_name}) == 0:
        publications.insert_one({"name": clean_name})

    publication_dir = os.path.join(base_dir, publication)
    if os.path.isdir(publication_dir):
        for year in os.listdir(publication_dir):
            year_dir = os.path.join(publication_dir, year)
            if os.path.isdir(year_dir):
                for file in os.listdir(year_dir):
                    file_path = os.path.join(year_dir, file)
                    date_str = os.path.splitext(file)[0]

                    if mode == "Zeitungen":
                        try:
                            publication_date = datetime.strptime(date_str, '%Y-%m-%d')

                            if issues.count_documents(
                                    {"publication_name": clean_name, "publication_date": publication_date}) == 0:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()

                                pages = extract_pages(content)

                                for page_num, page_content in enumerate(pages, start=1):
                                    chunks = chunk_text(page_content)

                                    for chunk in chunks:
                                        issues.insert_one({
                                            "publication_name": clean_name,
                                            "publication_date": date_str,
                                            "page": page_num,
                                            "content_chunk": chunk,
                                            "chunk_id": chunk_id
                                        })
                                        chunk_id += 1  # Increment chunk_id globally

                        except ValueError:
                            print(f"Invalid date format in file name: {file}")

                    # Yes this is duplicated
                    elif mode == "Zeitschriften":
                        publication_date = format_zeitschriften_date(date_str)

                        if issues.count_documents(
                                {"publication_name": clean_name, "publication_date": publication_date}) == 0:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            pages = extract_pages(content)

                            for page_num, page_content in enumerate(pages, start=1):
                                chunks = chunk_text(page_content)

                                for chunk in chunks:
                                    issues.insert_one({
                                        "publication_name": clean_name,
                                        "publication_date": publication_date,
                                        "page": page_num,
                                        "content_chunk": chunk,
                                        "chunk_id": chunk_id
                                    })
                                    chunk_id += 1  # Increment chunk_id globally

                print("finished publication " + clean_name + "\n")


for publication in publications.find():
    print(publication)

client.close()
