# %%
import os
import datetime

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import pyarrow as pa
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv

# %% 

print("Script started", flush = True)

# Load environment variables
load_dotenv()

print("Client ID exists:", "CLIENT_ID" in os.environ, flush = True)
print("Client secret exists:", "CLIENT_SECRET" in os.environ, flush = True)
print("Refresh token exists:", "REFRESH_TOKEN" in os.environ, flush = True)


print("Calling Spotify token endpoint", flush = True)

# %%
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
    os.environ["REFRESH_TOKEN"]
)

sp = spotipy.Spotify(auth = token_info["access_token"])

print("Calling recently played endpoint", flush = True)
# Fetch recently played tracks
results = sp.current_user_recently_played(limit=50)
print(results)


# %%
song_list = []

# Loop through dictionary and  write to dataframe
for item in results['items']:
    track = item['track']
    song = track['name']
    artists = ', '.join(artist['name'] for artist in track['artists'])
    main_artist = track['artists'][0]['name']
    featured_artists = ', '.join(artist['name'] for artist in track['artists'][1:])
    album = track['album']['name']
    release_date = track['album']['release_date']
    played_at = pd.to_datetime(item['played_at']).tz_convert('America/Chicago')
    
    song_list.append({
        'song': song,
        'artists': artists,
        'main_artist': main_artist,
        'featured_artists': featured_artists,
        'album': album,
        'release_date': release_date,
        'played_at': played_at
    })

recently_played = pd.DataFrame(song_list)
recently_played['played_at'] = (pd.to_datetime(recently_played['played_at'])
                                .dt.tz_convert('UTC')
                                .dt.tz_localize(None)
                                )
recently_played['last_updated'] = datetime.datetime.now()

print(f'Scraped {len(recently_played)} records.')

# %%
def sf_connect():
    cnx = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )
    return cnx

# %%
with sf_connect() as conn:

    with conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(played_at)
            FROM SPOTIFY.RAW.RECENTLY_PLAYED
        """)
        
        max_date = cur.fetchone()[0]

    if max_date is None:
        recently_played_to_sf = recently_played.copy()
    else:
        recently_played_to_sf = recently_played[recently_played['played_at'] > max_date]

    write_pandas(
        conn=conn,
        df=recently_played_to_sf,
        table_name='RECENTLY_PLAYED',
        schema='RAW',
        database='SPOTIFY',
        auto_create_table=False,
        quote_identifiers=False,
        use_logical_type=True
    )
# %%
print(f'Added {len(recently_played_to_sf)} records to Snowflake.')

# %%
