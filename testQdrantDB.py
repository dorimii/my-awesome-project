from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
import uuid
import os
from tqdm import tqdm

client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections()
print(collections)

model = SentenceTransformer("intfloat/multilingual-e5-small")

query = "Was hat Kaiser Wilhelm am 7. Juli gemacht?"
query_vector = model.encode(query).tolist()

points = client.query_points(
    collection_name="german-english-multilingual-e5-small",
    query=query_vector,
    limit=5,
    with_payload=True,
    with_vectors=True
)

for i, point in enumerate(points.points, 1):
    print(f"\n🔎 Result {i} (Score: {point.score:.3f})")
    print(f"📰 Newspaper: {point.payload.get('newspaper')}")
    print(f"📄 File: {point.payload.get('file')}")
    print(f"📅 Year: {point.payload.get('year')}")
    print(f"📄 Text Preview: {point.payload.get('text')}...")
