from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient


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
