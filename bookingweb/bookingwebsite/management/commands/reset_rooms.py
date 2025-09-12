from django.core.management.base import BaseCommand
from bookingwebsite.models import Room
from .seed_rooms import PRESETS  # reuse the presets list

class Command(BaseCommand):
    help = "Delete all rooms and reseed with 9 predefined ones."

    def handle(self, *args, **kwargs):
        # wipe all rooms
        count = Room.objects.count()
        Room.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Deleted {count} existing rooms."))

        # reseed
        created = 0
        for name, rtype, cmin, cmax, min_legit, slot_hours, loc in PRESETS:
            obj, was_created = Room.objects.get_or_create(
                name=name,
                defaults=dict(
                    room_type=rtype,
                    capacity_min=cmin,
                    capacity_max=cmax,
                    min_legit_attendees=min_legit,
                    slot_hours=slot_hours,
                    location=loc,
                ),
            )
            created += 1 if was_created else 0

        self.stdout.write(self.style.SUCCESS(f"Reseed complete. Created {created} new rooms."))
