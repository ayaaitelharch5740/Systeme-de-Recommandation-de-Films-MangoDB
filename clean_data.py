from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["moviesdb"]

# Étape 1 — Genres en tableau
print("Conversion des genres...")
for doc in db.movies.find():
    genres = doc["genres"].split("|") if doc.get("genres") else []
    db.movies.update_one(
        {"_id": doc["_id"]},
        {"$set": {"genres": genres}}
    )
print("Genres convertis")

# Étape 2 — Fusion links dans movies
print("Fusion des liens...")
for link in db.links.find():
    db.movies.update_one(
        {"movieId": int(link["movieId"])},
        {"$set": {
            "imdbId": link.get("imdbId", ""),
            "tmdbId": link.get("tmdbId", "")
        }}
    )
print("Liens fusionnes")

# Étape 3 — Supprimer la collection links
db.links.drop()
print("Collection links supprimee")

print("Nettoyage termine !")