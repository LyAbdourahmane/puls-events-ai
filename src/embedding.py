import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,  # Niveau minimum affiché
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()                # Affiche dans la console
    ]
)

def transform_csv_to_document(df: pd.DataFrame) -> List[Any]:
    try:
        documents = []
        for _, row in df.iterrows():
            doc = Document(
                page_content=row['text_for_rag'],
                metadata={
                    'id': row['id'],
                    'title': row['title'],
                    'city': row['city'],
                    'date_end': row['date_end']
                }
            )
            documents.append(doc)
        logging.info(f"{len(documents)} documents transformés avec succès")
        return documents
    except Exception as e:
        logging.error(f"Erreur lors de la transformation CSV → Document : {e}")
        return []

def documents_to_chunks(df: pd.DataFrame, chunk_size: int, chunk_overlap: int) -> List[Any]:
    try:
        documents = transform_csv_to_document(df)
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_documents(documents)
        logging.info(f"{len(chunks)} chunks générés avec succès")
        return chunks
    except Exception as e:
        logging.error(f"Erreur lors du découpage des documents : {e}")
        return []

def data_to_embeddings(df: pd.DataFrame, persist_dir: str, chunk_size: int = 800, chunk_overlap: int = 120):
    try:
        chunks = documents_to_chunks(df, chunk_size, chunk_overlap)
        logging.info(f"Génération des embeddings pour {len(chunks)} chunks...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        os.makedirs(persist_dir, exist_ok=True)
        db = FAISS.from_documents(chunks, embeddings)
        db.save_local(persist_dir)
        logging.info(f"Base FAISS sauvegardée dans {persist_dir}")
    except Exception as e:
        logging.error(f"Erreur lors de la génération des embeddings : {e}")
