import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from numbers import Real

from django.utils import timezone as django_timezone


MESES_ES = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)


def _numero(valor):
    if isinstance(valor, bool) or valor is None:
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) else None


def _promedio(evaluaciones, campos):
    valores = []
    for evaluacion in evaluaciones:
        for campo in campos:
            numero = _numero(evaluacion.get(campo))
            if numero is not None:
                valores.append(numero)
                break
    return round(sum(valores) / len(valores), 1) if valores else None


def _etiqueta_satisfaccion(promedio):
    if promedio is None:
        return "Sin registros"
    if promedio >= 4.5:
        return "Muy satisfecho"
    if promedio >= 3.5:
        return "Satisfecho"
    if promedio >= 2.5:
        return "Neutral"
    if promedio >= 1.5:
        return "Insatisfecho"
    return "Muy insatisfecho"


def _promedio_textual_o_satisfaccion(evaluaciones, campos):
    respuestas = [
        str(evaluacion[campo]).strip()
        for evaluacion in evaluaciones
        for campo in campos
        if evaluacion.get(campo) is not None
        and str(evaluacion[campo]).strip()
    ]
    if respuestas and any(_numero(respuesta) is None for respuesta in respuestas):
        return Counter(respuestas).most_common(1)[0][0]
    return _etiqueta_satisfaccion(_promedio(evaluaciones, campos))


def _porcentaje_dudas_resueltas(evaluaciones):
    porcentajes = []
    respuestas = []
    for evaluacion in evaluaciones:
        porcentaje = _numero(evaluacion.get("dudas_resueltas_porcentaje"))
        if porcentaje is not None:
            porcentajes.append(porcentaje)
            continue
        respuesta = evaluacion.get("dudas_resueltas")
        if isinstance(respuesta, bool):
            respuestas.append(respuesta)
        elif isinstance(respuesta, Real) and respuesta in (0, 1):
            respuestas.append(bool(respuesta))
        elif isinstance(respuesta, str):
            respuesta_normalizada = respuesta.strip().lower()
            if respuesta_normalizada in {"si", "sí", "true", "1"}:
                respuestas.append(True)
            elif respuesta_normalizada in {"no", "false", "0"}:
                respuestas.append(False)

    if porcentajes:
        return round(sum(porcentajes) / len(porcentajes), 1)
    if respuestas:
        return round(sum(respuestas) / len(respuestas) * 100, 1)
    return 0.0


def crear_reporte_gerencial(evaluaciones, ahora=None):
    ahora = ahora or django_timezone.localtime()
    periodo = f"{MESES_ES[ahora.month - 1]} {ahora.year}"
    puntuaciones = [
        (evaluacion, _numero(evaluacion.get("puntuacion")))
        for evaluacion in evaluaciones
    ]
    puntuaciones_validas = [
        (evaluacion, puntuacion)
        for evaluacion, puntuacion in puntuaciones
        if puntuacion is not None
    ]
    promedio_general = (
        round(sum(puntuacion for _, puntuacion in puntuaciones_validas) /
              len(puntuaciones_validas), 1)
        if puntuaciones_validas
        else 0.0
    )
    distribucion = Counter(
        int(puntuacion)
        for _, puntuacion in puntuaciones_validas
        if puntuacion in {1, 2, 3, 4, 5}
    )
    porcentaje_alto = (
        round(
            sum(distribucion[puntuacion] for puntuacion in (4, 5))
            / len(puntuaciones_validas)
            * 100,
            1,
        )
        if puntuaciones_validas
        else 0.0
    )

    patologias = defaultdict(list)
    pacientes_por_patologia = defaultdict(set)
    pacientes_sin_id_por_patologia = Counter()
    for evaluacion, puntuacion in puntuaciones:
        patologia = evaluacion.get("patologia_cronica")
        if isinstance(patologia, str) and patologia.strip():
            nombre_patologia = patologia.strip()
            patologias[nombre_patologia].append(puntuacion)
            paciente_id = evaluacion.get("paciente_id")
            if paciente_id is None or str(paciente_id).strip() == "":
                pacientes_sin_id_por_patologia[nombre_patologia] += 1
            else:
                pacientes_por_patologia[nombre_patologia].add(str(paciente_id))

    desglose_patologias = []
    for patologia, calificaciones in sorted(patologias.items()):
        validas = [calificacion for calificacion in calificaciones if calificacion is not None]
        desglose_patologias.append({
            "patologia": patologia,
            "total_pacientes": (
                len(pacientes_por_patologia[patologia])
                + pacientes_sin_id_por_patologia[patologia]
            ),
            "satisfaccion_promedio": (
                round(sum(validas) / len(validas), 1) if validas else 0.0
            ),
        })

    promedio_atencion = _promedio(
        evaluaciones,
        ("atencion_medica", "promedio_atencion_medica"),
    )
    espera_promedio = _promedio(
        evaluaciones,
        ("tiempo_espera_minutos", "tiempo_espera_promedio_minutos"),
    )
    trato_promedio = _promedio_textual_o_satisfaccion(
        evaluaciones,
        ("trato_personal", "trato_personal_promedio"),
    )

    return {
        "periodo": periodo,
        "total_evaluaciones": len(evaluaciones),
        "puntuacion_promedio": promedio_general,
        "porcentaje_satisfaccion_alta": porcentaje_alto,
        "indicadores_clave": {
            "promedio_atencion_medica": _etiqueta_satisfaccion(promedio_atencion),
            "tiempo_espera_promedio_minutos": espera_promedio or 0,
            "trato_personal_promedio": trato_promedio,
            "dudas_resueltas_porcentaje": _porcentaje_dudas_resueltas(evaluaciones),
        },
        "desglose_patologias_cronicas": desglose_patologias,
        "distribucion_calificaciones": {
            "excelente_5_estrellas": distribucion[5],
            "muy_bueno_4_estrellas": distribucion[4],
            "bueno_3_estrellas": distribucion[3],
            "malo_2_estrellas": distribucion[2],
            "muy_malo_1_estrella": distribucion[1],
        },
        "ultima_actualizacion": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
