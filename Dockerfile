# Image Python légère
FROM python:3.12-slim

# Installons uv (gestionnaire de dépendances moderne)
RUN pip install --no-cache-dir uv

# Définissons le dossier de travail
WORKDIR /app

# Copions les fichiers de configuration uv
COPY pyproject.toml uv.lock ./

# Installons les dépendances via uv
RUN uv sync --no-dev

# 6. Copier le reste du code
COPY . .

# 7. Exposer le port FastAPI
EXPOSE 8000

# 8. Lancer l’API (je gère déjà uvicorn dans app.py)
CMD ["python", "app.py"]
