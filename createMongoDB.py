import os
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['anno_db']
publications = db['publications']
issues = db['issues']

# db.drop_collection(issues)
# issues = db['issues']

base_dir = "ANNO Cleaned/test"
# TODO: Create mode for Zeitschriften


def clean_publication_name(name):
    for char in "()":
        name = name.replace(char, "")
    return name


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
                    date_str = os.path.splitext(file)[0]
                    try:
                        publication_date = datetime.strptime(date_str, '%Y-%m-%d')
                        file_path = os.path.join(year_dir, file)

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

for publication in publications.find():
    print(publication)

client.close()
