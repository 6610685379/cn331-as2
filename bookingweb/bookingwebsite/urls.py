from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.index, name='index'),
    path('aboutme', views.aboutme, name='aboutme'),

    # auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),


    # rooms
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:room_id>/reserve/', views.reserve_room, name='reserve_room'),

    # reservations
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('reservations/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),

    # admin-side approval (simple)
    path('reservations/<int:pk>/approve/', views.approve_reservation, name='approve_reservation'),
    path('admin/room-report/', views.room_reservations_report, name='room_report'),
]
