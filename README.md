# 🎬 CineMatch — Système de Recommandation de Films

CineMatch est une application web de recommandation de films basée sur les notes des utilisateurs.
Elle utilise **FastAPI** pour le backend, **MongoDB** pour la base de données, et un frontend en **HTML/CSS/JS**.

> 📸 *Captures d'écran du projet :*

![Page d'accueil](screenshots/accueil.png)
![Page Profil](screenshots/profil.png)
![Recommandations](screenshots/recommandations.png)
![Panneau Admin](screenshots/admin.png)

---

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- [Python 3.10+](https://www.python.org/downloads/)
- [MongoDB Community Server](https://www.mongodb.com/try/download/community)
- [MongoDB Compass](https://www.mongodb.com/try/download/compass) *(optionnel, interface graphique)*
- [Git](https://git-scm.com/downloads)

---

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone https://github.com/votre-username/cinematch.git
cd cinematch
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Démarrer MongoDB

**Windows :**
```bash
net start MongoDB
```

**Mac/Linux :**
```bash
sudo systemctl start mongod
```

### 4. Importer les données MovieLens

Téléchargez le dataset MovieLens depuis :
👉 https://grouplens.org/datasets/movielens/25m/

Placez les fichiers CSV dans le dossier du projet :
- `movie.csv`
- `rating.csv`
- `tag.csv`
- `link.csv`

Puis importez les données dans MongoDB dans cet ordre :

```bash
python import_movies.py
python import_ratings.py
python import_tags.py
```

### 5. Créer le premier compte Admin

Le compte admin par défaut est créé automatiquement au premier lancement :

| Champ | Valeur |
|-------|--------|
| Username | `admin` |
| Password | `admin123` |

> ⚠️ Changez le mot de passe après la première connexion !

Ou mettez à jour manuellement dans MongoDB Compass :
```javascript
db.users.updateOne(
  { "username": "votre_username" },
  { $set: { "role": "admin" } }
)
```

---

## ▶️ Lancer le projet

Ouvrez **deux terminaux** dans le dossier du projet :

### Terminal 1 — Lancer l'API FastAPI

```bash
python main.py
```

✅ L'API tourne sur : http://localhost:8000
📄 Documentation Swagger : http://localhost:8000/docs

### Terminal 2 — Lancer le serveur frontend

```bash
python -m http.server 5500
```

✅ Ouvrez dans le navigateur : **http://localhost:5500**

> ⚠️ N'ouvrez **pas** le fichier HTML directement (`file:///...`), utilisez toujours `http://localhost:5500`

---

## 🗂️ Structure du projet

```
cinematch/
│
├── main.py                 # API FastAPI (backend)
├── import_movies.py        # Script import films
├── import_ratings.py       # Script import notes
├── import_tags.py          # Script import tags
├── index.html              # Frontend (HTML/CSS/JS)
├── requirements.txt        # Dépendances Python
├── screenshots/            # Captures d'écran
│   ├── accueil.png
│   ├── profil.png
│   ├── recommandations.png
│   └── admin.png
└── README.md               # Documentation
```

---

## 🔧 Configuration

Le fichier `main.py` contient les paramètres de connexion MongoDB :

```python
client = MongoClient("mongodb://localhost:27017/")
db = client["moviesdb"]
```

Si votre MongoDB tourne sur un port différent, modifiez cette ligne.

---

## 👥 Fonctionnalités

| Fonctionnalité | User | Admin |
|---|---|---|
| Voir le Top 20 films | ✅ | ✅ |
| Voir son profil (genres préférés) | ✅ | ✅ |
| Recevoir des recommandations personnalisées | ✅ | ✅ |
| Voir le profil de tous les utilisateurs | ❌ | ✅ |
| Voir les recommandations de tous les utilisateurs | ❌ | ✅ |
| Panneau d'administration complet | ❌ | ✅ |

---

## 🛠️ Résolution de problèmes fréquents

### ❌ "Impossible de contacter le serveur"
- Vérifiez que `python main.py` tourne dans un terminal
- Vérifiez que MongoDB est démarré :
```bash
net start MongoDB
```
- Ouvrez le site via `http://localhost:5500` et **pas** via `file:///`

### ❌ Erreur bcrypt / passlib
```bash
pip uninstall bcrypt -y
pip install bcrypt==4.0.1
```

### ❌ Warnings Pylance dans VS Code
Ce sont des warnings d'éditeur normaux, pas des erreurs réelles.
Pour les supprimer : `Ctrl+Shift+P` → `Python: Select Interpreter` → choisir Python 3.12

### ❌ Page blanche ou erreur CORS
- Assurez-vous d'utiliser `http://localhost:5500` et non `file:///`
- Vérifiez que les deux terminaux (API + serveur frontend) sont bien lancés

### ❌ Recommandations lentes
Ajoutez des index MongoDB pour accélérer les requêtes :
```javascript
db.ratings.createIndex({ "userId": 1 })
db.ratings.createIndex({ "movieId": 1 })
db.movies.createIndex({ "genres": 1 })
db.movies.createIndex({ "movieId": 1 })
```

---

## 📦 Dépendances (`requirements.txt`)

```
fastapi
uvicorn
pymongo
pydantic
python-jose[cryptography]
bcrypt==4.0.1
python-multipart
```

---

## 🗄️ Base de données

### Collections MongoDB (`moviesdb`)

| Collection | Description |
|------------|-------------|
| `movies` | Films (movieId, title, genres) |
| `ratings` | Notes des utilisateurs (userId, movieId, rating) |
| `tags` | Tags des films |
| `users` | Comptes utilisateurs (username, password hashé, role) |

### Exporter / Importer la base de données

**Exporter (sur votre machine) :**
```bash
mongodump --db moviesdb --out ./backup
```

**Importer (sur une autre machine) :**
```bash
mongorestore --db moviesdb ./backup/moviesdb
```

---

## 🔐 Sécurité

- Les mots de passe sont hashés avec **bcrypt**
- L'authentification utilise des tokens **JWT**
- Les routes sensibles sont protégées par rôle (`user` / `admin`)
- Un utilisateur normal ne peut accéder qu'à ses propres données

---

## 📝 Licence

Ce projet est réalisé à des fins éducatives.