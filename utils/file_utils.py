import os
import shutil
import logging

def delete_file(path):
    if os.path.exists(path):
        os.remove(path)
        logging.info(f"Fichier supprimé : {path}")

def delete_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)
        logging.info(f"Dossier supprimé : {path}")
