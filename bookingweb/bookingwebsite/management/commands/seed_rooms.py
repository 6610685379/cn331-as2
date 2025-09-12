from django.core.management.base import BaseCommand
from bookingwebsite.models import Room

PRESETS = [
    ("S-101", "small", 1, 2, 1, 1, "1st Floor A"),
    ("S-102", "small", 1, 2, 1, 1, "1st Floor B"),
    ("S-103", "small", 1, 2, 1, 1, "1st Floor C"),
    ("N-201", "normal", 3, 5, 3, 3, "2nd Floor A"),
    ("N-202", "normal", 3, 5, 3, 3, "2nd Floor B"),
    ("N-203", "normal", 3, 5, 3, 3, "2nd Floor C"),
    ("B-301", "big", 5, 8, 5, 5, "3rd Floor A"),
    ("B-302", "big", 5, 8, 5, 5, "3rd Floor B"),
    ("B-303", "big", 5, 8, 5, 5, "3rd Floor C"),
]

class Command(BaseCommand):
    help = "Seed 9 rooms (3 small, 3 normal, 3 big) with slot_hours."

    def handle(self, *args, **kwargs):
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
        self.stdout.write(self.style.SUCCESS(f"Seed complete. Created {created} new rooms."))
