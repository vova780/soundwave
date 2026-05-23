from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('play/<int:track_id>/', views.play_track, name='play_track'),
    path('artist/<int:artist_id>/', views.artist_detail, name='artist_detail'),
    path('artist/<int:artist_id>/subscribe/', views.toggle_subscribe, name='toggle_subscribe'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('playlist/create/', views.create_playlist, name='create_playlist'),
    path('playlist/<int:pl_id>/', views.playlist_detail, name='playlist_detail'),
    path('playlist/<int:pl_id>/delete/', views.delete_playlist, name='delete_playlist'),
    path('playlist/<int:pl_id>/remove/<int:track_id>/', views.remove_from_playlist, name='remove_from_playlist'),
    path('api/tracks/', views.api_tracks, name='api_tracks'),
    path('api/playlist/add/', views.add_to_playlist, name='add_to_playlist'),
]
