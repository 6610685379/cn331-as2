from django.test import TestCase, SimpleTestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from bookingwebsite import views


# --------------------------
# URL Resolution Tests
# --------------------------
class URLResolutionTests(SimpleTestCase):
    def test_index_url_resolves(self):
        url = reverse('index')
        self.assertEqual(resolve(url).func, views.index)

    def test_login_url_resolves(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func, views.login_view)

    def test_room_list_url_resolves(self):
        url = reverse('room_list')
        self.assertEqual(resolve(url).func, views.room_list)


# --------------------------
# Public Page Tests
# --------------------------
class PublicPagesTests(TestCase):
    def test_index_page_loads(self):
        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 200)

    def test_login_page_loads(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

    def test_room_list_redirects_guest_to_login(self):
        resp = self.client.get(reverse('room_list'))
        # Expect redirect
        self.assertEqual(resp.status_code, 302)
        # Should redirect to login (often with ?next=<room_list>)
        self.assertIn(reverse('login'), resp.url)

    def test_room_list_guest_follow_redirect_shows_login(self):
        resp = self.client.get(reverse('room_list'), follow=True)
        # After following redirect, we should be on the login page (200 OK)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'login', html=False)


# --------------------------
# Authentication Tests
# --------------------------
class AuthenticatedPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='secret123')

    def test_room_list_authenticated(self):
        self.client.login(username='alice', password='secret123')
        resp = self.client.get(reverse('room_list'))
        self.assertEqual(resp.status_code, 200)


# --------------------------
# Login Flow Tests
# --------------------------
class LoginFlowTests(TestCase):
    def test_login_with_wrong_credentials_stays_on_page(self):
        resp = self.client.post(reverse('login'), {'username': 'wrong', 'password': 'nope'})
        # Should NOT redirect (stay on login page)
        self.assertNotEqual(resp.status_code, 302)
