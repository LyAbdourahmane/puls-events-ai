# ---------------------------------------------------------------------------------------------------------------------------------#
import logging
import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from src.rag_chain import rag_response
from src.data_loader import load_csv
from src.embedding import data_to_embeddings
from utils.pydantic_utils import QueryRequest
from src.openagenda_loader import fetch_openagenda_events, save_events_to_csv
from utils.file_utils import delete_file, delete_folder
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Configuration du logger
logging.getLogger("httpx").setLevel(logging.WARNING) 
logging.getLogger("httpcore").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
        # ,logging.FileHandler("rag_api.log") pour le moment je ne sauvegarde pas
    ]
)

# -------------------------------------------------------------------
# Configuration externalisée (via .env )
load_dotenv()
API_KEY = os.getenv('API_KEY')
API_KEY_ADMIN = os.getenv("API_KEY_ADMIN")
api_key_header = APIKeyHeader(name="X-API-Key")
VECTORDB_PATH = os.getenv("VECTORDB_PATH", "vectorDB")
DATA_DIR = os.getenv("DATA_DIR", "data")
DATA_FILE = os.getenv("DATA_FILE", "events_raw")


# -------------------------------------------------------------------
# Initialisation de l'API
app = FastAPI(
    title="Puls-Events AI API",
    description="API de recommandation culturelle basée sur RAG (Mistral + OpenAgenda)",
    version="1.0.0"
)


# -------------------------------------------------------------------
# Fonctions utilitaires

def _verify_api_chat(x_api_key: str = Security(api_key_header)):
    """Sécurité pour l'endpoint /chat (user ou admin)"""
    if x_api_key not in {API_KEY, API_KEY_ADMIN}:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _verify_api_admin(api_key: str = Security(api_key_header)):
    '''pour la partie rebuild (admin)'''
    if api_key != API_KEY_ADMIN:
        raise HTTPException(status_code=403, detail = "Admin only")


def launch_the_rag():
    try:
        logging.debug("Initialisation du système RAG au démarrage...")
        data = load_csv(data_dir=DATA_DIR, data_name=DATA_FILE)
        logging.info(f"{len(data)} lignes chargées depuis {DATA_FILE}.csv")

        data_to_embeddings(data, persist_dir=VECTORDB_PATH)
        logging.info("Base vectorielle initialisée avec succès")
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation du RAG : {e}")
        raise HTTPException(status_code=503, detail="Système RAG indisponible au démarrage")


# -------------------------------------------------------------------
# Événement de démarrage
@app.on_event("startup")
async def startup_event():
    launch_the_rag()


# -------------------------------------------------------------------
# Endpoint racine
@app.get("/")
async def home():
    logging.info("Endpoint racine appelé")
    return {
        "message": "API de recommandation culturelle basée sur RAG (Mistral + OpenAgenda)",
        "endpoints": ["/chat", "/rebuild"]
    }


# -------------------------------------------------------------------
# Endpoint principal : chat
@app.post("/chat")
async def chat_endpoint(request: QueryRequest, api_key: str = Security(_verify_api_chat)):
    query = request.question
    model_choice = request.model_size
    logging.debug(f"Nouvelle requête utilisateur (model:{model_choice}): {query}")
    try:
        llm_text, results = rag_response(query=query, persist_dir=VECTORDB_PATH, model_size=model_choice)
        if not llm_text:
            raise HTTPException(status_code=503, detail="Système RAG indisponible")

        #structuré pour les sources
        sources_text = "\n--- Sources ---\n" 
        for doc in results: 
            sources_text += f"- {doc.metadata.get('title')} ({doc.metadata.get('city')}, fin: {doc.metadata.get('date_end')})\n"

        return {"answer": llm_text, "sources": sources_text}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Erreur lors du traitement de la requête : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors du traitement")

# -------------------------------------------------------------------
# Endpoint rebuild
@app.post("/rebuild")
async def system_rebuild(api_key: str = Security(_verify_api_admin)):
    logging.info("Reconstruction complète demandée.")

    try:
        # Récupération OpenAgenda
        df = fetch_openagenda_events()
        if df.empty:
            raise HTTPException(status_code=500, detail="Aucune donnée récupérée depuis OpenAgenda")

        # Suppression anciennes données
        delete_file(f"{DATA_DIR}/{DATA_FILE}.csv")
        delete_folder(VECTORDB_PATH)

        # Sauvegarde nouvelles données
        save_events_to_csv(df, DATA_DIR, DATA_FILE)

        # Reconstruction vectorDB
        launch_the_rag()

        return {"info": "Le Système RAG a été rechargé avec succès !"}

    except Exception as e:
        logging.error(f"Erreur lors du rebuild : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors du rebuild")


# -------------------------------------------------------------------
# Démarrage du serveur
if __name__ == "__main__":
    import uvicorn
    logging.info("Démarrage du serveur FastAPI...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
