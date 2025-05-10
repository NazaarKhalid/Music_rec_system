from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Song, Artist, Genre, Playlist, PlaylistSong
from . import db
import requests
from sqlalchemy import func

views = Blueprint('views', __name__)

@views.route('/', methods=['GET'])
@login_required
def home():
    songs = Song.query.all()
    artists = Artist.query.all()
    genres = Genre.query.all()
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    recommendations = get_playlist_recommendations(current_user.id, limit=10)
    return render_template(
        "home.html", 
        user=current_user,
        songs=songs,
        artists=artists,
        genres=genres,
        playlists=playlists,
        recommendations=recommendations
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

@views.route('/import-deezer-song', methods=['POST'])
@login_required
def import_deezer_song():
    deezer_id = request.form.get('deezer_id')
    title = request.form.get('title')
    artist_name = request.form.get('artist')
    album = request.form.get('album')
    image_url = request.form.get('image_url')
    duration = request.form.get('duration')
    genre_id = request.form.get('genre_id')

    artist = Artist.query.filter_by(name=artist_name).first()
    if not artist:
        artist = Artist(name=artist_name)
        db.session.add(artist)
        db.session.commit()

    song = Song.query.filter_by(title=title, artist_id=artist.id).first()
    if not song:
        song = Song(
            title=title,
            artist_id=artist.id,
            genre_id=genre_id,
            duration=duration,
            song_metadata={"deezer_id": deezer_id, "album": album},
            image_url=image_url
        )
        db.session.add(song)
        db.session.commit()

    flash(f'Song "{title}" imported successfully!', category='success')
    return redirect(url_for('views.home'))
    
@views.route('/add-to-playlist', methods=['GET', 'POST'])
@login_required
def add_to_playlist():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    selected_playlist = None
    songs = []
    query = request.args.get('q', '').strip()

    if request.method == 'POST':
        playlist_id = request.form.get('playlist_id')
        song_ids = request.form.getlist('song_ids')
        if not playlist_id:
            flash('Please select a playlist.', category='error')
            return redirect(url_for('views.add_to_playlist'))

        playlist = Playlist.query.get(int(playlist_id))
        for song_id in song_ids:
            if not PlaylistSong.query.filter_by(playlist_id=playlist.id, song_id=int(song_id)).first():
                playlist_song = PlaylistSong(playlist_id=playlist.id, song_id=int(song_id))
                db.session.add(playlist_song)
        db.session.commit()
        flash('Songs added to playlist successfully!', category='success')
        return redirect(url_for('views.view_playlists'))

    if playlists:
        selected_playlist_id = request.args.get('playlist_id')
        if selected_playlist_id:
            selected_playlist = Playlist.query.get(int(selected_playlist_id))
            existing_song_ids = {ps.song_id for ps in selected_playlist.songs}
            if query:
                songs = Song.query.join(Artist).filter(
                    ((Song.title.ilike(f'%{query}%')) | (Artist.name.ilike(f'%{query}%'))) &
                    (~Song.id.in_(existing_song_ids))
                ).all()
            else:
                songs = Song.query.filter(~Song.id.in_(existing_song_ids)).all()
        else:
            songs = []
    return render_template("add_to_playlist.html", user=current_user, playlists=playlists, songs=songs, selected_playlist=selected_playlist, query=query)

@views.route('/remove-song-from-playlist/<int:playlist_id>/<int:song_id>', methods=['POST'])
@login_required
def remove_song_from_playlist(playlist_id, song_id):
    playlist_song = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first()
    if playlist_song:
        db.session.delete(playlist_song)
        db.session.commit()
        flash('Song removed from playlist!', category='success')
    else:
        flash('Song not found in playlist.', category='error')
    return redirect(url_for('views.update_playlist', playlist_id=playlist_id))

@views.route('/update-playlist/<int:playlist_id>', methods=['GET'])
@login_required
def update_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
    if not playlist:
        flash('Playlist not found or not authorized.', category='error')
        return redirect(url_for('views.view_playlists'))
    return render_template("update_playlist.html", user=current_user, playlist=playlist)

@views.route('/confirm-import-deezer-song', methods=['POST'])
@login_required
def confirm_import_deezer_song():
    song_data = {
        'deezer_id': request.form.get('deezer_id'),
        'title': request.form.get('title'),
        'artist': request.form.get('artist'),
        'album': request.form.get('album'),
        'image_url': request.form.get('image_url'),
        'duration': request.form.get('duration')
    }
    genres = Genre.query.all()
    return render_template("confirm_import.html", user=current_user, song_data=song_data, genres=genres)

def get_playlist_recommendations(user_id, limit=10):
    user_playlist_ids = [pl.id for pl in Playlist.query.filter_by(user_id=user_id).all()]
    user_song_ids = db.session.query(PlaylistSong.song_id).filter(PlaylistSong.playlist_id.in_(user_playlist_ids)).subquery()

    top_genres = db.session.query(
        Song.genre_id, func.count(Song.id).label('genre_count')
    ).filter(Song.id.in_(user_song_ids)).group_by(Song.genre_id).order_by(func.count(Song.id).desc()).all()

    if top_genres:
        genre_ids = [g[0] for g in top_genres]
        recommendations = Song.query.filter(
            Song.genre_id.in_(genre_ids),
            ~Song.id.in_(user_song_ids)
        ).limit(limit).all()
    else:
        recommendations = Song.query.limit(limit).all()
    return recommendations