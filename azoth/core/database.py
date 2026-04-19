"""TinyDB wrapper for transcription storage."""

import os
from datetime import datetime
from tinydb import TinyDB

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transcricoes.json")


class TranscriptionDB:
    def __init__(self, path=DB_PATH):
        self.db = TinyDB(path)

    def save(self, origin, title, text):
        self.db.insert({
            "origem": origin,
            "titulo": title,
            "texto": text,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def get_all(self):
        return self.db.all()

    def delete(self, doc_id):
        self.db.remove(doc_ids=[doc_id])
