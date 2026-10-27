from .mongo_client import get_encuestas_collection


def guardar_encuesta(datos):
    resultado = get_encuestas_collection().insert_one(dict(datos))
    return str(resultado.inserted_id)
