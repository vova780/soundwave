import json
import os
from pathlib import Path
from django.conf import settings
from datetime import datetime


def get_db():
    db_path = settings.JSON_DB_PATH
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        default_db = {
            "tracks": [], "artists": [], "users": [],
            "playlists": [], "subscriptions": [],
            "next_track_id": 1, "next_artist_id": 1,
            "next_user_id": 1, "next_playlist_id": 1
        }
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(default_db, f, ensure_ascii=False, indent=2)
        return default_db
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # migrate old DBs
    for key in ["users", "playlists", "subscriptions"]:
        if key not in data:
            data[key] = []
    for key in ["next_user_id", "next_playlist_id"]:
        if key not in data:
            data[key] = 1
    return data


def save_db(db):
    db_path = settings.JSON_DB_PATH
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ── ARTISTS ────────────────────────────────────────────────
def get_or_create_artist(name):
    db = get_db()
    for artist in db['artists']:
        if artist['name'].lower() == name.lower():
            return artist
    artist = {
        'id': db['next_artist_id'],
        'name': name,
        'created_at': datetime.now().isoformat()
    }
    db['artists'].append(artist)
    db['next_artist_id'] += 1
    save_db(db)
    return artist


def get_top_artists(limit=6):
    db = get_db()
    artist_plays = {}
    for track in db['tracks']:
        aid = track['artist_id']
        artist_plays[aid] = artist_plays.get(aid, 0) + track['play_count']

    result = []
    for artist in db['artists']:
        plays = artist_plays.get(artist['id'], 0)
        track_count = sum(1 for t in db['tracks'] if t['artist_id'] == artist['id'])
        result.append({**artist, 'total_plays': plays, 'track_count': track_count})

    return sorted(result, key=lambda x: x['total_plays'], reverse=True)[:limit]


def get_artist_by_id(artist_id):
    db = get_db()
    for a in db['artists']:
        if a['id'] == artist_id:
            return a
    return None


def get_artist_tracks(artist_id):
    db = get_db()
    tracks = [t for t in db['tracks'] if t['artist_id'] == artist_id]
    return sorted(tracks, key=lambda x: x['play_count'], reverse=True)


# ── TRACKS ─────────────────────────────────────────────────
def add_track(title, artist_name, file_path, cover_path=None, duration=None):
    # Read DB once, create artist inline if needed (fixes bug where artist
    # was saved but then a fresh get_db() load missed it in the same call)
    db = get_db()
    artist = None
    for a in db['artists']:
        if a['name'].lower() == artist_name.lower():
            artist = a
            break
    if artist is None:
        artist = {
            'id': db['next_artist_id'],
            'name': artist_name,
            'created_at': datetime.now().isoformat()
        }
        db['artists'].append(artist)
        db['next_artist_id'] += 1

    track = {
        'id': db['next_track_id'],
        'title': title,
        'artist_id': artist['id'],
        'artist_name': artist['name'],
        'file_path': file_path,
        'cover_path': cover_path,
        'duration': duration,
        'play_count': 0,
        'created_at': datetime.now().isoformat()
    }
    db['tracks'].append(track)
    db['next_track_id'] += 1
    save_db(db)
    return track


def get_all_tracks():
    db = get_db()
    return sorted(db['tracks'], key=lambda x: x['play_count'], reverse=True)


def get_top_tracks(limit=10):
    return get_all_tracks()[:limit]


def get_track_by_id(track_id):
    db = get_db()
    for t in db['tracks']:
        if t['id'] == track_id:
            return t
    return None


def increment_play(track_id):
    db = get_db()
    for track in db['tracks']:
        if track['id'] == track_id:
            track['play_count'] += 1
            save_db(db)
            return track
    return None


# ── USERS ──────────────────────────────────────────────────
def register_user(username, password):
    db = get_db()
    if any(u['username'].lower() == username.lower() for u in db['users']):
        return None, 'Имя пользователя уже занято'
    user = {
        'id': db['next_user_id'],
        'username': username,
        'password': password,  # plain text as requested
        'created_at': datetime.now().isoformat()
    }
    db['users'].append(user)
    db['next_user_id'] += 1
    save_db(db)
    return user, None


def login_user(username, password):
    db = get_db()
    for u in db['users']:
        if u['username'].lower() == username.lower() and u['password'] == password:
            return u, None
    return None, 'Неверный логин или пароль'


def get_user_by_id(user_id):
    db = get_db()
    for u in db['users']:
        if u['id'] == user_id:
            return u
    return None


# ── PLAYLISTS ──────────────────────────────────────────────
def create_playlist(user_id, name):
    db = get_db()
    pl = {
        'id': db['next_playlist_id'],
        'user_id': user_id,
        'name': name,
        'track_ids': [],
        'created_at': datetime.now().isoformat()
    }
    db['playlists'].append(pl)
    db['next_playlist_id'] += 1
    save_db(db)
    return pl


def get_user_playlists(user_id):
    db = get_db()
    return [p for p in db['playlists'] if p['user_id'] == user_id]


def get_playlist_by_id(pl_id):
    db = get_db()
    for p in db['playlists']:
        if p['id'] == pl_id:
            return p
    return None


def add_track_to_playlist(pl_id, track_id):
    db = get_db()
    for p in db['playlists']:
        if p['id'] == pl_id:
            if track_id not in p['track_ids']:
                p['track_ids'].append(track_id)
                save_db(db)
                return True
            return False  # already in
    return False


def remove_track_from_playlist(pl_id, track_id):
    db = get_db()
    for p in db['playlists']:
        if p['id'] == pl_id:
            if track_id in p['track_ids']:
                p['track_ids'].remove(track_id)
                save_db(db)
                return True
    return False


def delete_playlist(pl_id, user_id):
    db = get_db()
    db['playlists'] = [p for p in db['playlists'] if not (p['id'] == pl_id and p['user_id'] == user_id)]
    save_db(db)


def get_playlist_tracks(pl_id):
    pl = get_playlist_by_id(pl_id)
    if not pl:
        return []
    db = get_db()
    track_map = {t['id']: t for t in db['tracks']}
    return [track_map[tid] for tid in pl['track_ids'] if tid in track_map]


# ── SUBSCRIPTIONS ──────────────────────────────────────────
def subscribe(user_id, artist_id):
    db = get_db()
    exists = any(s for s in db['subscriptions']
                 if s['user_id'] == user_id and s['artist_id'] == artist_id)
    if not exists:
        db['subscriptions'].append({'user_id': user_id, 'artist_id': artist_id})
        save_db(db)


def unsubscribe(user_id, artist_id):
    db = get_db()
    db['subscriptions'] = [s for s in db['subscriptions']
                           if not (s['user_id'] == user_id and s['artist_id'] == artist_id)]
    save_db(db)


def is_subscribed(user_id, artist_id):
    db = get_db()
    return any(s for s in db['subscriptions']
               if s['user_id'] == user_id and s['artist_id'] == artist_id)


def get_subscribed_artists(user_id):
    db = get_db()
    artist_ids = {s['artist_id'] for s in db['subscriptions'] if s['user_id'] == user_id}
    result = []
    for a in db['artists']:
        if a['id'] in artist_ids:
            plays = sum(t['play_count'] for t in db['tracks'] if t['artist_id'] == a['id'])
            tc = sum(1 for t in db['tracks'] if t['artist_id'] == a['id'])
            result.append({**a, 'total_plays': plays, 'track_count': tc})
    return result


def get_subscriber_count(artist_id):
    db = get_db()
    return sum(1 for s in db['subscriptions'] if s['artist_id'] == artist_id)
