from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from .reportes import crear_reporte_gerencial


class EvaluacionesApiTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def autenticar(self, rol):
        usuario = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            rol=rol,
        )
        self.client.force_authenticate(user=usuario)

    @patch("apps.evaluaciones.views.get_evaluaciones_collection")
    def test_post_guarda_evaluacion(self, obtener_coleccion):
        coleccion = Mock()
        coleccion.insert_one.return_value.inserted_id = "mongo-id"
        obtener_coleccion.return_value = coleccion
        self.autenticar("Paciente")
        evaluacion = {"respuesta": "bien", "puntaje": 5}

        respuesta = self.client.post(
            "/api/evaluaciones/",
            evaluacion,
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json(), {"id": "mongo-id"})
        coleccion.insert_one.assert_called_once_with(evaluacion)

    @patch("apps.evaluaciones.views.get_evaluaciones_collection")
    def test_get_retorna_encuestas_solo_a_gerencia(self, obtener_coleccion):
        coleccion = Mock()
        coleccion.find.return_value = [{"respuesta": "bien", "puntaje": 5}]
        obtener_coleccion.return_value = coleccion
        self.autenticar("Gerencia")

        respuesta = self.client.get("/api/evaluaciones/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), [{"respuesta": "bien", "puntaje": 5}])
        coleccion.find.assert_called_once_with({}, {"_id": 0})

    def test_get_deniega_acceso_a_otros_roles(self):
        self.autenticar("Paciente")

        respuesta = self.client.get("/api/evaluaciones/")

        self.assertEqual(respuesta.status_code, 403)

    def test_post_rechaza_cuerpos_que_no_sean_objetos_json(self):
        self.autenticar("Paciente")

        respuesta = self.client.post(
            "/api/evaluaciones/",
            [{"respuesta": "bien"}],
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    @patch("apps.evaluaciones.views.get_reportes_collection")
    @patch("apps.evaluaciones.views.get_evaluaciones_collection")
    def test_reporte_calcula_metricas_y_guarda_por_periodo(
        self,
        obtener_evaluaciones,
        obtener_reportes,
    ):
        evaluaciones = [
            {
                "puntuacion": 5,
                "patologia_cronica": "Diabetes",
                "atencion_medica": 5,
                "tiempo_espera_minutos": 10,
                "trato_personal": "Excelente",
                "dudas_resueltas": True,
            },
            {
                "puntuacion": 3,
                "patologia_cronica": "Diabetes",
                "atencion_medica": 3,
                "tiempo_espera_minutos": 20,
                "trato_personal": "Bueno",
                "dudas_resueltas": False,
            },
        ]
        obtener_evaluaciones.return_value.find.return_value = evaluaciones
        self.autenticar("Gerencia")

        respuesta = self.client.get("/api/reportes-gerenciales/")

        self.assertEqual(respuesta.status_code, 200)
        reporte = respuesta.json()
        self.assertEqual(reporte["total_evaluaciones"], 2)
        self.assertEqual(reporte["puntuacion_promedio"], 4.0)
        self.assertEqual(reporte["porcentaje_satisfaccion_alta"], 50.0)
        self.assertEqual(
            reporte["indicadores_clave"]["tiempo_espera_promedio_minutos"],
            15.0,
        )
        self.assertEqual(
            reporte["indicadores_clave"]["dudas_resueltas_porcentaje"],
            50.0,
        )
        self.assertEqual(
            reporte["desglose_patologias_cronicas"][0]["total_pacientes"],
            2,
        )
        obtener_reportes.return_value.replace_one.assert_called_once()

    @patch("apps.evaluaciones.views.get_reportes_collection")
    @patch("apps.evaluaciones.views.get_evaluaciones_collection")
    def test_reporte_vacio_no_inventa_metricas(
        self,
        obtener_evaluaciones,
        obtener_reportes,
    ):
        obtener_evaluaciones.return_value.find.return_value = []
        self.autenticar("Gerencia")

        respuesta = self.client.get("/api/reportes-gerenciales/")

        self.assertEqual(respuesta.status_code, 200)
        reporte = respuesta.json()
        self.assertEqual(reporte["total_evaluaciones"], 0)
        self.assertEqual(reporte["puntuacion_promedio"], 0.0)
        self.assertEqual(reporte["indicadores_clave"]["promedio_atencion_medica"], "Sin registros")
        self.assertEqual(reporte["indicadores_clave"]["tiempo_espera_promedio_minutos"], 0)
        self.assertEqual(reporte["desglose_patologias_cronicas"], [])
        obtener_reportes.return_value.replace_one.assert_called_once()

    def test_reporte_deniega_acceso_a_otros_roles(self):
        self.autenticar("Paciente")

        respuesta = self.client.get("/api/reportes-gerenciales/")

        self.assertEqual(respuesta.status_code, 403)

    def test_calcula_reporte_con_datos_y_sin_valores_inventados(self):
        reporte = crear_reporte_gerencial([{"puntuacion": 4}])

        self.assertEqual(reporte["puntuacion_promedio"], 4.0)
        self.assertEqual(
            reporte["indicadores_clave"]["promedio_atencion_medica"],
            "Sin registros",
        )
        self.assertEqual(
            reporte["indicadores_clave"]["trato_personal_promedio"],
            "Sin registros",
        )
