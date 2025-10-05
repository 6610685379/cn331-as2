from io import StringIO
import unittest
from django.test import TestCase, SimpleTestCase
from django.urls import reverse, resolve, NoReverseMatch
from django.contrib.auth.models import User
from bookingwebsite import views
from django.core.management import call_command
from datetime import timedelta
from django.utils import timezone
from bookingwebsite.models import Room, Reservation

# If your models have different names/fields, adjust these imports & usages.
try:
    from bookingwebsite.models import Room, RoomType
    HAS_ROOM_MODELS = True
except Exception:
    HAS_ROOM_MODELS = False


def has_url(name: str) -> bool:
    """Return True if a named URL exists in this project."""
    try:
        reverse(name)
        return True
    except NoReverseMatch:
        return False


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
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp.url)

    def test_room_list_guest_follow_redirect_shows_login(self):
        resp = self.client.get(reverse('room_list'), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'login', html=False)


# --------------------------
# Authentication + View Tests
# --------------------------
class AuthenticatedPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='secret123')

    def test_room_list_authenticated(self):
        self.client.login(username='alice', password='secret123')
        resp = self.client.get(reverse('room_list'))
        self.assertEqual(resp.status_code, 200)

    def test_login_success_redirects(self):
        """Submitting correct credentials should redirect (usually to index or next=...)."""
        resp = self.client.post(reverse('login'),
                                {'username': 'alice', 'password': 'secret123'})
        self.assertEqual(resp.status_code, 302)

    @unittest.skipUnless(HAS_ROOM_MODELS, "Room/RoomType models not available")
    def test_room_list_shows_existing_room_when_authenticated(self):
        """Create a room and verify it appears on the authenticated room list."""
        self.client.login(username='alice', password='secret123')
        rt = RoomType.objects.create(name="Lecture")
        room = Room.objects.create(name="Room101", capacity=20, room_type=rt)

        resp = self.client.get(reverse('room_list'))
        self.assertEqual(resp.status_code, 200)
        # Loose check: make sure room name renders somewhere
        self.assertContains(resp, room.name)

    def test_optional_logout_view(self):
        """If a 'logout' route exists, ensure it returns 200/302."""
        if not has_url('logout'):
            self.skipTest("logout URL not configured")
        resp = self.client.get(reverse('logout'))
        self.assertIn(resp.status_code, (200, 302))

    @unittest.skipUnless(HAS_ROOM_MODELS, "Room/RoomType models not available")
    def test_optional_booking_create_post(self):
        """
        If a 'booking_create' route exists, POST a simple payload.
        Adjust field names to match your form if different.
        """
        if not has_url('booking_create'):
            self.skipTest("booking_create URL not configured")

        self.client.login(username='alice', password='secret123')
        rt = RoomType.objects.create(name="Lecture")
        room = Room.objects.create(name="R101", capacity=20, room_type=rt)

        payload = {
            "room": room.id,
            "date": "2025-10-10",
            "start": "09:00",
            "end": "10:00",
            "people": 3,
        }
        resp = self.client.post(reverse("booking_create"), payload, follow=True)
        # Depending on your view, this could be a redirect to detail/list or a render with 200
        self.assertIn(resp.status_code, (200, 302))


# --------------------------
# Login Flow (invalid creds)
# --------------------------
class LoginFlowTests(TestCase):
    def test_login_with_wrong_credentials_stays_on_page(self):
        resp = self.client.post(reverse('login'), {'username': 'wrong', 'password': 'nope'})
        self.assertNotEqual(resp.status_code, 302)


# --------------------------
# Management Commands
# --------------------------
class CommandsTests(TestCase):
    def test_seed_rooms_runs(self):
        out = StringIO()
        call_command("seed_rooms", stdout=out)
        self.assertIn("seed", out.getvalue().lower())

    def test_reset_rooms_runs(self):
        out = StringIO()
        call_command("reset_rooms", stdout=out)
        self.assertIn("deleted", out.getvalue().lower())



class BaseSetup(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.user = User.objects.create_user("alice", password="secret123")
        cls.staff = User.objects.create_user("admin", password="admin123", is_staff=True)

        # Rooms (one per type)
        cls.small = Room.objects.create(name="S-1", room_type=Room.SMALL, capacity_min=1, capacity_max=3)
        cls.normal = Room.objects.create(name="N-1", room_type=Room.NORMAL, capacity_min=3, capacity_max=5)
        cls.big = Room.objects.create(name="B-1", room_type=Room.BIG, capacity_min=5, capacity_max=8)

    # helpers
    def _dt(self, hours_from_now=1, duration_hours=1):
        start = timezone.now() + timedelta(hours=hours_from_now)
        end = start + timedelta(hours=duration_hours)
        return start, end

    def _login(self, who="alice"):
        if who == "alice":
            self.client.login(username="alice", password="secret123")
        else:
            self.client.login(username="admin", password="admin123")


class PublicViewsTests(BaseSetup):
    def test_index_and_aboutme_load(self):
        r = self.client.get(reverse("index"))
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("aboutme"))
        self.assertEqual(r.status_code, 200)

    def test_login_get_and_post_invalid(self):
        # GET login page
        r = self.client.get(reverse("login"))
        self.assertEqual(r.status_code, 200)
        # POST invalid credentials → re-render (not 302)
        r = self.client.post(reverse("login"), {"username": "nope", "password": "xxx"})
        self.assertNotEqual(r.status_code, 302)

    def test_register_invalid_then_valid(self):
        # invalid (missing fields)
        r = self.client.post(reverse("register"), {})
        self.assertEqual(r.status_code, 200)  # re-render with form errors

        # valid register
        payload = {"username": "newguy", "password1": "StrongPassw0rd!", "password2": "StrongPassw0rd!"}
        r = self.client.post(reverse("register"), payload, follow=True)
        self.assertEqual(r.status_code, 200)
        # should land on login by your view
        self.assertContains(r, "login", html=False)


class AuthFlowTests(BaseSetup):
    def test_login_success_redirects_and_logout_back_to_index(self):
        r = self.client.post(reverse("login"), {"username": "alice", "password": "secret123"})
        self.assertEqual(r.status_code, 302)

        self._login("alice")
        r = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(r.status_code, 200)
        # Assert we’re on the index route / template instead of searching for the word "index"
        self.assertEqual(r.request["PATH_INFO"], reverse("index"))
        self.assertTemplateUsed(r, "index.html")
        self.assertContains(r, "Welcome to RoomReserve", html=False)


class RoomListTests(BaseSetup):
    def test_room_list_requires_login(self):
        r = self.client.get(reverse("room_list"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)

    def test_room_list_grid_authenticated(self):
        self._login("alice")
        r = self.client.get(reverse("room_list"))
        self.assertEqual(r.status_code, 200)
        # should render names of the three rooms somewhere on the grid
        for name in ["S-1", "N-1", "B-1"]:
            self.assertContains(r, name)


class ReservationCreateTests(BaseSetup):
    def test_reserve_room_get_page(self):
        self._login("alice")
        r = self.client.get(reverse("reserve_room", args=[self.small.id]))
        self.assertEqual(r.status_code, 200)
        # has day/time UI
        self.assertContains(r, "time", html=False)

    def test_reserve_room_missing_fields(self):
        self._login("alice")
        r = self.client.post(reverse("reserve_room", args=[self.small.id]), {})  # missing day/time
        # view redirects back with error
        self.assertEqual(r.status_code, 302)

    def test_reserve_room_invalid_datetime(self):
        self._login("alice")
        payload = {"day": "not-a-date", "time": "not-a-time", "attendees": 1}
        r = self.client.post(reverse("reserve_room", args=[self.small.id]), payload)
        self.assertEqual(r.status_code, 302)

    def test_reserve_room_conflict(self):
        self._login("alice")
        # Create an existing reservation that will collide
        start, end = self._dt(hours_from_now=4, duration_hours=1)
        Reservation.objects.create(user=self.user, room=self.small, start_time=start, end_time=end, attendees=2)
        # Try to book overlapping slot (same hour)
        payload = {
            "day": timezone.localdate(start).strftime("%Y-%m-%d"),
            "time": timezone.localtime(start).strftime("%H:%M"),
            "attendees": 2,
        }
        r = self.client.post(reverse("reserve_room", args=[self.small.id]), payload)
        self.assertEqual(r.status_code, 302)  # rejected with message

    def test_reserve_room_attendee_rules_small(self):
        self._login("alice")
        # Too many for small (allowed 1–3)
        start, _ = self._dt(hours_from_now=6)
        payload = {
            "day": timezone.localdate(start).strftime("%Y-%m-%d"),
            "time": timezone.localtime(start).strftime("%H:%M"),
            "attendees": 5,
        }
        r = self.client.post(reverse("reserve_room", args=[self.small.id]), payload)
        self.assertEqual(r.status_code, 302)

    def test_reserve_room_success_normal(self):
        self._login("alice")
        start, _ = self._dt(hours_from_now=8)
        payload = {
            "day": timezone.localdate(start).strftime("%Y-%m-%d"),
            "time": timezone.localtime(start).strftime("%H:%M"),
            "attendees": 4,  # valid for NORMAL (3–5)
        }
        r = self.client.post(reverse("reserve_room", args=[self.normal.id]), payload, follow=True)
        self.assertEqual(r.status_code, 200)
        # lands on my reservations page per your view
        self.assertContains(r, "reservations", html=False)

    def test_user_cannot_have_two_future_reservations(self):
        self._login("alice")
        # Create one future reservation
        start, end = self._dt(hours_from_now=10, duration_hours=1)
        Reservation.objects.create(user=self.user, room=self.normal, start_time=start, end_time=end, attendees=3)
        # Try to create another one
        payload = {
            "day": timezone.localdate(start + timedelta(hours=2)).strftime("%Y-%m-%d"),
            "time": (timezone.localtime(start + timedelta(hours=2))).strftime("%H:%M"),
            "attendees": 3,
        }
        r = self.client.post(reverse("reserve_room", args=[self.normal.id]), payload)
        # should redirect with error to my_reservations
        self.assertEqual(r.status_code, 302)


class MyReservationsTests(BaseSetup):
    def test_my_reservations_requires_login(self):
        r = self.client.get(reverse("my_reservations"))
        # login_required should redirect guests
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)

        # Optional: follow the redirect and ensure the login page renders
        r = self.client.get(reverse("my_reservations"), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Login", html=False)

    def test_my_reservations_authenticated(self):
        self._login("alice")
        start, end = self._dt(hours_from_now=3)
        Reservation.objects.create(user=self.user, room=self.small, start_time=start, end_time=end, attendees=2)
        r = self.client.get(reverse("my_reservations"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "S-1")


class CancelReservationTests(BaseSetup):
    def test_cancel_reservation(self):
        self._login("alice")
        start, end = self._dt(hours_from_now=5)
        res = Reservation.objects.create(user=self.user, room=self.small, start_time=start, end_time=end, attendees=2)
        r = self.client.get(reverse("cancel_reservation", args=[res.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        # ensure it’s gone
        self.assertFalse(Reservation.objects.filter(pk=res.pk).exists())


class AdminOnlyViewsTests(BaseSetup):
    def test_approve_reservation_requires_staff(self):
        # non-staff gets redirected to login page (user_passes_test)
        self._login("alice")
        start, end = self._dt(hours_from_now=2)
        res = Reservation.objects.create(user=self.user, room=self.normal, start_time=start, end_time=end, attendees=3)
        r = self.client.get(reverse("approve_reservation", args=[res.pk]))
        self.assertEqual(r.status_code, 302)

    def test_approve_reservation_marks_approved(self):
        self._login("admin")  # staff
        start, end = self._dt(hours_from_now=2)
        res = Reservation.objects.create(user=self.staff, room=self.normal, start_time=start, end_time=end, attendees=3)
        r = self.client.get(reverse("approve_reservation", args=[res.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        res.refresh_from_db()
        self.assertTrue(res.approved)

    def test_delete_reservation(self):
        self._login("admin")
        start, end = self._dt(hours_from_now=2)
        res = Reservation.objects.create(user=self.staff, room=self.big, start_time=start, end_time=end, attendees=6)
        r = self.client.get(reverse("delete_reservation", args=[res.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Reservation.objects.filter(pk=res.pk).exists())

    def test_room_reservations_report(self):
        self._login("admin")
        # add a few reservations so annotate(total_attendees) is exercised
        start1, end1 = self._dt(hours_from_now=1)
        Reservation.objects.create(user=self.staff, room=self.small, start_time=start1, end_time=end1, attendees=2)
        start2, end2 = self._dt(hours_from_now=2)
        Reservation.objects.create(user=self.staff, room=self.small, start_time=start2, end_time=end2, attendees=1)
        r = self.client.get(reverse("room_report"))
        self.assertEqual(r.status_code, 200)
        # report should show room names or totals
        self.assertContains(r, "S-1")
