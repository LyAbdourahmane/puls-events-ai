import logging
from pathlib import Path
import pandas as pd

# Configuration du logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(message)s"
)

def load_csv(data_dir: str, data_name: str) -> pd.DataFrame:
    try:
        data_path = Path(data_dir).resolve()
        logging.debug(f"Dossier de Données : {data_path}")

        df = pd.read_csv(f"{data_path}/{data_name}.csv")
        logging.info(f"✓ Le fichier de {df.shape[0]} lignes et de {df.shape[1]} colonnes a été chargé avec SUCCÈS !")

        return df
    except Exception as e:
        logging.error(f"Erreur : {e}")
