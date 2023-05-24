import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import statistics
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

# setup spotify api
scope = "playlist-read-private"
sp_oauth = SpotifyOAuth(scope=scope)
token_info = sp_oauth.get_access_token(as_dict=False)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth())

# create directory to store downloaded images
if not os.path.exists("playlist_statistics"):
    os.makedirs("playlist_statistics")

def process_playlist(playlist_id, playlist_name):
    # Get tracks from playlist
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    audio_features = []
    for track in tracks:
        audio_feature = sp.audio_features(track['track']['id'])
        if audio_feature:
            audio_features.append(audio_feature[0])

    feature_values = {feature: [track_feature[feature] for track_feature in audio_features] for feature in
                      ['energy', 'danceability', 'tempo', 'valence', 'acousticness', 'instrumentalness',
                       'liveness', 'speechiness']}

    outliers = {}
    for feature, values in feature_values.items():
        avg_feature = statistics.mean(values)
        stdev_feature = statistics.stdev(values)
        outliers[feature] = [(track['track']['name'], track_feature) for track, track_feature in zip(tracks, values)
                             if abs(track_feature - avg_feature) > 3 * stdev_feature]

    averages = {feature: statistics.mean(values) for feature, values in feature_values.items()}
    stddevs = {feature: statistics.stdev(values) for feature, values in feature_values.items()}

    filename = "playlist_statistics/" + (re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', playlist_name)).strip() + ' - audio_features.txt'
    with open(filename, 'w') as f:
        f.write(f'Playlist: {playlist_name}\n')
        f.write(f'no. tracks: {len(tracks)}\n\n')
        for feature in feature_values.keys():
            f.write(f'Average {feature}: {averages[feature]:.2f} | stdev: {stddevs[feature]:.2f}\n')
        f.write('\n')

        for feature, tracks in outliers.items():
            if tracks:
                f.write(f'{feature.capitalize()} outliers:\n')
                for track in tracks:
                    f.write(f'\t{track[0]} ({track[1]:.2f})\n')
                f.write('\n')
        print('Significant outliers printed to file.')


url = sys.argv[1]

# Check if the playlist_link is a single URL link or a file containing multiple playlist URLs
if url.startswith('http'):
    # Process a single playlist URL
    playlist_id = re.search(r"playlist\/(\w+)", url).group(1)
    playlist = sp.playlist(playlist_id)
    playlist_name = playlist['name']
    process_playlist(playlist_id,playlist_name)
else:
    # Read playlist URLs from a text file
    with open(url, "r") as f:
        playlist_urls = [line.strip() for line in f]

    for playlist_url in playlist_urls:
        playlist = sp.playlist(playlist_url)
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        process_playlist(playlist_id,playlist_name)