from django.contrib import admin
from .models import Room, Reservation

def approve_reservations(modeladmin, request, queryset):
    updated = queryset.update(approved=True)
    modeladmin.message_user(request, f"Approved {updated} reservation(s).")

approve_reservations.short_description = "Approve selected reservations"

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "room_type", "capacity_min", "capacity_max", "min_legit_attendees", "location")
    list_filter = ("room_type",)
    search_fields = ("name", "location")

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "start_time", "end_time", "attendees", "approved")
    list_editable = ("approved",)              # <— make it editable on the list page
    list_filter = ("approved", "room__room_type")
    search_fields = ("user__username", "room__name")
    ordering = ("-start_time",)
    actions = [approve_reservations]