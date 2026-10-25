"""Preprocesamiento de texto de PQRS (idéntico al usado en el notebook de la Fase 2)."""
import re
import unicodedata

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

nltk.download("stopwords", quiet=True)


def quitar_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


# Se conservan las negaciones: «no ha recibido» cambia el sentido de la frase
STOP = {quitar_tildes(w) for w in stopwords.words("spanish")} - {"no", "sin", "ni", "nada"}
STEM = SnowballStemmer("spanish")


def preprocesar(texto: str) -> str:
    t = quitar_tildes(str(texto).lower())
    t = re.sub(r"[^a-z\s]", " ", t)
    return " ".join(STEM.stem(w) for w in t.split() if w not in STOP and len(w) > 1)
