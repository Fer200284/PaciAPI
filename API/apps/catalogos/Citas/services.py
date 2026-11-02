from datetime import datetime

from django.utils import timezone

from .models import Citas


def _fecha_hora(fecha, hora):
    if not fecha or not hora:
        return None
    return timezone.make_aware(
        datetime.combine(fecha, hora),
        timezone.get_current_timezone(),
    )


def _buscar_cita_programada(paciente_id, medico_id, fecha_hora):
    return Citas.objects.filter(
        id_paciente_id=paciente_id,
        id_medico_id=medico_id,
        fecha_hora_cita=fecha_hora,
        estado=Citas.Estado.PROGRAMADA,
    ).order_by("pk").first()


def sincronizar_cita_proxima(
    atencion,
    fecha_anterior=None,
    hora_anterior=None,
    paciente_anterior_id=None,
    medico_anterior_id=None,
):
    fecha_actual = atencion.fecha_proxima_cita
    hora_actual = atencion.hora_proxima_cita
    fecha_hora_actual = _fecha_hora(fecha_actual, hora_actual)
    fecha_hora_anterior = _fecha_hora(fecha_anterior, hora_anterior)

    paciente_actual_id = atencion.id_paciente_patologia.id_paciente_id
    medico_actual_id = atencion.id_medico_id
    paciente_anterior_id = (
        paciente_actual_id
        if paciente_anterior_id is None
        else paciente_anterior_id
    )
    medico_anterior_id = (
        medico_actual_id if medico_anterior_id is None else medico_anterior_id
    )

    cita_anterior = None
    if fecha_hora_anterior:
        cita_anterior = _buscar_cita_programada(
            paciente_anterior_id,
            medico_anterior_id,
            fecha_hora_anterior,
        )

    if not fecha_hora_actual:
        if cita_anterior:
            cita_anterior.estado = Citas.Estado.CANCELADA
            cita_anterior.save(update_fields=["estado"])
        return cita_anterior

    misma_programacion = (
        fecha_hora_anterior == fecha_hora_actual
        and paciente_anterior_id == paciente_actual_id
        and medico_anterior_id == medico_actual_id
    )
    if misma_programacion:
        existente = Citas.objects.filter(
            id_paciente_id=paciente_actual_id,
            id_medico_id=medico_actual_id,
            fecha_hora_cita=fecha_hora_actual,
        ).order_by("pk").first()
        if existente and existente.estado != Citas.Estado.PROGRAMADA:
            return existente

    cita = cita_anterior
    if cita is None:
        cita = _buscar_cita_programada(
            paciente_actual_id,
            medico_actual_id,
            fecha_hora_actual,
        )

    if cita is None:
        return Citas.objects.create(
            id_paciente_id=paciente_actual_id,
            id_medico_id=medico_actual_id,
            fecha_hora_cita=fecha_hora_actual,
            estado=Citas.Estado.PROGRAMADA,
        )

    cita.id_paciente_id = paciente_actual_id
    cita.id_medico_id = medico_actual_id
    cita.fecha_hora_cita = fecha_hora_actual
    cita.save(update_fields=[
        "id_paciente",
        "id_medico",
        "fecha_hora_cita",
    ])
    return cita


def registrar_llegada_cita(atencion, fecha_llegada):
    fecha_cita = atencion.fecha_atencion
    citas_del_dia = Citas.objects.filter(
        id_paciente_id=atencion.id_paciente_patologia.id_paciente_id,
        id_medico_id=atencion.id_medico_id,
        fecha_hora_cita__date=fecha_cita,
        estado=Citas.Estado.PROGRAMADA,
    )
    cita = min(
        citas_del_dia,
        key=lambda item: abs(
            (item.fecha_hora_cita - fecha_llegada).total_seconds()
        ),
        default=None,
    )
    if cita is None:
        return None

    cita.estado = Citas.Estado.ASISTIO
    cita.fecha_atencion_real = fecha_llegada
    cita.save(update_fields=["estado", "fecha_atencion_real"])
    return cita
