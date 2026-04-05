import csv
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["moviesdb"]
db.movies.drop()

with open("movie.csv", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    batch = []
    for i, row in enumerate(reader):
        batch.append(dict(row))
        if len(batch) == 1000:
            db.movies.insert_many(batch)
            batch = []
            print(f"{i+1} documents insérés...")
    if batch:
        db.movies.insert_many(batch)

print("Import termine :", db.movies.count_documents({}), "films importes")
