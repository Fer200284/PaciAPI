import os
from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured
from pymongo import MongoClient


@lru_cache(maxsize=1)
def get_mongo_client():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ImproperlyConfigured(
            "La variable de entorno MONGODB_URI no está configurada."
        )
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def get_evaluaciones_collection():
    return get_mongo_client()["paciencare_db"]["evaluaciones_pacientes"]
