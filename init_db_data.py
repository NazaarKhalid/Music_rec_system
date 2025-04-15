from website import create_app, db
from website.models import Genre, Artist, Song
from datetime import datetime

app = create_app()

def add_initial_data():
    with app.app_context():
        genres = [
            "Pop", "Rock", "Hip Hop", "Jazz", "Classical", 
            "Electronic", "R&B", "Country", "Metal", "Folk"
        ]
        
        for genre_name in genres:
            if not Genre.query.filter_by(name=genre_name).first():
                genre = Genre(name=genre_name)
                db.session.add(genre)
        
        db.session.commit()
        print("Added initial genres")

        artists = [
            "The Beatles", "Queen", "Michael Jackson", "Taylor Swift",
            "Ed Sheeran", "Drake", "Lady Gaga", "Coldplay"
        ]
        
        for artist_name in artists:
            if not Artist.query.filter_by(name=artist_name).first():
                artist = Artist(name=artist_name)
                db.session.add(artist)
        
        db.session.commit()
        print("Added initial artists")

        sample_songs = [
            {
                "title": "Bohemian Rhapsody",
                "artist_name": "Queen",
                "genre_name": "Rock",
                "release_date": datetime(1975, 10, 31),
                "duration": 354
            },
            {
                "title": "Shape of You",
                "artist_name": "Ed Sheeran",
                "genre_name": "Pop",
                "release_date": datetime(2017, 1, 6),
                "duration": 233
            },
            {
                "title": "Billie Jean",
                "artist_name": "Michael Jackson",
                "genre_name": "Pop",
                "release_date": datetime(1983, 1, 2),
                "duration": 294
            },
            {
                "title": "Yesterday",
                "artist_name": "The Beatles",
                "genre_name": "Rock",
                "release_date": datetime(1965, 8, 6),
                "duration": 125
            }
        ]

        for song_data in sample_songs:
            artist = Artist.query.filter_by(name=song_data["artist_name"]).first()
            genre = Genre.query.filter_by(name=song_data["genre_name"]).first()
            
            if not Song.query.filter_by(title=song_data["title"], artist_id=artist.id).first():
                song = Song(
                    title=song_data["title"],
                    artist_id=artist.id,
                    genre_id=genre.id,
                    release_date=song_data["release_date"],
                    duration=song_data["duration"],
                    song_metadata={"added_by": "system"}
                )
                db.session.add(song)
        
        db.session.commit()
        print("Added initial songs")

if __name__ == "__main__":
    try:
        add_initial_data()
        print("Successfully initialized database with sample data!")
    except Exception as e:
        print("An error occurred:", e) 