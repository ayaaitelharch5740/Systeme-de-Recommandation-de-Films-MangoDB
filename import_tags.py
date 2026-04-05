import csv
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["moviesdb"]
db.tags.drop()

with open("tag.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    batch = []
    for i, row in enumerate(reader):
        batch.append(dict(row))
        if len(batch) == 1000:
            db.tags.insert_many(batch)
            batch = []
            print(f"{i+1} documents insérés...")
    if batch:
        db.tags.insert_many(batch)

print("Import termine :", db.tags.count_documents({}), "tags importes")