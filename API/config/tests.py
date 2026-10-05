from django.test import SimpleTestCase


class APITest(SimpleTestCase):

    def test_health_endpoint(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_schema_endpoint(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)

    def test_swagger_endpoint(self):
        response = self.client.get("/api/schema/swagger-ui/")
        self.assertEqual(response.status_code, 200)