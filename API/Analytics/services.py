from .mongo_client import get_atenciones_collection, get_encuestas_collection


def guardar_encuesta(datos):
    documento = dict(datos)
    documento["id_fecha"] = documento["id_fecha"].isoformat()
    resultado = get_encuestas_collection().insert_one(documento)
    return str(resultado.inserted_id)


def listar_encuestas(filtro=None):
    return list(
        get_encuestas_collection().find(
            filtro or {},
            {"_id": 1, "id_encuesta": 1, "id_fecha": 1, "id_paciente": 1,
             "id_patologia": 1, "puntuacion_general": 1,
             "score_atencion_medica": 1, "tiempo_espera_minutos": 1,
             "score_trato_personal": 1, "score_consulta_doctor": 1,
             "resolucion_dudas_val": 1, "comentario": 1},
        )
    )


def obtener_encuesta(filtro):
    return get_encuestas_collection().find_one(filtro)


def actualizar_encuesta(filtro, cambios):
    return get_encuestas_collection().update_one(
        filtro,
        {"$set": dict(cambios)},
    )


def eliminar_encuesta(filtro):
    return get_encuestas_collection().delete_one(filtro)


def guardar_atencion(datos):
    documento = dict(datos)
    documento["id_fecha"] = documento["id_fecha"].isoformat()
    collection = get_atenciones_collection()
    resultado = collection.update_one(
        {"id_atencion": documento["id_atencion"]},
        {"$set": documento},
        upsert=True,
    )
    if resultado.upserted_id is not None:
        return str(resultado.upserted_id)
    existente = collection.find_one(
        {"id_atencion": documento["id_atencion"]},
        {"_id": 1},
    )
    return str(existente["_id"])


def guardar_atencion_desde_modelo(atencion):
    from apps.catalogos.Detalle_Tratamiento.models import DetalleTratamiento
    from apps.catalogos.Solicitud_Examenes.models import SolicitudDeExamenes

    paciente_patologia = atencion.id_paciente_patologia
    return guardar_atencion({
        "id_atencion": atencion.pk,
        "id_fecha": atencion.fecha_atencion,
        "id_paciente": paciente_patologia.id_paciente_id,
        "id_medico": atencion.id_medico_id,
        "id_patologia": paciente_patologia.id_patologia_cronica_id,
        "asistio_val": int(atencion.asistio),
        "duracion_consulta_minutos": 15,
        "tiempo_espera_real_minutos": 10,
        "receto_medicamento_flag": int(
            DetalleTratamiento.objects.filter(
                id_tratamiento__id_atencion_cronico_id=atencion.pk,
            ).exists()
        ),
        "solicito_examen_flag": int(
            SolicitudDeExamenes.objects.filter(
                id_atencion_cronico_id=atencion.pk,
            ).exists()
        ),
    })


def listar_atenciones(filtro=None):
    return list(
        get_atenciones_collection().find(
            filtro or {},
            {
                "_id": 1,
                "id_atencion": 1,
                "id_fecha": 1,
                "id_paciente": 1,
                "id_medico": 1,
                "id_patologia": 1,
                "asistio_val": 1,
                "duracion_consulta_minutos": 1,
                "tiempo_espera_real_minutos": 1,
                "receto_medicamento_flag": 1,
                "solicito_examen_flag": 1,
            },
        )
    )
