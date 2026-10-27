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
  "id_fecha": 20261026,
  "id_paciente": 102,
  "id_patologia": 12,
  "puntuacion_general": 5,
  "score_atencion_medica": 5,
  "tiempo_espera_minutos": 5,
  "score_trato_personal": 5,
  "score_consulta_doctor": 5,
  "resolucion_dudas_val": 1
}
```

### Cómo obtener los identificadores

- `id_paciente` corresponde al `id` de `Pacientes`, no al ID de la cuenta
  `User`.
- `id_patologia` corresponde al `id` de `PatologiasCronicas`. Si se parte de
  una relación `PacientePatologia`, se debe enviar su
  `id_patologia_cronica_id`, no el `id` de la relación.
- Ambos son claves primarias `BigAutoField` en este proyecto. Los valores `102`
  y `12` del ejemplo son ilustrativos; usa los IDs reales que devuelve la API.
- `id_fecha` es la clave de fecha `AAAAMMDD`. El proyecto todavía no contiene
  un modelo de dimensión de fechas.
- El proyecto tampoco tiene un modelo relacional de encuestas: `id_encuesta`
  debe ser el identificador que asigne la app o el sistema que envía la
  encuesta. MongoDB genera aparte el campo `_id`.

Envía el JWT de la cuenta Paciente en `Authorization: Bearer <access>`.

Las puntuaciones se validan entre 1 y 5, el tiempo de espera como valor entero
no negativo y la resolución de dudas como `0` o `1`. `id_fecha` debe ser una
fecha válida con formato `AAAAMMDD`.
