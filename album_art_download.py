import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import os
import sys
import json
import re

# read client ID and client secret from keys.json
with open('keys.json') as f:
    secrets = json.load(f)['secrets']
client_id = next((s['value'] for s in secrets if s['id'] == 'client-id'), None)
client_secret = next((s['value'] for s in secrets if s['id'] == 'client-secret'), None)

# set environment variables
os.environ["SPOTIPY_CLIENT_ID"] = client_id
os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:3000"

# define scope
scope = "playlist-read-private"
sp_oauth = SpotifyOAuth(scope=scope)
token_info = sp_oauth.get_access_token(as_dict=False)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth())

playlists_list = sys.argv[1]

# read playlist urls from txt file
with open(playlists_list, "r") as f:
    playlist_urls = [line.strip() for line in f]

# create directory to store downloaded images
if not os.path.exists("playlist_images"):
    os.makedirs("playlist_images")

# download cover art for each playlist
for url in playlist_urls:
    # get playlist information
    playlist_id = re.search(r"playlist\/(\w+)", url).group(1)
    playlist = sp.playlist(playlist_id)

    # get cover art url
    image_url = playlist['images'][0]['url']

    # download and save the image
    response = requests.get(image_url)
    file_name = "playlist_images/" + (re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', playlist['name'])).strip() + ".jpg"
    with open(file_name, "wb") as f:
        f.write(response.content)
        print(f"Saved cover art for {playlist['name']} playlist")