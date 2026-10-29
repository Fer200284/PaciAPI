# Encuestas analíticas

La app móvil puede enviar una encuesta con `POST /api/analytics/encuestas/`.
El endpoint requiere un JWT de Paciente y guarda las métricas en la colección
`paciencare_db.encuestas_pacientes`. MongoDB genera el campo `_id`.

Configura `MONGODB_URI` en el entorno del backend. No guardes la cadena de
conexión en el repositorio.

El cuerpo JSON debe incluir:

```json
{
  "id_encuesta": 1054,
  "id_fecha": "2026-10-26",
  "id_paciente": 102,
  "id_patologia": 12,
  "puntuacion_general": 5,
  "score_atencion_medica": 5,
  "tiempo_espera_minutos": 5,
  "score_trato_personal": 5,
  "score_consulta_doctor": 5,
  "resolucion_dudas_val": 1,
  "comentario": "La atención fue muy buena."
}
```

`comentario` es opcional y se guarda como texto dentro del mismo documento de
la encuesta en `encuestas_pacientes` (máximo 2000 caracteres). No hace falta
crear una colección nueva en MongoDB. El ETL podrá usar ese texto para poblar
`DimComentario` en el Data Warehouse.

## Consultar y administrar encuestas

- `GET /api/analytics/encuestas/`: Paciente recibe solo encuestas de su ficha
  vinculada; Gerencia puede consultar todas.
- `GET /api/analytics/encuestas/{id}/`: obtiene una encuesta por su `_id` de
  MongoDB, devuelto por la API como `id`.
- `PUT` o `PATCH /api/analytics/encuestas/{id}/`: el Paciente propietario
  puede actualizar puntuaciones y/o comentario. Envía solo los campos que
  cambian.
- `DELETE /api/analytics/encuestas/{id}/`: el Paciente propietario puede
  eliminar su encuesta.

Gerencia tiene acceso de solo lectura. Los cambios y eliminaciones se limitan
al Paciente asociado al token; una encuesta que no pertenezca a su ficha se
responde como no encontrada.

### Cómo obtener los identificadores

- `id_paciente` corresponde al `id` de `Pacientes`, no al ID de la cuenta
  `User`.
- `id_patologia` corresponde al `id` de `PatologiasCronicas`. Si se parte de
  una relación `PacientePatologia`, se debe enviar su
  `id_patologia_cronica_id`, no el `id` de la relación.
- Ambos son claves primarias `BigAutoField` en este proyecto. Los valores `102`
  y `12` del ejemplo son ilustrativos; usa los IDs reales que devuelve la API.
- `id_fecha` es una fecha como texto con formato `AAAA-MM-DD`. El proyecto
  todavía no contiene un modelo de dimensión de fechas.
- El proyecto tampoco tiene un modelo relacional de encuestas: `id_encuesta`
  debe ser el identificador que asigne la app o el sistema que envía la
  encuesta. MongoDB genera aparte el campo `_id`.

Envía el JWT de la cuenta Paciente en `Authorization: Bearer <access>`.

Las puntuaciones se validan entre 1 y 5, el tiempo de espera como valor entero
no negativo y la resolución de dudas como `0` o `1`. `id_fecha` debe ser una
fecha válida con formato `AAAA-MM-DD`; MongoDB la almacena como texto, por
ejemplo `"2026-10-26"`.

## Bitácora analítica de atenciones

La app móvil puede registrar una atención con `POST /api/analytics/atenciones/`
y consultar los registros con `GET /api/analytics/atenciones/`. Los datos se
guardan en `paciencare_dw.bitacora_citas_atenciones`, usando la conexión MongoDB
configurada en `MONGODB_URI`.

Ejemplo de `POST`:

```json
{
  "id_atencion": 28,
  "id_fecha": "2026-10-26",
  "id_paciente": 102,
  "id_medico": 14,
  "id_patologia": 12,
  "asistio_val": 1,
  "duracion_consulta_minutos": 25,
  "tiempo_espera_real_minutos": 10,
  "receto_medicamento_flag": 1,
  "solicito_examen_flag": 0
}
```

El `POST` solo está disponible para cuentas Paciente y comprueba que la
atención exista, pertenezca a la ficha vinculada a la cuenta y coincidan
paciente, médico, patología y fecha. También verifica que `asistio_val` sea
compatible con el campo de asistencia de la atención. El modelo operacional
actual no distingue entre inasistencia y cancelación, por lo que `-1` solo se
acepta para una atención que no figure como asistida. Los flags de receta y
exámenes se calculan desde los registros operacionales de tratamientos y
solicitudes; no se toma como fuente de verdad el valor enviado por la app.

`duracion_consulta_minutos` y `tiempo_espera_real_minutos` son enteros no
negativos (por defecto `15` y `10`). `asistio_val` acepta `-1`, `0` o `1`;
los flags aceptan `0` o `1`. `id_fecha` debe tener formato `AAAA-MM-DD`.
Gerencia puede consultar todas las atenciones y Paciente únicamente las de su
ficha. `id_atencion`, `id_paciente`, `id_medico` e `id_patologia` deben ser los
IDs reales de los registros operacionales, no IDs de cuentas de usuario.
