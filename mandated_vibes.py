import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import statistics
import sys
import json

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

# create SpotifyOAuth object
sp_oauth = SpotifyOAuth(scope=scope)

# get access token
# get access token
token_info = sp_oauth.get_access_token(as_dict=False)

# create Spotify object
sp = spotipy.Spotify(auth_manager=SpotifyOAuth())

# get playlist ID
playlist_link = sys.argv[1]
playlist = sp.playlist(playlist_link)
playlist_id = playlist['id']
playlist_name = playlist['name']

# Get tracks from playlist
tracks = sp.playlist_tracks(playlist_id)

audio_features = []
for track in tracks['items']:
    features = sp.audio_features(track['track']['id'])[0]
    audio_features.append(features)

# Calculate average values for audio features
feature_values = {
    'energy': [],
    'danceability': [],
    'tempo': [],
    'valence': [],
    'acousticness': [],
    'instrumentalness': [],
    'liveness': [],
    'speechiness': []
}
for feature in feature_values.keys():
    feature_values[feature] = [track_feature[feature] for track_feature in audio_features]

outliers = {}
for feature, values in feature_values.items():
    avg_feature = statistics.mean(values)
    stdev_feature = statistics.stdev(values)
    for i, track_feature in enumerate(values):
        if abs(track_feature - avg_feature) > 2 * stdev_feature:
            if feature not in outliers:
                outliers[feature] = []
            track_name = tracks['items'][i]['track']['name']
            outliers[feature].append((track_name, track_feature))

# Calculate average values for audio features
energy_values = [feature['energy'] for feature in audio_features]
danceability_values = [feature['danceability'] for feature in audio_features]
tempo_values = [feature['tempo'] for feature in audio_features]
valence_values = [feature['valence'] for feature in audio_features]
acousticness_values = [feature['acousticness'] for feature in audio_features]
instrumentalness_values = [feature['instrumentalness'] for feature in audio_features]
liveness_values = [feature['liveness'] for feature in audio_features]
speechiness_values = [feature['speechiness'] for feature in audio_features]

avg_energy = statistics.mean(energy_values)
avg_danceability = statistics.mean(danceability_values)
avg_tempo = statistics.mean(tempo_values)
avg_valence = statistics.mean(valence_values)
avg_acousticness = statistics.mean(acousticness_values)
avg_instrumentalness = statistics.mean(instrumentalness_values)
avg_liveness = statistics.mean(liveness_values)
avg_speechiness = statistics.mean(speechiness_values)

# Print significant outliers
filename = str(playlist_name.replace(':','') + ' - audio_features.txt')
with open(filename, 'w') as f:
    f.write(f'Playlist: {playlist_name}\n\n')

    f.write('Average energy: ' + str(avg_energy) + '\n')
    f.write('Average danceability: ' + str(avg_danceability) + '\n')
    f.write('Average tempo: ' + str(avg_tempo) + '\n')
    f.write('Average valence: ' + str(avg_valence) + '\n')
    f.write('Average acousticness: ' + str(avg_acousticness) + '\n')
    f.write('Average instrumentalness: ' + str(avg_instrumentalness) + '\n')
    f.write('Average liveness: ' + str(avg_liveness) + '\n')
    f.write('Average speechiness: ' + str(avg_speechiness) + '\n\n')

    for feature, tracks in outliers.items():
        f.write(f'{feature.capitalize()} outliers:\n')
        for track in tracks:
            track_name = track[0]
            track_feature = track[1]
            f.write(f'\t{track_name} ({track_feature:.2f})\n')
            #print(f'{track_name} is a significant outlier in {feature}')
        f.write('\n')
    print('Significant outliers printed to file.')