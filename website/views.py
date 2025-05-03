from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Song, Artist, Genre, Playlist, PlaylistSong
from . import db
import requests

views = Blueprint('views', __name__)

@views.route('/', methods=['GET'])
@login_required
def home():
    songs = Song.query.all()
    artists = Artist.query.all()
    genres = Genre.query.all()
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "home.html", 
        user=current_user,
        songs=songs,
        artists=artists,
        genres=genres,
        playlists=playlists
    )

@views.route('/songs', methods=['GET'])
@login_required
def songs():
    songs = Song.query.all()
    return render_template("songs.html", user=current_user, songs=songs)

@views.route('/artists', methods=['GET'])
@login_required
def artists():
    artists = Artist.query.all()
    return render_template("artists.html", user=current_user, artists=artists)

@views.route('/create-playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    if request.method == 'POST':
        playlist_name = request.form.get('playlist_name')
        song_ids = request.form.getlist('song_ids')

        if not playlist_name:
            flash('Playlist name is required.', category='error')
            return redirect(url_for('views.create_playlist'))

        new_playlist = Playlist(user_id=current_user.id, name=playlist_name)
        db.session.add(new_playlist)
        db.session.commit()

        for song_id in song_ids:
            playlist_song = PlaylistSong(playlist_id=new_playlist.id, song_id=int(song_id))
            db.session.add(playlist_song)
        db.session.commit()

        flash('Playlist created successfully!', category='success')
        return redirect(url_for('views.home'))

    query = request.args.get('q', '').strip()
    if query:
        songs = Song.query.join(Artist).filter(
            (Song.title.ilike(f'%{query}%')) |
            (Artist.name.ilike(f'%{query}%'))
        ).all()
    else:
        songs = Song.query.all()
    return render_template("create_playlist.html", user=current_user, songs=songs, query=query)

@views.route('/playlists', methods=['GET'])
@login_required
def view_playlists():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return render_template("view_playlists.html", user=current_user, playlists=playlists)

@views.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        results = Song.query.join(Artist).join(Genre).filter(
            (Song.title.ilike(f'%{query}%')) |
            (Artist.name.ilike(f'%{query}%')) |
            (Genre.name.ilike(f'%{query}%'))
        ).all()
    return render_template("search_results.html", user=current_user, query=query, results=results)

@views.route('/delete-playlist/<int:playlist_id>', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
    if playlist:
        # Delete all PlaylistSong entries for this playlist
        PlaylistSong.query.filter_by(playlist_id=playlist.id).delete()
        db.session.delete(playlist)
        db.session.commit()
        flash('Playlist deleted successfully!', category='success')
    else:
        flash('Playlist not found or not authorized.', category='error')
    return redirect(url_for('views.view_playlists'))

@views.route('/deezer-search', methods=['GET', 'POST'])
@login_required
def deezer_search():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('q', '').strip()
        if query:
            r = requests.get(f"https://api.deezer.com/search", params={'q': query})
            if r.status_code == 200:
                results = r.json().get('data', [])
    return render_template("deezer_search.html", user=current_user, results=results, query=query)