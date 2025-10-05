from django.core.management.base import BaseCommand
from bookingwebsite.models import Room
from django.core.exceptions import FieldDoesNotExist
from .seed_rooms import PRESETS  # reuse the presets list

def model_has_field(model, field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False

class Command(BaseCommand):
    help = "Delete all rooms and reseed 9 predefined ones. Works with/without Room.slot_hours."

    def handle(self, *args, **kwargs):
        # wipe all rooms
        count = Room.objects.count()
        Room.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Deleted {count} existing rooms."))

        # reseed
        created = 0
        has_slot_hours = model_has_field(Room, "slot_hours")

        for name, rtype, cmin, cmax, min_legit, hours, loc in PRESETS:
            defaults = dict(
                room_type=rtype,
                capacity_min=cmin,
                capacity_max=cmax,
                min_legit_attendees=min_legit,
                location=loc,
            )
            if has_slot_hours:
                defaults["slot_hours"] = hours

            obj, was_created = Room.objects.get_or_create(
                name=name,
                defaults=defaults,
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Reseed complete. Created {created} new rooms."))