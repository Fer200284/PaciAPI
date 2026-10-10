from django.test import TestCase
from .models import Pacientes
from .Api.serializers import PacientesSerializer


class PacienteTest(TestCase):
    def crear_paciente(self, cedula):
        return Pacientes.objects.create(
            nombre='Juan',
            apellidos='Perez',
            sexo='M',
            fecha_de_nacimiento='1990-01-01',
            celular='88888888',
            cedula=cedula,
            direccion='Managua',
            barrio='Centro',
            estado=True,
        )

    def test_crear_paciente(self):
        paciente = self.crear_paciente('0010101000000A')

        self.assertEqual(paciente.nombre, 'Juan')

    def test_no_permite_duplicar_cedula_de_otro_paciente(self):
        self.crear_paciente('0010101000000A')
        serializer = PacientesSerializer(data={
            'nombre': 'Ana',
            'apellidos': 'Lopez',
            'sexo': 'F',
            'fecha_de_nacimiento': '1992-02-02',
            'celular': '88776655',
            'cedula': '0010101000000A',
            'direccion': 'Managua',
            'barrio': 'Centro',
        })

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['cedula'][0]),
            'No se puede guardar el paciente porque esta cédula ya pertenece a otro paciente.',
        )

    def test_permite_conservar_cedula_al_editar_mismo_paciente(self):
        paciente = self.crear_paciente('0010101000000A')
        serializer = PacientesSerializer(
            paciente,
            data={
                'nombre': 'Juan Carlos',
                'apellidos': 'Perez',
                'sexo': 'M',
                'fecha_de_nacimiento': '1990-01-01',
                'celular': '88888888',
                'cedula': '0010101000000A',
                'direccion': 'Managua',
                'barrio': 'Centro',
                'estado': True,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)