from django.test import SimpleTestCase


class FrontendPagesTest(SimpleTestCase):
    def test_root_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PacienCare')

    def test_login_page_loads(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Sesión')
