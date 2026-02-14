from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
import uuid
import os
from tqdm import tqdm

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="german-english-multilingual-e5-small",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

model = SentenceTransformer("ferrisS/german-english-multilingual-e5-small")

base_dir = "ANNO Cleaned/Zeitungen1"
CHUNK_SIZE = 512


def chunk_text(text, chunk_size=CHUNK_SIZE):
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]


for newspaper_folder in os.listdir(base_dir):
    path_1900 = os.path.join(base_dir, newspaper_folder, "1900")

    if not os.path.isdir(path_1900):
        continue

    print(f"\n📂 Processing: {path_1900}")

    for filename in tqdm(os.listdir(path_1900)):
        file_path = os.path.join(path_1900, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                full_text = f.read()
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
            continue

        chunks = chunk_text(full_text)

        if not chunks:
            continue

        vectors = model.encode(chunks).tolist()

        points = [
            {
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "text": chunk,
                    "file": filename,
                    "newspaper": newspaper_folder,
                    "year": "1900"
                }
            }
            for chunk, vector in zip(chunks, vectors)
        ]

        try:
            client.upsert(collection_name="intfloat1", points=points)
            print(f"✅ Uploaded {len(points)} chunks from {filename}")
        except Exception as e:
            print(f"⚠️ Error uploading chunks from {filename}: {e}")
