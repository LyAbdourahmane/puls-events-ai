# src/openagenda_loader.py

import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta

# Désactivation des logs verbeux de requests / urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

API_KEY_AGENDA = os.getenv("OPENAGENDA_API_KEY")
AGENDA_UID = os.getenv("OPENAGENDA_UID", "82290100")

BASE_URL = f"https://api.openagenda.com/v2/agendas/{AGENDA_UID}/events"

LATITUDE = 48.8566
LONGITUDE = 2.3522
RADIUS_KM = 20

DATE_START = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
DATE_END = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")


def fetch_openagenda_events():
    """Récupère et nettoie les événements OpenAgenda, sans logs verbeux."""
    logging.info(f"Collecte des événements depuis OpenAgenda (agenda {AGENDA_UID})...")

    events_data = []
    offset = 0

    try:
        while True:
            params = {
                "key": API_KEY_AGENDA,
                "lat": LATITUDE,
                "lng": LONGITUDE,
                "dist": RADIUS_KM,
                "timings[gte]": DATE_START,
                "timings[lte]": DATE_END,
                "detailed": 1,
                "offset": offset
            }

            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            current_events = data.get("events", [])
            if not current_events:
                break

            for event in current_events:
                title = event.get("title", {}).get("fr", "Titre inconnu")
                description = (
                    event.get("longDescription", {}).get("fr")
                    or event.get("description", {}).get("fr", "")
                )

                location = event.get("location", {})
                timings = event.get("timings", [])

                events_data.append({
                    "id": event.get("uid"),
                    "title": title,
                    "description": description,
                    "date_end": timings[0].get("end") if timings else None,
                    "city": location.get("city"),
                    "text_for_rag": (
                        f"Titre: {title}. Description: {description}. "
                        f"Ville: {location.get('city')}"
                    )
                })

            # Pagination
            if len(current_events) < 20:
                break
            offset += len(current_events)

    except Exception as e:
        logging.error(f"Erreur OpenAgenda : {e}")
        return pd.DataFrame()

    # Conversion en DataFrame
    df = pd.DataFrame(events_data)

    if df.empty:
        logging.warning("Aucun événement récupéré.")
        return df

    # Nettoyage
    df.drop_duplicates(subset=["id"], inplace=True)
    df = df[df["description"].str.len() > 25]

    logging.info(f"Collecte terminée : {len(df)} événements prêts.")
    return df


def save_events_to_csv(df, data_dir, data_file):
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f"{data_file}.csv")
    df.to_csv(csv_path, index=False)
    logging.info(f"Données sauvegardées dans {csv_path}")
