import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sys
import os
import json
import re
import requests

# read client ID and client secret from keys.json
with open('keys.json') as f:
    secrets = json.load(f)['secrets']
client_id = next((s['value'] for s in secrets if s['id'] == 'client-id'), None)
client_secret = next((s['value'] for s in secrets if s['id'] == 'client-secret'), None)

# set environment variables
os.environ["SPOTIPY_CLIENT_ID"] = client_id
os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:3000"

# setup spotify auth
scope = "playlist-read-private playlist-modify-private playlist-modify-public ugc-image-upload"
sp_oauth = SpotifyOAuth(scope=scope)
token_info = sp_oauth.get_access_token(as_dict=False)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth())

playlists_list = sys.argv[1]

# read playlist urls from txt file
with open(playlists_list, "r") as f:
    playlist_urls = [line.strip() for line in f]

# download cover art for each playlist
for url in playlist_urls:
    # get playlist information
    playlist_id = re.search(r"playlist\/(\w+)", url).group(1)
    playlist = sp.playlist(playlist_id)
    new_playlist_name = 'DnD - ' + playlist['name']
    new_playlist = sp.user_playlist_create(sp.me()['id'], new_playlist_name, public=False, collaborative=False)
    # Add all tracks from original playlist to new playlist
    tracks = sp.playlist_tracks(playlist['id'])
    track_urls = [track['track']['uri'] for track in tracks['items']]
    sp.playlist_add_items(new_playlist['id'], track_urls)
    #image_url = playlist['images'][0]['url']
    #response = requests.get(image_url)
    #cover_data = response.content
    #sp.playlist_upload_cover_image(new_playlist['id'], cover_data)
    print(f"Duplicated {playlist['name']} playlist")