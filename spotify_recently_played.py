import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
import datetime as dt
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Authenticate Spotify API
sp = spotipy.Spotify(auth_manager = SpotifyOAuth(
    client_id = os.environ['CLIENT_ID'],
    client_secret = os.environ['CLIENT_SECRET'],
    redirect_uri = 'http://127.0.0.1:8080',
    scope = 'user-read-recently-played'
))

# Fetch recently played tracks
results = sp.current_user_recently_played(limit = 50)

song_list = []

# Loop through dictionary and  write to dataframe
for item in results['items']:
    track = item['track']
    song = track['name']
    artists = ', '.join(artist['name'] for artist in track['artists'])
    album = track['album']['name']
    # isrc = track['external_ids']['isrc']
    played_at = pd.to_datetime(item['played_at']).tz_convert('America/Chicago')
    
    song_list.append({
        'song': song,
        'artists': artists,
        'album': album,
        # 'isrc': isrc,
        'played_at': played_at
    })

df = pd.DataFrame(song_list)

print(df.head())
