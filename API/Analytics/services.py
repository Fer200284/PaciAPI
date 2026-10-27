from .mongo_client import get_encuestas_collection


def guardar_encuesta(datos):
    documento = dict(datos)
    documento["id_fecha"] = documento["id_fecha"].isoformat()
    resultado = get_encuestas_collection().insert_one(documento)
    return str(resultado.inserted_id)
