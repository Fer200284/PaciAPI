# Evaluaciones de pacientes en MongoDB Atlas

La API ofrece estos endpoints:

- `POST /api/evaluaciones/`: recibe una evaluación como objeto JSON, la guarda
  en `paciencare_db.evaluaciones_pacientes` y responde con HTTP 201 y el ID
  generado por MongoDB.
- `GET /api/evaluaciones/`: devuelve todas las evaluaciones sin el campo Mongo
  `_id`. Solo permite el acceso a usuarios autenticados con rol `Gerencia`.

Ambos endpoints requieren el token JWT en el encabezado:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

Configura `MONGODB_URI` en **Azure App Service → Settings → Environment
variables** con la cadena de conexión privada de MongoDB Atlas. No la escribas
en el código ni en archivos del repositorio. Asegúrate también de que la lista
de acceso de red de Atlas permita las conexiones salientes de la aplicación
Azure. El backend devuelve HTTP 503 y registra el error si la variable falta o
Atlas no está disponible.

El cuerpo JSON se almacena tal como se recibe. Por ejemplo:

```json
{
  "paciente_id": 123,
  "respuestas": [
    {"pregunta": "¿Cómo se siente?", "respuesta": "Bien"}
  ],
  "fecha": "2026-10-15T12:00:00Z"
}
```
