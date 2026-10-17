import math
import re
import unicodedata
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


def _normalizar_campo(campo):
    texto = unicodedata.normalize("NFKD", str(campo))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def _campos_evaluacion(evaluacion):
    if isinstance(evaluacion, dict):
        pregunta = next(
            (
                valor
                for clave, valor in evaluacion.items()
                if _normalizar_campo(clave) in {"pregunta", "question"}
            ),
            None,
        )
        respuesta = next(
            (
                valor
                for clave, valor in evaluacion.items()
                if _normalizar_campo(clave) in {"respuesta", "answer", "valor", "value"}
            ),
            None,
        )
        if isinstance(pregunta, str) and respuesta is not None:
            yield pregunta, respuesta

        for campo, valor in evaluacion.items():
            if isinstance(valor, (dict, list)):
                yield from _campos_evaluacion(valor)
            else:
                yield campo, valor
    elif isinstance(evaluacion, list):
        for elemento in evaluacion:
            yield from _campos_evaluacion(elemento)


def _obtener_valor(evaluacion, campos, pistas=()):
    campos_normalizados = tuple(_normalizar_campo(campo) for campo in campos)
    pistas_normalizadas = tuple(_normalizar_campo(pista) for pista in pistas)
    encontrados = list(_campos_evaluacion(evaluacion))

    for campo in campos_normalizados:
        for nombre, valor in encontrados:
            if _normalizar_campo(nombre) == campo and valor is not None:
                return valor

    for pista in pistas_normalizadas:
        for nombre, valor in encontrados:
            if pista in _normalizar_campo(nombre) and valor is not None:
                return valor

    return None


def _promedio(evaluaciones, campos, pistas=()):
    valores = []
    for evaluacion in evaluaciones:
        numero = None
        for campo in campos:
            numero = _numero(_obtener_valor(evaluacion, (campo,)))
            if numero is not None:
                break
        if numero is None and pistas:
            numero = _numero(_obtener_valor(evaluacion, (), pistas))
        if numero is not None:
            valores.append(numero)
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
    respuestas = []
    puntuaciones = []
    for evaluacion in evaluaciones:
        respuesta = _obtener_valor(evaluacion, campos, ("trato",))
        if respuesta is None or not str(respuesta).strip():
            continue
        numero = _numero(respuesta)
        if numero is None:
            respuestas.append(str(respuesta).strip())
        else:
            puntuaciones.append(numero)
    if respuestas and any(_numero(respuesta) is None for respuesta in respuestas):
        return Counter(respuestas).most_common(1)[0][0]
    promedio = (
        round(sum(puntuaciones) / len(puntuaciones), 1)
        if puntuaciones
        else _promedio(evaluaciones, campos, ("trato",))
    )
    return _etiqueta_trato(promedio)


def _etiqueta_trato(promedio):
    if promedio is None:
        return "Sin registros"
    if promedio >= 4.5:
        return "Excelente"
    if promedio >= 3.5:
        return "Bueno"
    return "Regular"


def _porcentaje_dudas_resueltas(evaluaciones):
    porcentajes = []
    respuestas = []
    for evaluacion in evaluaciones:
        porcentaje = _numero(
            _obtener_valor(
                evaluacion,
                ("dudas_resueltas_porcentaje",),
                ("porcentaje de dudas resueltas",),
            )
        )
        if porcentaje is not None:
            porcentajes.append(porcentaje)
            continue
        respuesta = _obtener_valor(
            evaluacion,
            ("dudas_resueltas",),
            ("duda",),
        )
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
    campos_puntuacion = ("puntuacion", "overall_rating", "r1_atencion_recibida")
    puntuaciones = []
    for evaluacion in evaluaciones:
        puntuacion = None
        for campo in campos_puntuacion:
            puntuacion = _numero(_obtener_valor(evaluacion, (campo,)))
            if puntuacion is not None:
                break
        if puntuacion is None:
            puntuacion = _numero(
                _obtener_valor(evaluacion, (), ("atencion recibida",))
            )
        puntuaciones.append((evaluacion, puntuacion))
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
        patologia = _obtener_valor(evaluacion, ("patologia_cronica",))
        if isinstance(patologia, str) and patologia.strip():
            nombre_patologia = patologia.strip()
            patologias[nombre_patologia].append(puntuacion)
            paciente_id = _obtener_valor(evaluacion, ("paciente_id",))
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
        (
            "atencion_medica",
            "promedio_atencion_medica",
            "r1_atencion_recibida",
            "overall_rating",
            "puntuacion",
        ),
        ("atencion",),
    )
    espera_promedio = _promedio(
        evaluaciones,
        (
            "tiempo_espera_minutos",
            "tiempo_espera_promedio_minutos",
            "tiempo_espera",
        ),
        ("espera",),
    )
    trato_promedio = _promedio_textual_o_satisfaccion(
        evaluaciones,
        ("trato_personal", "trato_personal_promedio"),
    )
    if trato_promedio == "Sin registros":
        trato_promedio = _etiqueta_trato(
            _promedio(evaluaciones, campos_puntuacion)
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
