from datetime import datetime, time, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Room(models.Model):
    SMALL = "small"
    NORMAL = "normal"
    BIG = "big"
    ROOM_TYPES = [
        (SMALL, "Small (1–3)"),
        (NORMAL, "Normal (3–5)"),
        (BIG, "Big (5–8)"),
    ]
    name = models.CharField(max_length=100, unique=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    capacity_min = models.PositiveIntegerField(default=1)
    capacity_max = models.PositiveIntegerField()            # keep capacity limits
    min_legit_attendees = models.PositiveIntegerField(default=1)  # <= set to 1 everywhere
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.name} · {self.get_room_type_display()}"

class Reservation(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reservations")
    start_time = models.DateTimeField()
    end_time   = models.DateTimeField()
    attendees  = models.PositiveIntegerField(default=1)     # we’ll default to 1
    approved   = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_time"]
        constraints = [
            models.CheckConstraint(check=models.Q(end_time__gt=models.F("start_time")), name="end_after_start"),
        ]

    @property
    def is_legit(self):
        # no special rule anymore – 1 person is enough
        return self.attendees >= 1

    def clean(self):
        super().clean()
        if self.room.room_type == Room.SMALL:   
            if not (1 <= self.attendees <= 3):
                raise ValidationError("Small room allows 1–3 attendees only.")
        elif self.room.room_type == Room.NORMAL:
            if not (3 <= self.attendees <= 5):
                raise ValidationError("Normal room requires 3–5 attendees.")
        elif self.room.room_type == Room.BIG:
            if not (5 <= self.attendees <= 8):
                raise ValidationError("Big room requires 5-8 attendees.")
       

        # within next 3 days, not past
        now = timezone.localtime()
        latest = now + timedelta(days=3)
        if self.start_time < now:
            raise ValidationError("Start time cannot be in the past.")
        if self.start_time > latest:
            raise ValidationError("You can only book within the next 3 days.")

        # day rule + hours 06:00–24:00 and exactly 1 hour
        start_local = timezone.localtime(self.start_time)
        end_local   = timezone.localtime(self.end_time)

        if start_local.date() != end_local.date():
            raise ValidationError("Start and end must be on the same day.")

        open_bound = datetime.combine(start_local.date(), time(6, 0, tzinfo=start_local.tzinfo))
        close_bound = datetime.combine(start_local.date() + timedelta(days=1), time(0, 0, tzinfo=start_local.tzinfo))

        if not (open_bound <= start_local < close_bound):
            raise ValidationError("Start time must be between 06:00 and 23:00.")
        if not (start_local < end_local <= close_bound):
            raise ValidationError("End time must be no later than 24:00 the same day.")

        # exactly 1 hour
        if (end_local - start_local) != timedelta(hours=1):
            raise ValidationError("Each reservation must be exactly 1 hour.")
