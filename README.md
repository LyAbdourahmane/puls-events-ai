# 🎉 **Puls-Events AI — Système RAG Culturel (Paris)**

_Recommandations d’événements culturels basées sur OpenAgenda + Mistral + FAISS_

---

# **Objectif du projet**

Puls-Events AI est un assistant intelligent capable de :

- récupérer automatiquement les événements culturels de Paris via **OpenAgenda**
- les nettoyer, vectoriser et indexer dans **FAISS**
- répondre aux questions des utilisateurs grâce à un système **RAG** (Retrieval-Augmented Generation)
- générer des réponses naturelles via **Mistral AI**
- exposer le tout via une **API FastAPI**
- offrir une interface utilisateur moderne via **Streamlit**
- collecter du **feedback utilisateur** pour améliorer le système

Ce projet constitue un pipeline complet, industrialisable et démontrable.

---

# **Architecture globale**

```
                ┌────────────────────────┐
                │     OpenAgenda API     │
                └─────────────┬──────────┘
                              │
                              ▼
                (fetch_openagenda_events)
                              │
                              ▼
                ┌────────────────────────┐
                │  CSV nettoyé (data/)   │
                └─────────────┬──────────┘
                              │
                              ▼
                ┌────────────────────────┐
                │Vectorisation (Mistral) │
                └─────────────┬──────────┘
                              │
                              ▼
                ┌────────────────────────┐
                │ Index FAISS (vectorDB) │
                └─────────────┬──────────┘
                              │
                              ▼
                ┌────────────────────────┐
                │     API FastAPI        │
                └─────────────┬──────────┘
                              │
                              ▼
                ┌────────────────────────┐
                │  Interface Streamlit   │
                └────────────────────────┘
```

---

# **Données utilisées**

### Source :

➡️ **OpenAgenda** (Agenda UID configurable via `.env`)

### Filtrage appliqué :

- localisation : Paris (lat/lng + rayon 20 km)
- période : 1 an d’historique + 1 an futur
- description FR uniquement
- suppression des événements sans description
- suppression des doublons

### Format final CSV :

| id | title | description | date_end | city | text_for_rag |

---

# **Pipeline RAG**

Le pipeline RAG repose sur :

### 🔹 1. **Vectorisation**

- modèle : `sentence-transformers/all-MiniLM-L6-v2`
- découpage en chunks
- embeddings stockés dans FAISS

### 🔹 2. **Recherche sémantique**

- FAISS (Index FlatL2)
- récupération des 5 chunks les plus pertinents

### 🔹 3. **Génération augmentée**

- modèle Mistral (small ou large)
- prompt structuré
- réponse + sources

---

# **API FastAPI**

L’API expose :

- `/chat` → question → réponse augmentée
- `/rebuild` → reconstruit toute la base vectorielle
- `/` → endpoint racine
- documentation Swagger : `/docs`

### Sécurité :

- clé API utilisateur
- clé API admin pour `/rebuild`

### Fonctionnalités :

- reconstruction automatique au démarrage
- logs propres et structurés
- gestion des erreurs

---

# **Interface Streamlit**

Fonctionnalités :

- chat moderne avec avatars
- effet machine à écrire
- sélection du modèle (rapide / précis)
- affichage des sources
- cache des requêtes
- historique limité
- feedback utilisateur (thumbs up/down)
- stockage du feedback en SQLite

L’interface consomme uniquement l’API FastAPI.

---

# **Base de feedback utilisateur**

Stockée dans :

```
data/feedback.db
```

Modèle SQLAlchemy :

- question
- réponse
- sources
- label (positive/negative)
- commentaire optionnel
- timestamp

---

# **Dockerisation**

### Dockerfile (API uniquement)

- basé sur `python:3.12-slim`
- installation via `uv sync`
- lancement via `python app.py`

### .dockerignore

- ignore data, vectorDB, logs, env, caches, IDE, etc.

---

# **Installation & Exécution**

## 1️⃣ Cloner le projet

```bash
git clone https://github.com/LyAbdourahmane//puls-events-ai.git
cd puls-events-ai
```

## 2️⃣ Configurer l’environnement

Créer un fichier `.env` :

```
API_KEY=ta_cle_user
API_KEY_ADMIN=ta_cle_admin
OPENAGENDA_API_KEY=ta_cle_openagenda
OPENAGENDA_UID=82290100
URL_API=http://localhost:8000/chat
DATA_DIR=data
DATA_FILE=events_raw
VECTORDB_PATH=vectorDB
```

## 3️⃣ Installer les dépendances (uv)

```bash
uv sync
```

## 4️⃣ Lancer l’API

```bash
python app.py
```

Accéder à la doc :

```
http://localhost:8000/docs
```

## 5️⃣ Lancer l’interface Streamlit

```bash
streamlit run interface.py
```

---

# 📡 **Endpoints API**

## `POST /chat`

**Entrée :**

```json
{
  "question": "Quels événements religieux à Paris ?",
  "model_size": "small"
}
```

**Sortie :**

```json
{
  "answer": "...",
  "sources": "..."
}
```

---

## `POST /rebuild` (admin only)

Reconstruit :

- CSV OpenAgenda
- base vectorielle FAISS

---

# 👤 **Auteur**

**Abdourahamane LY**  
Spécialiste RAG, MLOps, NLP, Computer Vision
