import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

import base64
from PIL import Image
from io import BytesIO
import json
import os
import requests


#text colors for the console output
purple = '\033[95m'
green = '\033[92m'
orange = '\033[93m'
red = '\033[91m'
blue = '\033[96m'
white = '\033[0m'

#gives the Spotify API permissions to modify the users library and upload a picture to the playlist
scope = "playlist-modify-public ugc-image-upload"


#user-specific info that needs to be changed
#client id and secret are retrieved after "upgrading" your Spotify account to a Developer account

#account name (cannot be changed), not your profile name(can be changed)
user = "laxer666"
client_id = "d5b124b315ab4e8fa5a5f6bc8a717ccb"
client_secret = "49a6b5632bf64855be5ba43ec667d01b"
redirect_uri = 'http://localhost'

#no idea how this works, but used to give the API permissions
os.environ['SPOTIPY_CLIENT_ID'] = client_id
os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
os.environ['SPOTIPY_REDIRECT_URI'] = redirect_uri
token = util.prompt_for_user_token(user, scope, client_id, client_secret, redirect_uri)
credentials_manager =  SpotifyClientCredentials(client_id = client_id, client_secret = client_secret,)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope), client_credentials_manager = credentials_manager)


target_artist = sp.search(q=input(f"{purple}what artist would you like to discover? {white}"), type="artist")
#print(json.dumps(target_artist, sort_keys=4, indent = 4))
target_artist_name = target_artist["artists"]["items"][0]["name"]
target_artist_id = target_artist["artists"]["items"][0]["id"]

#prints the info of a Spotify Track JSON object to the terminal
def visualize_track(track): 
    s = ", "
    track_artists = s.join(str(v['name']) for v in track['artists'])
    print(f"{green}{track_name} {orange}{track_artists} {red}{track['album']} {blue}{track['popularity']}")

#abstracted method to request tracks from record types
#record types are albums, singles, compilations/mixtapes
#because requesting album tracks do not always include the singles that an Artists releases
def compile_tracks_from(record_type : str):
    albumlist = sp.artist_albums(target_artist_id, album_type=record_type)
    tracklist = dict()
    for album in albumlist['items']:
        #if the album is by the target_artist, add all the songs on it to the tracklist
        curr_album = sp.album_tracks(album['id'])['items']
        for track in curr_album:
            if track['name'] in tracklist:
                #prevents duplicate track entries into the artist's discography
                continue
            track['album'] = album['name']
            tracklist[track['name']] = track
    return tracklist


album_tracks = compile_tracks_from('album')
single_tracks = compile_tracks_from('single')
#unions the two lists. As long as the two tracks have the same name (key in the dictionaries), duplicates will be prevented
tracklist = single_tracks | album_tracks
#go through the tracklist below
    
for track_name in tracklist:
    track = tracklist[track_name]
    track['popularity'] = str(sp.track(track['id'])['popularity'])
#    visualize_track(track)

#sort the tracklist by popularity
sorted_tracklist = {k: v for k, v in sorted(tracklist.items(), key=lambda item: int(item[1]['popularity']), reverse=True)}

#then filter the list of tracks to be within a certain range of the artist's popularity
filtered_and_sorted_tracklist = dict()
artist_popularity = sp.artist(target_artist_id)['popularity']
print(f"{artist_popularity}{white}")
for track_name, track in sorted_tracklist.items():
    visualize_track(track)
    if int(track['popularity']) > (int(artist_popularity) * .6666):
        filtered_and_sorted_tracklist[track_name] = track
        
#add the filtered list of songs to a playlist

try:
    sp.user_playlist_create(user=user, name=f"{target_artist_name} Top Hits 🎶🧭", public=True, collaborative=False, description=f"The top hits from {target_artist_name}, found by the HitFinder program")
    new_playlist_id = sp.user_playlists(user=user)['items'][0]['id']

    track_uris = [v['uri'] for k,v in filtered_and_sorted_tracklist.items()]
    sp.user_playlist_add_tracks(user=user, playlist_id=new_playlist_id, tracks=track_uris)

    target_artist_image = target_artist['artists']['items'][0]['images'][0]['url']
    target_artist_image = base64.b64encode(requests.get(target_artist_image).content)
except Exception as e:
    print(f"{white} There was an error creating the playlist")
    print(e)


#EXPERIMENTING WITH PUTTING A LOGO OVERLAY ON THE ARTIST IMAGE USING THESE LIBRARIES BELOW

#background = Image.open(target_artist_image)
#overlay = Image.open("ol.jpg")
#buffered = BytesIO()

#background = background.convert("RGBA")
#overlay = overlay.convert("RGBA")

#new_img = Image.blend(background, overlay, 0.8)
#new_img.save(buffered, format="JPEG")
#new_img_str = base64.b64encode(buffered.getvalue())
sp.playlist_upload_cover_image(new_playlist_id, target_artist_image)
