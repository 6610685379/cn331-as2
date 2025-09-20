from django.apps import AppConfig


class BookingwebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookingwebsite'

class BookingwebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookingwebsite'

    def ready(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = os.getenv("DJANGO_SUPERUSER_USERNAME")
        e = os.getenv("DJANGO_SUPERUSER_EMAIL")
        p = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        if u and p and not User.objects.filter(username=u).exists():
            User.objects.create_superuser(u, e, p)
