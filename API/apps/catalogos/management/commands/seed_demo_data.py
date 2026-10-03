from datetime import date, timedelta
from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogos.Especialidades.models import Especialidades
from apps.catalogos.Medicos.models import Medicos
from apps.catalogos.Paciente_Patologia.models import PacientePatologia
from apps.catalogos.Pacientes.models import Pacientes
from apps.catalogos.Patologias_Cronicas.models import PatologiasCronicas
from apps.catalogos.Sector.models import Sector
from apps.catalogos.Atención_cronico.models import AtencionCronico


class Command(BaseCommand):
    help = "Genera datos demo para pacientes, patologías y atención crónica."

    def handle(self, *args, **options):
        names = [
            "Carlos", "María", "José", "Ana", "Luis", "Sofía", "Roberto", "Laura",
            "Miguel", "Valeria", "Pedro", "Andrea", "Daniel", "Fernanda", "Diego",
            "Camila", "Oscar", "Gabriela", "Mateo", "Isabel", "Javier", "Paula",
            "René", "Tatiana", "Francisco", "Nadia", "Edwin", "Yolanda", "Rafael",
            "Lucía", "Manuel", "Diana", "Hernán", "Cecilia", "Tomás", "Alina",
        ]
        last_names = [
            "García", "Martínez", "López", "Sánchez", "Pérez", "Torres", "Ramírez",
            "Flores", "Castro", "Vega", "Ruiz", "Mendoza", "Herrera", "Silva", "Ortiz",
            "Morales", "Jiménez", "Reyes", "Cruz", "Díaz", "Mora", "Aragón", "Aguirre",
            "Rojas", "Salazar", "Navarro", "Delgado", "González", "Pineda", "Córdoba",
        ]
        barrios = [
            "San Miguel", "Las Colinas", "El Carmen", "La Primavera", "Bello Horizonte",
            "Santa Ana", "La Unión", "San Ramón", "Villa Nueva", "Centro Histórico",
            "El Progreso", "Los Laureles", "El Roble", "El Sauce", "Miraflores",
        ]
        calles = [
            "1ra Calle", "2da Calle", "3ra Calle", "4ta Calle", "5ta Avenida",
            "6ta Avenida", "7ma Calle", "8va Calle", "9na Avenida", "10ma Calle",
            "11 Calle", "12 Avenida", "13 Calle", "14 Avenida", "15 Calle",
        ]
        sectores = [
            ("Zona Sur", 1, "Urbana"), ("Zona Central", 2, "Urbana"), ("Zona Norte", 3, "Urbana"),
            ("Noel Morales", 4, "Urbana"), ("Alejandro Martínez", 5, "Urbana"),
            ("Camilo Ortega", 6, "Urbana"), ("Primero de Mayo", 7, "Urbana"),
            ("30 Mayo", 8, "Urbana"), ("Chamorro", 9, "Urbana"), ("Sector Carretera", 10, "Rural"),
        ]
        especialidades = [
            "Medicina General", "Cardiología", "Pediatría", "Ginecología",
            "Endocrinología", "Neurología", "Dermatología", "Nefrología",
        ]
        patologias = [
            "Hipertensión", "Diabetes Mellitus", "Asma", "Artritis", "Renal",
            "Enfermedad Renal Crónica", "Cardiopatía", "Obesidad", "EPOC", "Epilepsia",
            "Colitis", "Gastritis", "Osteoporosis", "Alergia", "Depresión",
        ]

        with transaction.atomic():
            for nombre, numero, zona in sectores:
                Sector.objects.get_or_create(
                    nombre_sector=nombre,
                    defaults={
                        "numero_sector": numero,
                        "zona_procedencia": zona,
                        "estado": True,
                    },
                )

            for nombre in especialidades:
                Especialidades.objects.get_or_create(
                    nombre_especialidad=nombre,
                    defaults={"estado": True},
                )

            for nombre in patologias:
                PatologiasCronicas.objects.get_or_create(
                    nombre_patologia=nombre,
                    defaults={"estado": True},
                )

            for i in range(1, 11):
                esp = Especialidades.objects.order_by('id')[i % Especialidades.objects.count()]
                nombre = f"Médico {i}"
                apellido = last_names[i % len(last_names)]
                codigo = f"MED-{i:03d}"
                Medicos.objects.get_or_create(
                    codigo_minsa=codigo,
                    defaults={
                        "id_especialidad": esp,
                        "nombre": nombre,
                        "apellidos": apellido,
                        "celular": f"{70000000 + i}",
                        "estado": True,
                    },
                )

            while Pacientes.objects.count() < 100:
                nombre = random.choice(names)
                apellido = random.choice(last_names)
                sexo = random.choice(["M", "F"])
                anio = random.randint(1950, 2008)
                mes = random.randint(1, 12)
                dia = random.randint(1, 28)
                fecha_nac = date(anio, mes, dia)
                celular = str(random.randint(81000000, 99999999))
                numero = Pacientes.objects.count() + 1
                cedula = f"{numero:013d}{chr(65 + (numero % 26))}"
                direccion = f"{random.choice(calles)} {random.randint(1, 200)}"
                barrio = random.choice(barrios)
                sector = Sector.objects.order_by('?').first()

                Pacientes.objects.create(
                    id_sector=sector,
                    nombre=nombre,
                    apellidos=apellido,
                    sexo=sexo,
                    fecha_de_nacimiento=fecha_nac,
                    celular=celular,
                    cedula=cedula,
                    direccion=direccion,
                    barrio=barrio,
                    estado=True,
                )

            while PacientePatologia.objects.count() < 100:
                paciente = Pacientes.objects.order_by('?').first()
                patologia = PatologiasCronicas.objects.order_by('?').first()
                if paciente is None or patologia is None:
                    break

                obj, created = PacientePatologia.objects.get_or_create(
                    id_paciente=paciente,
                    id_patologia_cronica=patologia,
                    defaults={
                        "fecha_de_diagnostico": date.today() - timedelta(days=random.randint(30, 2000)),
                        "estado": True,
                        "observaciones": "Diagnóstico registrado en preparación de datos demo.",
                    },
                )

            while AtencionCronico.objects.count() < 30:
                relacion = PacientePatologia.objects.order_by('?').first()
                medico = Medicos.objects.order_by('?').first()
                if relacion is None or medico is None:
                    break

                fecha = date.today() - timedelta(days=random.randint(1, 365))
                peso = Decimal(str(round(random.uniform(45, 95), 2)))
                talla = Decimal(str(round(random.uniform(1.50, 1.90), 2)))
                presion = f"{random.randint(110, 150)}/{random.randint(70, 95)}"
                proxima = fecha + timedelta(days=random.randint(7, 60))

                AtencionCronico.objects.create(
                    id_paciente_patologia=relacion,
                    id_medico=medico,
                    fecha_atencion=fecha,
                    peso=peso,
                    talla=talla,
                    presion_arterial=presion,
                    fecha_proxima_cita=proxima,
                    asistio=random.choice([True, False]),
                    consulta_especializada=random.choice([True, False]),
                    observaciones="Seguimiento de control y evolución clínica para demostración del sistema.",
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos demo creados: {Pacientes.objects.count()} pacientes, "
                f"{PacientePatologia.objects.count()} pacientes-patologías y "
                f"{AtencionCronico.objects.count()} atenciones crónicas."
            )
        )
