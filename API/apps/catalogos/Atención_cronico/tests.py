from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .Api.views import AnalyticsStorageUnavailable, AtencionCronicoViewSet


class AtencionCronicoViewSetTests(SimpleTestCase):
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.guardar_atencion_desde_modelo"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_create_saves_analytics_document_after_operational_record(
        self,
        atomic,
        guardar_analitica,
    ):
        atencion = SimpleNamespace(pk=28)
        serializer = Mock()
        serializer.instance = atencion
        view = AtencionCronicoViewSet()

        view.perform_create(serializer)

        serializer.save.assert_called_once_with()
        guardar_analitica.assert_called_once_with(atencion)

    @patch(
        "apps.catalogos.Atención_cronico.Api.views.guardar_atencion_desde_modelo"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_create_fails_explicitly_when_analytics_storage_is_unavailable(
        self,
        atomic,
        guardar_analitica,
    ):
        guardar_analitica.side_effect = ImproperlyConfigured(
            "MongoDB is not configured"
        )
        serializer = Mock()
        serializer.instance = SimpleNamespace(pk=28)
        view = AtencionCronicoViewSet()

        with self.assertRaises(AnalyticsStorageUnavailable) as context:
            view.perform_create(serializer)

        self.assertEqual(context.exception.status_code, 503)
