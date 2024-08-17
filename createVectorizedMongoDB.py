import os
from pymongo import MongoClient
from datetime import datetime
import re
from langchain_ollama.embeddings import OllamaEmbeddings
import asyncio

client = MongoClient('mongodb://localhost:27017/')
db = client['vectorized_anno_db']
issues = db['vectorized_issues']
publications = db['vectorized_publications']
db.drop_collection(issues)

base_dir = "ANNO Cleaned/Zeitungen1"
chunk_id = 1  # Initialize a global chunk_id

embedding_model = OllamaEmbeddings(model="mxbai-embed-large")  # Initialize the embedding model

# Set the mode based on the base_dir
if "Zeitungen" in base_dir:
    mode = "Zeitungen"
elif "Zeitschriften" in base_dir:
    mode = "Zeitschriften"
else:
    mode = "Unknown"

# Define the maximum number of tasks
MAX_TASKS = 8  # Adjust the number of tasks as needed


def clean_publication_name(name):
    for char in "()":
        name = name.replace(char, "")
    return name


def format_zeitschriften_date(filename):
    formatted_date = filename[:4] + " " + filename[4:]
    return formatted_date


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


def extract_pages(text):
    page_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} - \d{8} - (Seite \d+)"
    pages = re.split(page_pattern, text)

    cleaned_pages = []
    for i in range(1, len(pages), 2):
        page_header = pages[i].strip()
        page_content = pages[i + 1].strip()
        cleaned_pages.append(f"{page_header}\n{page_content}")

    return cleaned_pages


async def process_file(publication, year, file):
    global chunk_id
    clean_name = clean_publication_name(publication)
    publication_dir = os.path.join(base_dir, publication)
    year_dir = os.path.join(publication_dir, year)
    file_path = os.path.join(year_dir, file)
    date_str = os.path.splitext(file)[0]

    if mode == "Zeitungen":
        try:
            publication_date = datetime.strptime(date_str, '%Y-%m-%d')

            if issues.count_documents({"publication_name": clean_name, "publication_date": publication_date}) == 0:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                pages = extract_pages(content)

                for page_num, page_content in enumerate(pages, start=1):
                    chunks = chunk_text(page_content)

                    for chunk in chunks:
                        # Embed each chunk individually
                        embedding = await embedding_model.aembed_query(chunk)

                        issues.insert_one({
                            "publication_name": clean_name,
                            "publication_date": date_str,
                            "page": page_num,
                            "content_chunk": chunk,
                            "embedding": embedding,
                            "chunk_id": chunk_id
                        })
                        chunk_id += 1

        except ValueError:
            print(f"Invalid date format in file name: {file}")

    elif mode == "Zeitschriften":
        publication_date = format_zeitschriften_date(date_str)

        if issues.count_documents({"publication_name": clean_name, "publication_date": publication_date}) == 0:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            pages = extract_pages(content)

            for page_num, page_content in enumerate(pages, start=1):
                chunks = chunk_text(page_content)

                for chunk in chunks:
                    # Embed each chunk individually
                    embedding = await embedding_model.aembed_query(chunk)

                    issues.insert_one({
                        "publication_name": clean_name,
                        "publication_date": publication_date,
                        "page": page_num,
                        "content_chunk": chunk,
                        "embedding": embedding,
                        "chunk_id": chunk_id
                    })
                    chunk_id += 1


async def process_publication(publication):
    publication_dir = os.path.join(base_dir, publication)
    if os.path.isdir(publication_dir):
        for year in os.listdir(publication_dir):
            year_dir = os.path.join(publication_dir, year)
            if os.path.isdir(year_dir):
                for file in os.listdir(year_dir):
                    await process_file(publication, year, file)
        print("finished publication " + clean_publication_name(publication) + "\n")


async def worker_task(queue):
    while not queue.empty():
        publication = await queue.get()
        await process_publication(publication)
        queue.task_done()


async def main():
    queue = asyncio.Queue()
    for publication in os.listdir(base_dir):
        await queue.put(publication)

    tasks = []
    for _ in range(MAX_TASKS):
        task = asyncio.create_task(worker_task(queue))
        tasks.append(task)

    await queue.join()

    for task in tasks:
        task.cancel()

    for publication in publications.find():
        print(publication)

    client.close()

# Run the asyncio event loop
asyncio.run(main())
