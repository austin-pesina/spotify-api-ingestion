import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
import datetime as dt
from sqlalchemy import create_engine
from dotenv import load_dotenv

print("Script started", flush = True)

# Load environment variables
load_dotenv()

print("Client ID exists:", "CLIENT_ID" in os.environ, flush = True)
print("Client secret exists:", "CLIENT_SECRET" in os.environ, flush = True)
print("Refresh token exists:", "SPOTIFY_REFRESH_TOKEN" in os.environ, flush = True)


print("Calling Spotify token endpoint", flush = True)

# Authenticate Spotify API
auth_manager = SpotifyOAuth(
    client_id = os.environ["CLIENT_ID"],
    client_secret = os.environ["CLIENT_SECRET"],
    redirect_uri = "http://127.0.0.1:8080",
    scope = "user-read-recently-played",
    cache_path = None,
    open_browser = False
)

print("Refreshing Spotify access token", flush = True)

token_info = auth_manager.refresh_access_token(
    os.environ["SPOTIFY_REFRESH_TOKEN"]
)

sp = spotipy.Spotify(auth = token_info["access_token"])

print("Calling recently played endpoint", flush = True)
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
