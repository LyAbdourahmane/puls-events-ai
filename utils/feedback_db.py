import os
import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

# ----------------------------------------------------------------------------
# LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ----------------------------------------------------------------------------
# CONFIG BDD
DATABASE_DIR = "data"
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/feedback.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

Base = declarative_base()

# ----------------------------------------------------------------------------
# TABLE FEEDBACK
class Feedback(Base):
    __tablename__ = "feedback_users"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    sources = Column(Text)
    feedback = Column(String(20))        # "positive" / "negative"
    feedback_value = Column(Integer)     # 1 = positif, 0 = négatif
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    comment = Column(Text)

# ----------------------------------------------------------------------------
# CRÉATION DES TABLES (ne modifie pas les tables existantes)
try:
    Base.metadata.create_all(engine)
    logging.info("Base et tables initialisées (create_all exécuté)")
except SQLAlchemyError as e:
    logging.exception("Erreur lors de la création des tables")

# ----------------------------------------------------------------------------
# SESSION
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----------------------------------------------------------------------------
# FONCTION D'INSERT ROBUSTE
def save_feedback_to_db(question, answer, sources, feedback_label, value, comment=None):
    """
    Enregistre un feedback dans la base.
    Retourne True si OK, False sinon.
    """
    if not question:
        logging.warning("Tentative d'enregistrement avec question vide")
        return False
    if value not in (0, 1):
        logging.warning("Valeur de feedback invalide: %s", value)
        return False

    db = SessionLocal()
    try:
        entry = Feedback(
            question=question,
            answer=answer,
            sources=str(sources),
            feedback=feedback_label,
            feedback_value=value,
            comment=comment
        )
        db.add(entry)
        db.commit()
        logging.info("Feedback inséré (question=%s, value=%s)", question[:50], value)
        return True
    except Exception as e:
        logging.exception("Erreur DB lors de l'insertion du feedback")
        try:
            db.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            db.close()
        except Exception:
            pass
