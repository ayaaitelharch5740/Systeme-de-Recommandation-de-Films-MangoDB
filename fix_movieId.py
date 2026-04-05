from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["moviesdb"]

count = 0
for doc in db.movies.find():
    try:
        mid = int(doc["movieId"])
        db.movies.update_one(
            {"_id": doc["_id"]},
            {"$set": {"movieId": mid}}
        )
        count += 1
        if count % 1000 == 0:
            print(f"{count} films mis a jour...")
    except:
        pass

print(f"Termine ! {count} films mis a jour")