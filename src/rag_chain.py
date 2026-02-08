import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from src.vectorsearch import search
import os

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,  # Niveau minimum affiché
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler() 
    ]
)

load_dotenv()
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

TEMPLATE = """
Tu es l'assistant virtuel expert de "Puls-Events". Ta mission est de recommander des événements culturels.

Voici les informations sur les événements disponibles (Contexte) :
---------------------
{context}
---------------------

Question de l'utilisateur : 
{question}

CONSIGNES DE RÉPONSE (À RESPECTER IMPÉRATIVEMENT) :
1. Si aucune information dans le contexte ne répond à la question, dis simplement que tu ne sais pas.
2. Ton ton doit être engageant, chaleureux et dynamique.
3. FORMATAGE OBLIGATOIRE :
   - Ne fais PAS de gros paragraphes compacts.
   - Utilise une Liste à puces pour chaque événement.
   - Mets le Titre de l'événement en Gras.
   - Utilise des émojis pour chaque ligne (Date, Lieu, Prix/Détails).
   - Finis par une courte phrase invitante.

Réponse structurée :
"""

#----------------------------------------------------------------------------------
# configuration du llm
def config_llm(model_size='small'):
    try:
        if model_size == 'small':
            model_name = 'mistral-small-latest'
        else:
            model_name = 'mistral-large-latest'

        logging.debug("Initialisation du LLM Mistral...")
        llm = ChatMistralAI(
            mistral_api_key=MISTRAL_API_KEY,
            model=model_name,
            temperature=0.2
        )
        prompt = ChatPromptTemplate.from_template(TEMPLATE)
        logging.info("LLM et prompt configurés avec succès")
        return llm, prompt
    except Exception as e:
        logging.error(f"Erreur lors de la configuration du LLM : {e}")
        return None, None


#-----------------------------------------------------------------------------
# construction du rag
def rag_chain(prompt: str, llm):
    try:
        logging.debug("Construction du pipeline RAG...")
        rag_system = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | llm
        )
        logging.info("Pipeline RAG construit avec succès")
        return rag_system
    except Exception as e:
        logging.error(f"Erreur lors de la construction du pipeline RAG : {e}")
        return None


#-------------------------------------------------------------------------------
# genration de reponse par RAG
def rag_response(query: str, persist_dir: str, model_size: str='small'):
    try:
        logging.debug(f"Nouvelle requête utilisateur : {query}")
        llm, prompt = config_llm(model_size)
        if not llm or not prompt:
            logging.error("LLM ou prompt non initialisé")
            return None, None

        context = search(query, persist_dir)
        logging.info(f"{len(context)} chunks récupérés depuis la base vectorielle")

        # Concaténer les contenus des chunks
        context_text = "\n\n".join([doc.page_content for doc in context])

        rag = rag_chain(prompt, llm)
        if not rag:
            logging.error("Pipeline RAG non initialisé")
            return None, context

        response = rag.invoke({"context": context_text, "question": query})
        logging.info(f"Réponse générée avec succès par le LLM (Mistral-{model_size})")

        return response.content, context
    except Exception as e:
        logging.error(f"Erreur lors de la génération de la réponse RAG : {e}")
        return None, None
