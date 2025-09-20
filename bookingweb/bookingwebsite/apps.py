from django.apps import AppConfig
import os

class BookingwebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookingwebsite'

    # def ready(self):
    #     from django.db.models.signals import post_migrate
    #     from django.contrib.auth import get_user_model

    #     def ensure_superuser(sender, **kwargs):
    #         User = get_user_model()
    #         u = os.getenv("DJANGO_SUPERUSER_USERNAME")
    #         e = os.getenv("DJANGO_SUPERUSER_EMAIL")
    #         p = os.getenv("DJANGO_SUPERUSER_PASSWORD")
    #         if u and p and not User.objects.filter(username=u).exists():
    #             User.objects.create_superuser(u, e, p)

    #     # run AFTER migrations so auth_user exists
    #     post_migrate.connect(ensure_superuser, sender=self)
