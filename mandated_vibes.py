import argparse
import json
import os
import pprint
import re
import statistics
import sys

import emoji
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Read client ID and client secret from keys.json
with open('keys.json') as f:
    secrets = json.load(f)['secrets']
client_id = next((s['value'] for s in secrets if s['id'] == 'client-id'), None)
client_secret = next((s['value']
                     for s in secrets if s['id'] == 'client-secret'), None)

# Set environment variables
os.environ["SPOTIPY_CLIENT_ID"] = client_id
os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:3000"

# Define scope and authenticate Spotify API
scope = "playlist-read-private playlist-modify-private playlist-modify-public ugc-image-upload"
sp_oauth = SpotifyOAuth(scope=scope)
token_info = sp_oauth.get_access_token(as_dict=False)
access_token = token_info
sp = spotipy.Spotify(auth_manager=SpotifyOAuth())


def sanitise_playlist_name(playlist_name):
    keywords = r'(DnD|D&D|Fantasy|Music|Rpg|RPG|for|/)'
    cleaned_name = re.sub(keywords, '', playlist_name)
    cleaned_name = emoji.replace_emoji(cleaned_name, replace='').strip()
    return cleaned_name


def read_playlist(link):
    # Reads the input playlist from either a txt file or a Spotify playlist link
    # Returns a list of playlists with name and tracks
    playlists = []

    # Check if the link is a txt file
    if link.endswith('.txt'):
        with open(link, 'r') as file:
            lines = file.readlines()

        # Check if each line contains both the name and the link
        if any('\t' in line for line in lines):
            for line in lines:
                name, url = line.strip().split('\t')
                playlist_id = re.search(r"playlist\/(\w+)", url).group(1)
                playlists.append({
                    'name': name,
                    'id': playlist_id,
                    'tracks': get_playlist_tracks(playlist_id)
                })
        else:
            for url in lines:
                playlist_id = re.search(r"playlist\/(\w+)", url).group(1)
                playlists.append({
                    'name': sanitise_playlist_name(get_playlist_name(playlist_id)),
                    'id': playlist_id,
                    'tracks': get_playlist_tracks(playlist_id)
                })

    # Assume the link is a Spotify playlist link
    else:
        playlist_id = re.search(r"playlist\/(\w+)", link).group(1)
        playlists.append({
            'name': sanitise_playlist_name(get_playlist_name(playlist_id)),
            'id': playlist_id,
            'tracks': get_playlist_tracks(playlist_id)
        })

    return playlists


def get_playlist_name(playlist_id):
    # Retrieves the name of the playlist from its ID
    playlist = sp.playlist(playlist_id)
    return playlist['name']


def get_playlist_tracks(playlist_id):
    # Retrieves all tracks from the playlist with the given ID
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks


def duplicate_playlist(playlist, new_name=None):
    # Duplicate the playlist and optionally set a new name
    # Get the name of the original playlist
    original_name = playlist['name']
    # Use the new name if provided, otherwise keep the original name
    name = new_name if new_name else original_name

    # Create a new playlist with the specified name
    new_playlist = sp.user_playlist_create(user=sp.me()['id'], name=name)

    # Retrieve the tracks from the original playlist
    tracks = get_playlist_tracks(playlist['id'])

    # Extract the track URIs from the tracks
    track_uris = [track['track']['uri'] for track in tracks]

    # Add tracks to the new playlist in chunks
    for i in range(0, len(track_uris), 100):
        try:
            sp.playlist_add_items(new_playlist['id'], track_uris[i:i+100])
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 400 and e.code == -1 and "Unsupported URL / URI" in e.msg:
                # Skip the track if it's a local file with an unsupported URI
                print("Skipping local file:", e.msg)
            else:
                # Handle other Spotify API errors
                print("Error adding tracks to playlist:", e.msg)

    print(f"Playlist '{original_name}' duplicated as '{name}'")
    return new_playlist


def analyse_tracks(playlists):
    # Analyze the tracks in the playlists and identify outliers
    # Returns a dictionary of outliers per playlist

    outliers = {}
    for playlist in playlists:
        playlist_name = playlist['name']
        tracks = get_playlist_tracks(playlist['id'])
        playlist_outliers = process_playlist(playlist_name, tracks)
        if playlist_outliers:
            outliers[playlist_name] = playlist_outliers

    return outliers

def process_playlist(playlist_name, tracks):
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
        outliers[feature] = [(track['track']['name'], track_feature, track['track']['uri']) for track, track_feature in zip(tracks, values)
                             if abs(track_feature - avg_feature) > 3 * stdev_feature]

    averages = {feature: statistics.mean(
        values) for feature, values in feature_values.items()}
    stddevs = {feature: statistics.stdev(
        values) for feature, values in feature_values.items()}

    filename = "playlist_statistics/" + \
        (re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', playlist_name)
         ).strip() + ' - audio_features.txt'
    with open(filename, 'w') as f:
        f.write(f'Playlist: {playlist_name}\n')
        f.write(f'no. tracks: {len(tracks)}\n\n')
        for feature in feature_values.keys():
            f.write(
                f'Average {feature}: {averages[feature]:.2f} | stdev: {stddevs[feature]:.2f}\n')
        f.write('\n')

        outliers_uris = []
        for feature, tracks in outliers.items():
            if tracks:
                f.write(f'{feature.capitalize()} outliers:\n')
                for track in tracks:
                    f.write(f'\t{track[0]} ({track[1]:.2f})\n')
                    outliers_uris.append(track[2])
                f.write('\n')
        print('Significant outliers printed to file.')

    return outliers_uris


def remove_outliers(playlists, outliers):
    # Remove outliers from the newly created playlists

    total_outliers = sum(len(outliers)
                         for outliers in outliers.values())

    if total_outliers == 0:
        print("No outliers found.")
        return

    print(f"Total outliers found: {total_outliers}")

    # Prompt the user to confirm outlier removal
    confirm = input("Do you want to remove the outliers? (y/n): ")
    if confirm.lower() != 'y':
        print("Outlier removal canceled.")
        return

    for playlist in playlists:
        playlist_name = playlist['name']
        tracks = get_playlist_tracks(playlist['id'])
        playlist_outliers = outliers.get(playlist_name)  # Get outliers for the current playlist
        if playlist_outliers:  # Check if there are any outliers for the playlist
            print(f"Removing outliers from playlist: {playlist_name}")
            cleaned_tracks = []
            for track in tracks:
                if track['track']['uri'] not in playlist_outliers:
                    cleaned_tracks.append(track)
                else:
                    print(f"Outlier track: {track['track']['name']}")
            # Update the playlist with the cleaned tracks
            update_playlist(playlist['id'], cleaned_tracks)

    print("Outliers removed successfully.")


def update_playlist(playlist_id, tracks):
    # Update the specified playlist with the cleaned tracks
    # Get existing tracks from the playlist
    existing_tracks = get_playlist_tracks(playlist_id)
    existing_track_uris = [track['track']['uri'] for track in existing_tracks]
    # Remove existing tracks from the playlist in batches
    for i in range(0, len(existing_track_uris), 100):
        batch_tracks = existing_track_uris[i:i+100]
        sp.playlist_remove_all_occurrences_of_items(playlist_id, batch_tracks)

    # Add the cleaned tracks to the playlist
    track_uris = [track['track']['uri'] for track in tracks]

    # Add tracks in batches of 100
    for i in range(0, len(track_uris), 100):
        batch_tracks = track_uris[i:i+100]
        sp.playlist_add_items(playlist_id, batch_tracks)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "link", help="Link to the playlist or path to the text file")
    parser.add_argument("--analyse", action="store_true",
                        help="Perform analysis only without duplication")
    args = parser.parse_args()

    # Read the playlist from the provided link
    playlists = read_playlist(args.link)

    # Check if analysis mode is enabled
    if args.analyse:
        # Analyze the tracks in the playlists
        outliers = analyse_tracks(playlists)

    else:
        duplicated_playlists = []

        # Check if the link is a txt file
        if isinstance(args.link, str) and args.link.endswith('.txt'):

            # Duplicate each playlist and perform analysis
            for playlist in playlists:
                duplicated_playlist = duplicate_playlist(playlist)
                duplicated_playlists.append(duplicated_playlist)

        # Analyze the tracks in the duplicated playlists
        outliers = analyse_tracks(duplicated_playlists)
        # Prompt user to remove outliers
        remove_outliers(duplicated_playlists, outliers)  # Pass 'playlists' instead of 'duplicated_playlists'


if __name__ == '__main__':
    main()
