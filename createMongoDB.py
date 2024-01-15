import os
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['anno_db']
publications = db['publications']
issues = db['issues']

# db.drop_collection(issues)
# issues = db['issues']

base_dir = "ANNO Cleaned/Zeitungen"

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
                                with open(file_path, 'r') as f:
                                    content = f.read()

                                issues.insert_one({
                                    "publication_name": clean_name,
                                    "publication_date": date_str,
                                    "content": content
                                })

                        except ValueError:
                            print(f"Invalid date format in file name: {file}")

                    elif mode == "Zeitschriften":
                        # Example: Use the file name directly or another logic for the date
                        publication_date = format_zeitschriften_date(date_str)

                        if issues.count_documents(
                                {"publication_name": clean_name, "publication_date": publication_date}) == 0:
                            with open(file_path, 'r') as f:
                                content = f.read()

                            issues.insert_one({
                                "publication_name": clean_name,
                                "publication_date": publication_date,
                                "content": content
                            })

for publication in publications.find():
    print(publication)

client.close()
