import sys
from openai import OpenAI
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import itertools
import requests
from urllib.request import urlopen 
from PIL import Image
import io
import base64


SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT_URI = "http://localhost:3000"
OPENAI_API_KEY = ''

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_response(client, songs):
  #construct OpenAI objct with API key
  #create chat compleations object whit 'question' as an input
  response = client.chat.completions.create(
    model="gpt-3.5-turbo", #sets the model of ChatGPT to desired model
    messages=[
      {"role": "system", "content": "You are a helpful assistant, musician, and author. Just respond with the prompt. No excess text."}, #message from the system to the model that it is a helpful assistant
      {"role": "user", "content": "Given the following list of songs, generate a prompt from DALL-E or another image generation AI in order to create a playlist picture for a playlist containing the following songs: " + songs}, #input message from user
    ]
  )
  return response.choices[0].message.content

def generate_image(client, prompt):
      
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )

    return response.data[0].url

def get_image(image_url):
    response = requests.get(image_url)
    
    img = Image.open(io.BytesIO(response.content))
    img = img.resize((256, 256))

    jpeg_stream = io.BytesIO()

    img.convert("RGB").save(jpeg_stream, format="JPEG")

    base64_jpeg = base64.b64encode(jpeg_stream.getvalue()).decode("utf-8")

    return base64_jpeg

username = sys.argv[1]

s = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                              client_secret=SPOTIPY_CLIENT_SECRET,
                                              redirect_uri=SPOTIPY_REDIRECT_URI))

# Retrieve user's playlists
user_playlists = s.current_user_playlists()

# Display user's playlists and prompt for selection
print("Your Playlists:")
for i, playlist in enumerate(user_playlists['items']):
    print(f"{i + 1}. {playlist['name']}")

# Prompt user to select a playlist
selected_index = int(input("Enter the number of the playlist you want to modify: ")) - 1

# Get the selected playlist ID
selected_playlist_id = user_playlists['items'][selected_index]['id']

playlist_data = s.playlist_tracks(selected_playlist_id)
tracks = playlist_data['items']
songs = ''

for track in tracks:
    data = track['track']['name'] + ' by ' + track['track']['artists'][0]['name']
    songs += data
    if tracks[-1] != track:
        songs += ', '

prompt = generate_response(client, songs)

image_url = generate_image(client, prompt)

image = get_image(image_url)
  
s = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="ugc-image-upload playlist-modify-public playlist-modify-private",
                                              client_id=SPOTIPY_CLIENT_ID,
                                              client_secret=SPOTIPY_CLIENT_SECRET,
                                              redirect_uri=SPOTIPY_REDIRECT_URI))

s.playlist_upload_cover_image(selected_playlist_id, image)
