import os
import json
from pathlib import Path
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.conf import settings
from .forms import UploadTrackForm, RegisterForm, LoginForm, CreatePlaylistForm
from . import models as db


# ── helpers ────────────────────────────────────────────────
def current_user(request):
    uid = request.session.get('user_id')
    if uid:
        return db.get_user_by_id(uid)
    return None


def save_file(uploaded, subfolder):
    directory = settings.MEDIA_ROOT / subfolder
    directory.mkdir(parents=True, exist_ok=True)
    safe = uploaded.name.replace(' ', '_')
    path = directory / safe
    counter = 1
    stem, suffix = Path(safe).stem, Path(safe).suffix
    while path.exists():
        safe = f"{stem}_{counter}{suffix}"
        path = directory / safe
        counter += 1
    with open(path, 'wb+') as f:
        for chunk in uploaded.chunks():
            f.write(chunk)
    return f'{subfolder}/{safe}'


# ── MAIN ───────────────────────────────────────────────────
def index(request):
    user = current_user(request)
    top_tracks = db.get_top_tracks(10)
    top_artists = db.get_top_artists(6)
    all_tracks = db.get_all_tracks()
    playlists = db.get_user_playlists(user['id']) if user else []
    return render(request, 'music/index.html', {
        'top_tracks': top_tracks,
        'top_artists': top_artists,
        'all_tracks': all_tracks,
        'user': user,
        'playlists': playlists,
    })


# ── AUTH ───────────────────────────────────────────────────
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user, err = db.register_user(
                form.cleaned_data['username'],
                form.cleaned_data['password']
            )
            if user:
                request.session['user_id'] = user['id']
                return redirect('index')
            form.add_error(None, err)
    else:
        form = RegisterForm()
    return render(request, 'music/auth.html', {'form': form, 'mode': 'register'})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user, err = db.login_user(
                form.cleaned_data['username'],
                form.cleaned_data['password']
            )
            if user:
                request.session['user_id'] = user['id']
                return redirect('index')
            form.add_error(None, err)
    else:
        form = LoginForm()
    return render(request, 'music/auth.html', {'form': form, 'mode': 'login'})


def logout_view(request):
    request.session.flush()
    return redirect('index')


# ── UPLOAD ─────────────────────────────────────────────────
def upload(request):
    user = current_user(request)
    if not user:
        return redirect('login')
    if request.method == 'POST':
        form = UploadTrackForm(request.POST, request.FILES)
        if form.is_valid():
            audio_path = save_file(request.FILES['audio_file'], 'tracks')
            cover_path = None
            if request.FILES.get('cover_image'):
                cover_path = save_file(request.FILES['cover_image'], 'covers')
            db.add_track(
                form.cleaned_data['title'],
                form.cleaned_data['artist'],
                audio_path,
                cover_path=cover_path
            )
            return redirect('index')
    else:
        form = UploadTrackForm()
    return render(request, 'music/upload.html', {'form': form, 'user': user})


# ── PLAYER API ─────────────────────────────────────────────
@require_POST
def play_track(request, track_id):
    track = db.increment_play(track_id)
    if not track:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse({'success': True, 'play_count': track['play_count']})


# ── ARTISTS ────────────────────────────────────────────────
def artist_detail(request, artist_id):
    user = current_user(request)
    artist = db.get_artist_by_id(artist_id)
    if not artist:
        raise Http404
    tracks = db.get_artist_tracks(artist_id)
    subscribed = db.is_subscribed(user['id'], artist_id) if user else False
    sub_count = db.get_subscriber_count(artist_id)
    return render(request, 'music/artist.html', {
        'artist': artist, 'tracks': tracks,
        'user': user, 'subscribed': subscribed,
        'sub_count': sub_count,
    })


@require_POST
def toggle_subscribe(request, artist_id):
    user = current_user(request)
    if not user:
        return JsonResponse({'error': 'Not logged in'}, status=401)
    if db.is_subscribed(user['id'], artist_id):
        db.unsubscribe(user['id'], artist_id)
        subscribed = False
    else:
        db.subscribe(user['id'], artist_id)
        subscribed = True
    return JsonResponse({'subscribed': subscribed, 'count': db.get_subscriber_count(artist_id)})


# ── PLAYLISTS ──────────────────────────────────────────────
def profile(request):
    user = current_user(request)
    if not user:
        return redirect('login')
    playlists = db.get_user_playlists(user['id'])
    subscribed_artists = db.get_subscribed_artists(user['id'])
    return render(request, 'music/profile.html', {
        'user': user,
        'playlists': playlists,
        'subscribed_artists': subscribed_artists,
        'create_form': CreatePlaylistForm(),
    })


def create_playlist(request):
    user = current_user(request)
    if not user:
        return redirect('login')
    if request.method == 'POST':
        form = CreatePlaylistForm(request.POST)
        if form.is_valid():
            db.create_playlist(user['id'], form.cleaned_data['name'])
    return redirect('profile')


def playlist_detail(request, pl_id):
    user = current_user(request)
    pl = db.get_playlist_by_id(pl_id)
    if not pl:
        raise Http404
    tracks = db.get_playlist_tracks(pl_id)
    owner = db.get_user_by_id(pl['user_id'])
    return render(request, 'music/playlist.html', {
        'playlist': pl, 'tracks': tracks,
        'owner': owner, 'user': user,
    })


@require_POST
def add_to_playlist(request):
    user = current_user(request)
    if not user:
        return JsonResponse({'error': 'Not logged in'}, status=401)
    data = json.loads(request.body)
    pl_id = data.get('playlist_id')
    track_id = data.get('track_id')
    pl = db.get_playlist_by_id(pl_id)
    if not pl or pl['user_id'] != user['id']:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    added = db.add_track_to_playlist(pl_id, track_id)
    return JsonResponse({'added': added})


@require_POST
def remove_from_playlist(request, pl_id, track_id):
    user = current_user(request)
    pl = db.get_playlist_by_id(pl_id)
    if not pl or pl['user_id'] != user['id']:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    db.remove_track_from_playlist(pl_id, track_id)
    return redirect('playlist_detail', pl_id=pl_id)


@require_POST
def delete_playlist(request, pl_id):
    user = current_user(request)
    if user:
        db.delete_playlist(pl_id, user['id'])
    return redirect('profile')


def api_tracks(request):
    return JsonResponse({'tracks': db.get_all_tracks()})
