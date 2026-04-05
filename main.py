from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from jose import JWTError, jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
import uvicorn

app = FastAPI(title="CineMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient("mongodb://localhost:27017/")
db = client["moviesdb"]

SECRET_KEY = "cinematch-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- MODELES ---
class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    userId: Optional[int] = None
    role: Optional[str] = None

# --- FONCTIONS AUTH ---
def hash_password(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token invalide")
        user = db.users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

def is_admin(current_user) -> bool:
    return current_user.get("role") == "admin"

def check_access(current_user, user_id: int):
    """Vérifie que l'utilisateur peut accéder aux données demandées."""
    if not is_admin(current_user) and current_user.get("userId") != user_id:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé : vous ne pouvez accéder qu'à vos propres données"
        )

# --- ROUTES AUTH ---
@app.post("/auth/register", response_model=Token)
def register(user: UserRegister):
    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà pris")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit faire au moins 6 caractères")
    count = db.users.count_documents({})
    new_user = {
        "username": user.username,
        "password": hash_password(user.password),
        "email": user.email,
        "userId": count + 1,
        "role": "user",
        "created_at": datetime.utcnow()
    }
    db.users.insert_one(new_user)
    token = create_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "userId": new_user["userId"],
        "role": "user"
    }

@app.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = db.users.find_one({"username": form.username})
    if not user or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = create_token({"sub": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "userId": user.get("userId"),
        "role": user.get("role", "user")
    }

@app.get("/auth/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user.get("email"),
        "userId": current_user.get("userId"),
        "role": current_user.get("role", "user")
    }

# --- ROUTE ADMIN : promouvoir un utilisateur ---
@app.put("/admin/promote/{username}")
def promote_user(username: str, current_user=Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    result = db.users.update_one(
        {"username": username},
        {"$set": {"role": "admin"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"message": f"'{username}' est maintenant administrateur"}

# --- ROUTE ADMIN : liste tous les utilisateurs ---
@app.get("/admin/users")
def list_users(current_user=Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    users = list(db.users.find({}, {"_id": 0, "password": 0}))
    return {"count": len(users), "users": users}
@app.get("/users/{user_id}/profile/admin")
def user_profile_admin(user_id: int, limit: int = 5, current_user=Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    pipeline = [
        { "$match": { "userId": user_id, "rating": { "$gte": 3.5 } } },
        { "$lookup": {
            "from": "movies",
            "localField": "movieId",
            "foreignField": "movieId",
            "as": "movieInfo"
        }},
        { "$unwind": "$movieInfo" },
        { "$unwind": "$movieInfo.genres" },
        { "$group": {
            "_id": "$movieInfo.genres",
            "count": { "$sum": 1 }
        }},
        { "$sort": { "count": -1 } },
        { "$limit": limit }
    ]
    results = list(db.ratings.aggregate(pipeline))
    return {
        "userId": user_id,
        "favoriteGenres": [{"genre": r["_id"], "count": r["count"]} for r in results]
    }

# --- ROUTES FILMS ---
@app.get("/")
def home():
    return {"message": "CineMatch API", "status": "running"}

@app.get("/movies/top")
def top_movies(limit: int = 20, min_votes: int = 50):
    pipeline = [
        { "$group": {
            "_id": "$movieId",
            "avgRating": { "$avg": "$rating" },
            "totalVotes": { "$sum": 1 }
        }},
        { "$match": { "totalVotes": { "$gte": min_votes } } },
        { "$lookup": {
            "from": "movies",
            "localField": "_id",
            "foreignField": "movieId",
            "as": "movieInfo"
        }},
        { "$unwind": "$movieInfo" },
        { "$group": {
            "_id": "$_id",
            "title": { "$first": "$movieInfo.title" },
            "genres": { "$first": "$movieInfo.genres" },
            "avgRating": { "$first": "$avgRating" },
            "totalVotes": { "$first": "$totalVotes" }
        }},
        { "$project": {
            "_id": 0,
            "movieId": "$_id",
            "title": 1,
            "genres": 1,
            "avgRating": { "$round": ["$avgRating", 2] },
            "totalVotes": 1
        }},
        { "$sort": { "avgRating": -1 } },
        { "$limit": limit }
    ]
    results = list(db.ratings.aggregate(pipeline))
    return {"count": len(results), "movies": results}

@app.get("/users/{user_id}/profile")
def user_profile(user_id: int, limit: int = 5, current_user=Depends(get_current_user)):
    check_access(current_user, user_id)
    pipeline = [
        { "$match": { "userId": user_id, "rating": { "$gte": 3.5 } } },
        { "$lookup": {
            "from": "movies",
            "localField": "movieId",
            "foreignField": "movieId",
            "as": "movieInfo"
        }},
        { "$unwind": "$movieInfo" },
        { "$unwind": "$movieInfo.genres" },
        { "$group": {
            "_id": "$movieInfo.genres",
            "count": { "$sum": 1 }
        }},
        { "$sort": { "count": -1 } },
        { "$limit": limit }
    ]
    results = list(db.ratings.aggregate(pipeline))
    if not results:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé ou aucune note")
    return {
        "userId": user_id,
        "favoriteGenres": [{"genre": r["_id"], "count": r["count"]} for r in results]
    }

@app.get("/users/{user_id}/recommend")
def recommend(user_id: int, limit: int = 10, current_user=Depends(get_current_user)):
    check_access(current_user, user_id)
    profile_pipeline = [
        { "$match": { "userId": user_id, "rating": { "$gte": 3.5 } } },
        { "$lookup": {
            "from": "movies",
            "localField": "movieId",
            "foreignField": "movieId",
            "as": "movieInfo"
        }},
        { "$unwind": "$movieInfo" },
        { "$unwind": "$movieInfo.genres" },
        { "$group": { "_id": "$movieInfo.genres", "count": { "$sum": 1 } } },
        { "$sort": { "count": -1 } },
        { "$limit": 1 }
    ]
    profile = list(db.ratings.aggregate(profile_pipeline))
    if not profile:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé ou aucune note")
    top_genre = profile[0]["_id"]
    seen = [doc["movieId"] for doc in db.ratings.find({"userId": user_id}, {"movieId": 1})]
    reco_pipeline = [
        { "$match": { "genres": top_genre, "movieId": { "$nin": seen } } },
        { "$limit": 50 },
        { "$lookup": {
            "from": "ratings",
            "localField": "movieId",
            "foreignField": "movieId",
            "as": "ratingInfo"
        }},
        { "$unwind": "$ratingInfo" },
        { "$group": {
            "_id": "$movieId",
            "title": { "$first": "$title" },
            "genres": { "$first": "$genres" },
            "avgRating": { "$avg": "$ratingInfo.rating" },
            "totalVotes": { "$sum": 1 }
        }},
        { "$match": { "totalVotes": { "$gte": 10 } } },
        { "$sort": { "avgRating": -1 } },
        { "$limit": limit }
    ]
    results = list(db.movies.aggregate(reco_pipeline))
    return {
        "userId": user_id,
        "topGenre": top_genre,
        "recommendations": [
            {
                "movieId": r["_id"],
                "title": r["title"],
                "genres": r["genres"],
                "avgRating": round(r["avgRating"], 2),
                "totalVotes": r["totalVotes"]
            } for r in results
        ]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)