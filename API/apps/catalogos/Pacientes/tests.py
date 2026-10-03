from django.test import TestCase
from .models import Pacientes


class PacienteTest(TestCase):
    def test_crear_paciente(self):
        paciente = Pacientes.objects.create(
            nombre='Juan',
            apellidos='Perez',
            sexo='M',
            fecha_de_nacimiento='1990-01-01',
            celular='88888888',
            cedula='0010101000000A',
            direccion='Managua',
            barrio='Centro',
            estado=True,
        )

        self.assertEqual(paciente.nombre, 'Juan')