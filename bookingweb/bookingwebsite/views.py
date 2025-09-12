from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from django.shortcuts import render
from .models import Room, Reservation
from django.contrib.auth.decorators import user_passes_test
from itertools import zip_longest
from django.contrib.auth.decorators import login_required
from datetime import datetime, time, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Q

def index(request):
    return render(request, 'index.html', {})

def aboutme(request):
    return render(request, 'aboutme.html', {})

def _hours_list():
    # 06:00..23:00 as 'HH:MM' strings
    return [f"{h:02d}:00" for h in range(6, 24)]

def _aware(dt):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(dt, tz)


# ---------- Auth ----------


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Registered! Please log in.")
        return redirect('login')
    return render(request, 'auth/register.html', {"form": form})

def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect('index')
    return render(request, 'auth/login.html', {"form": form})

def room_list(request):
    if not request.user.is_authenticated:
        return render(request, 'rooms/not_logged_in.html')
    rooms = Room.objects.all().order_by("name")
    return render(request, 'rooms/list.html', {"rooms": rooms})

def my_reservations(request):
    if not request.user.is_authenticated:
        return render(request, 'reservations/not_logged_in.html')
    qs = Reservation.objects.filter(user=request.user)
    return render(request, 'reservations/my_list.html', {"reservations": qs})

@login_required
def logout_view(request):
    logout(request)
    return redirect('index')

# ---------- User features ----------
@login_required
def room_list(request):
    small  = list(Room.objects.filter(room_type=Room.SMALL).order_by("name"))
    normal = list(Room.objects.filter(room_type=Room.NORMAL).order_by("name"))
    big    = list(Room.objects.filter(room_type=Room.BIG).order_by("name"))

    # rows = [(S1,N1,B1), (S2,N2,B2), (S3,N3,B3), ...]
    rows = list(zip_longest(small, normal, big))  # fills missing with None if uneven
    return render(request, "rooms/list_grid_snb.html", {"rows": rows})

@login_required
def reserve_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id)

    # one future reservation per user
    if Reservation.objects.filter(user=request.user, start_time__gte=timezone.now()).exists():
        messages.error(request, "You already have a future reservation.")
        return redirect('my_reservations')

    today = timezone.localdate()
    days = [today + timedelta(days=i) for i in range(3)]

    if request.method == "POST":
        day_str = request.POST.get("day")
        time_str = request.POST.get("time")
        if not (day_str and time_str):
            messages.error(request, "Please pick a day and a time.")
            return redirect(request.path)

        try:
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
            hour, minute = map(int, time_str.split(":"))
        except Exception:
            messages.error(request, "Invalid date/time.")
            return redirect(request.path)

        start_dt = _aware(datetime.combine(day, time(hour, minute)))
        end_dt = start_dt + timedelta(hours=1)

        if room.reservations.filter(Q(start_time__lt=end_dt) & Q(end_time__gt=start_dt)).exists():
            messages.error(request, "That slot is taken. Pick another.")
            return redirect(request.path)

        res = Reservation(user=request.user, room=room, start_time=start_dt, end_time=end_dt, attendees=1)
        try:
            res.clean()
        except ValidationError as e:
            messages.error(request, "; ".join(e.messages))
            return redirect(request.path)

        res.save()
        messages.success(request, "Reservation submitted (pending approval).")
        return redirect('my_reservations')

    # build availability JSON (hours + taken list)
    availability = {}
    for d in days:
        taken = set()
        day_start = _aware(datetime.combine(d, time(0, 0)))
        day_end = day_start + timedelta(days=1)
        for r in room.reservations.filter(start_time__gte=day_start, start_time__lt=day_end):
            taken.add(timezone.localtime(r.start_time).strftime("%H:%M"))
        availability[d.strftime("%Y-%m-%d")] = {"hours": _hours_list(), "taken": sorted(list(taken))}

    return render(request, "rooms/reserve_simple.html", {
        "room": room,
        "days": days,
        "availability": availability,
    })

@login_required
def my_reservations(request):
    qs = Reservation.objects.filter(user=request.user)
    return render(request, 'reservations/my_list.html', {"reservations": qs})

@login_required
def cancel_reservation(request, pk):
    res = get_object_or_404(Reservation, pk=pk, user=request.user)
    res.delete()
    messages.warning(request, "Reservation cancelled.")
    return redirect('my_reservations')

# ---------- Admin feature (approve) ----------
def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def approve_reservation(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    res.approved = True
    res.save()
    messages.success(request, "Reservation approved.")
    return redirect('index')

@user_passes_test(is_admin)
def room_reservations_report(request):
    rooms = Room.objects.all().prefetch_related('reservation_set')
    return render(request, 'admin/room_report.html', {"rooms": rooms})