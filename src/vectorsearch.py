import logging
import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()             
    ]
)

def load_vectorDB(persist_dir: str):
    try:
        db_path = Path(persist_dir).resolve()
        logging.debug(f"Chargement de la base vectorielle depuis : {db_path}")

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        db = FAISS.load_local(
            folder_path=db_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )

        logging.info("Base FAISS chargée avec succès")
        return db
    except Exception as e:
        logging.error(f"Erreur lors du chargement de la base FAISS : {e}")
        return None

def search(query: str, persist_dir: str, top_k: int = 5):
    try:
        logging.debug(f"Recherche lancée pour la requête : {query}")
        db = load_vectorDB(persist_dir)
        if not db:
            logging.error("Impossible d'effectuer la recherche : base FAISS non chargée")
            return []

        retriever = db.as_retriever(search_kwargs={"k": top_k})
        results = retriever.invoke(query)

        logging.info(f"{len(results)} chunks récupérés pour la requête")
        return results  # le texte principal est dans page_content
    except Exception as e:
        logging.error(f"Erreur lors de la recherche dans la base FAISS : {e}")
        return []
