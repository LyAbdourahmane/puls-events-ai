import streamlit as st
import requests
import time
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from streamlit_feedback import streamlit_feedback
from utils.feedback_db import Feedback, Base, save_feedback_to_db
from dotenv import load_dotenv

# -----------------------------------------------------------
# --- CONFIGURATION DE LA PAGE & DB ---
st.set_page_config(
    page_title="Puls-Events AI",
    page_icon="🎉",
    layout="centered"
)

# Configuration de la base de données SQLite
DB_PATH = "data/feedback.db"
if not os.path.exists("data"):
    os.makedirs("data")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
# Création des tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

load_dotenv()
# URL de ton API FastAPI
URL_API = os.getenv('URL_API')
CLE_API = os.getenv('API_KEY')
MAX_HISTORY_LENGTH = 20

# -----------------------------------------------------------------------------------
# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
    h1 {
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .stChatInput {
        padding-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------------
# --- INITIALISATION DE L'ÉTAT (Session State) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "query_cache" not in st.session_state:
    st.session_state.query_cache = {}

if "interaction_id" not in st.session_state:
    st.session_state.interaction_id = 0

# Stockage pour le feedback persistant
if "last_response" not in st.session_state:
    st.session_state.last_response = None

# ----------------------------------------------------------------------------------
# --- FONCTIONS UTILITAIRES ---

def stream_text(text):
    """Simule un effet de machine à écrire"""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

# ------------------------------------------------------------------------------------
# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Réglages")
    model_display = st.selectbox("Modèle d'IA", ["Mistral (Rapide)", "Mistral (Précis)"])
    current_model_size = "small" if "Rapide" in model_display else "large"
    
    st.divider()
    
    if st.button("🗑️ Effacer l'historique", type="primary"):
        st.session_state.messages = []
        st.session_state.query_cache = {}
        st.session_state.last_response = None
        st.toast("Mémoire effacée !", icon="🗑️")
        st.success("Mémoire effacée !")
        time.sleep(1)
        st.rerun()

    st.info("(OpenAgenda + Mistral) \n by Abdourahamane LY")

# ---------------------------------------------------------------------------------------
# --- HEADER ---
st.title("🎉 Puls-Events Assistant")
st.caption("Votre guide intelligent pour les événements culturels (Paris).")

if len(st.session_state.messages)==0:
    st.markdown("👋 **Bonjour !** Je suis l'assistant virtuel de recommandation culturelle à Paris. Comment puis-je vous aider aujourd'hui ?")

# --- AFFICHAGE DE L'HISTORIQUE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 Voir les sources"):
                st.text(msg["sources"])

# ----------------------------------------------------------------------------------------------
# --- TRAITEMENT DE L'ENTRÉE UTILISATEUR ---
user_input = st.chat_input("Posez votre question ici...")

if user_input:
    # Ajout et affichage le message utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    # Génération la réponse de l'assistant
    with st.chat_message("assistant", avatar="🤖"):
        response_placeholder = st.empty()
        
        # Vérifier le Cache
        if user_input in st.session_state.query_cache:
            data = st.session_state.query_cache[user_input]
            answer = data["answer"]
            sources_text = data["sources"]
        else:
            # Appel API
            with st.spinner("Recherche des événements..."):
                try:
                    payload = {"question": user_input, "model_size": current_model_size}
                    response = requests.post(URL_API, json=payload, headers = {"X-API-Key": CLE_API}, timeout=60)
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("answer", "Désolé, je n'ai pas trouvé d'information.")
                        sources_text = data.get("sources", "")
                        # Mise en cache
                        st.session_state.query_cache[user_input] = data
                    else:
                        answer, sources_text = "Erreur lors de la connexion à l'IA.", ""
                except Exception as e:
                    answer, sources_text = f"Erreur technique : {e}", ""

        # Affichage animé
        response_placeholder.write_stream(stream_text(answer))
        
        if sources_text:
            with st.expander("📚 Voir les sources"):
                st.text(sources_text)

        # Mise à jour de l'état pour le feedback et l'historique
        st.session_state.messages.append({"role": "assistant", "content": answer, 'sources': sources_text})
        st.session_state.interaction_id += 1
        
        # On sauvegarde les infos de cette réponse pour le widget feedback
        st.session_state.last_response = {
            "question": user_input,
            "answer": answer,
            "sources": sources_text,
            "id": st.session_state.interaction_id
        }
        
        # Limitation historique
        if len(st.session_state.messages) > MAX_HISTORY_LENGTH:
            st.session_state.messages = st.session_state.messages[-MAX_HISTORY_LENGTH:]
        
        st.rerun()


# ----------------------------------------------------------------------------------------------
# --- ZONE DE FEEDBACK (S'affiche après le dernier message) ---

if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.last_response:
    
    last_res = st.session_state.last_response
    inter_id = last_res["id"]
    
    # On crée une clé unique pour le widget
    fb_key = f"feedback_{inter_id}"
    
    st.write("---")
    st.caption("Cette réponse vous a-t-elle aidé ?")
    
    # Utilisation du composant streamlit_feedback
    fb = streamlit_feedback(
        feedback_type="thumbs",
        key=fb_key,
        optional_text_label="[Optionnel] Un commentaire ?"
    )

    # Si l'utilisateur clique sur un pouce
    if fb is not None:
        score_val = fb.get("score")
        comment = fb.get('text', None)
        if score_val in ["👍", "thumbs_up", "up"]:
            label, value = 'positive', 1
        elif score_val in ["👎", "thumbs_down", "down"]:
            label, value = 'negative', 0
        else:
            label, value = None, None
        
        # Enregistrement
        success = save_feedback_to_db(
            question=last_res["question"],
            answer=last_res["answer"],
            sources=last_res["sources"],
            feedback_label=label,
            value=value,
            comment=comment
        )
        
        if success:
            st.toast("Merci pour votre retour !")
            # On réinitialise last_response pour éviter de proposer le feedback en boucle
            st.session_state.last_response = None
            time.sleep(2)
            st.rerun()