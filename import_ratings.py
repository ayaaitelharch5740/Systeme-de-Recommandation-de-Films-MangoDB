import csv
from pymongo import MongoClient, errors

client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=60000,
    socketTimeoutMS=120000
)
db = client["moviesdb"]
db.ratings.drop()

total = 0
batch = []

with open("rating.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        batch.append({
            "userId": int(row["userId"]),
            "movieId": int(row["movieId"]),
            "rating": float(row["rating"]),
            "timestamp": row["timestamp"]
        })
        if len(batch) == 5000:
            try:
                db.ratings.insert_many(batch)
                total += len(batch)
                print(f"{total} documents insérés...")
            except Exception as e:
                print(f"Erreur: {e}, retry...")
                db.ratings.insert_many(batch)
            batch = []

if batch:
    db.ratings.insert_many(batch)
    total += len(batch)

print("Import termine :", db.ratings.count_documents({}), "ratings importes")