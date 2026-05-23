const audio = document.getElementById('audioEl');
const playPauseBtn = document.getElementById('playPauseBtn');
const playerTitle = document.getElementById('playerTitle');
const playerArtist = document.getElementById('playerArtist');
const playerDisc = document.getElementById('playerDisc');
const playerCover = document.getElementById('playerCover');
const playerDiscIcon = document.getElementById('playerDiscIcon');
const progressFill = document.getElementById('progressFill');
const timeCur = document.getElementById('timeCur');
const timeTotal = document.getElementById('timeTotal');

let currentTrackId = null;
let trackQueue = [];
let currentIndex = 0;
let isPlaying = false;
let pendingPlaylistTrackId = null;

function getCsrf() {
    return document.cookie.split(';').map(c => c.trim())
        .find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
}

function fmtTime(s) {
    if (isNaN(s) || !isFinite(s)) return '0:00';
    const m = Math.floor(s / 60), sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
}

function buildQueue() {
    trackQueue = [];
    document.querySelectorAll('.track-row').forEach(row => {
        const attr = row.getAttribute('onclick');
        if (!attr) return;
        const m = attr.match(/playTrack\((\d+),'([^']*)','([^']*)','([^']*)'(?:,'([^']*)'\)|\))/);
        if (m) trackQueue.push({ id: +m[1], title: m[2], artist: m[3], src: m[4], cover: m[5] || '' });
    });
}

function playTrack(id, title, artist, src, cover) {
    buildQueue();
    const idx = trackQueue.findIndex(t => t.id === id);
    if (idx >= 0) currentIndex = idx;

    currentTrackId = id;
    playerTitle.textContent = title;
    playerArtist.textContent = artist;
    audio.src = src;
    audio.volume = document.getElementById('volumeSlider').value;
    audio.play();
    isPlaying = true;
    playPauseBtn.textContent = '⏸';
    playerDisc.classList.add('spinning');

    if (cover) {
        playerCover.src = cover;
        playerCover.style.display = 'block';
        playerDiscIcon.style.display = 'none';
    } else {
        playerCover.style.display = 'none';
        playerDiscIcon.style.display = '';
    }

    document.querySelectorAll('.track-row').forEach(r => r.classList.remove('track-row--active'));
    const activeRow = document.getElementById('track-' + id);
    if (activeRow) activeRow.classList.add('track-row--active');

    fetch(`/play/${id}/`, { method: 'POST', headers: { 'X-CSRFToken': getCsrf() } });
}

function togglePlay() {
    if (!audio.src || audio.src === window.location.href) return;
    if (isPlaying) {
        audio.pause(); isPlaying = false;
        playPauseBtn.textContent = '▶';
        playerDisc.classList.remove('spinning');
    } else {
        audio.play(); isPlaying = true;
        playPauseBtn.textContent = '⏸';
        playerDisc.classList.add('spinning');
    }
}

function nextTrack() {
    if (!trackQueue.length) return;
    currentIndex = (currentIndex + 1) % trackQueue.length;
    const t = trackQueue[currentIndex];
    playTrack(t.id, t.title, t.artist, t.src, t.cover);
}

function prevTrack() {
    if (!trackQueue.length) return;
    if (audio.currentTime > 3) { audio.currentTime = 0; return; }
    currentIndex = (currentIndex - 1 + trackQueue.length) % trackQueue.length;
    const t = trackQueue[currentIndex];
    playTrack(t.id, t.title, t.artist, t.src, t.cover);
}

function seekTo(e) {
    const bar = document.getElementById('progressBar');
    const rect = bar.getBoundingClientRect();
    audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
}

function setVolume(v) { audio.volume = v; }

function scrollCarousel(id, dir) {
    document.getElementById(id).scrollBy({ left: dir * 320, behavior: 'smooth' });
}

audio.addEventListener('timeupdate', () => {
    if (!audio.duration) return;
    progressFill.style.width = (audio.currentTime / audio.duration * 100) + '%';
    timeCur.textContent = fmtTime(audio.currentTime);
    timeTotal.textContent = fmtTime(audio.duration);
});
audio.addEventListener('ended', nextTrack);

function openPlaylistModal(e, trackId) {
    e.stopPropagation();
    pendingPlaylistTrackId = trackId;
    const modal = document.getElementById('playlistModal');
    if (modal) modal.classList.add('open');
}

function closeModal(e) {
    if (e.target === document.getElementById('playlistModal'))
        document.getElementById('playlistModal').classList.remove('open');
}

function doAddToPlaylist(plId) {
    fetch('/api/playlist/add/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_id: plId, track_id: pendingPlaylistTrackId })
    }).then(r => r.json()).then(d => {
        document.getElementById('playlistModal').classList.remove('open');
        if (d.added) showToast('Додано до плейлисту!');
        else showToast('Вже є в плейлисті');
    });
}

function showToast(msg) {
    let t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:100px;left:50%;transform:translateX(-50%);background:#c8ff00;color:#0a0a0f;padding:.5rem 1.2rem;border-radius:2rem;font-weight:700;z-index:500;font-family:Syne,sans-serif;font-size:.9rem;';
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2500);
}