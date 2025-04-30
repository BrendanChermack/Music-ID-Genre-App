import tkinter as tk
from tkinter import messagebox
import requests, re, base64, os
from dotenv import load_dotenv
load_dotenv()

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_SECRET")
YOUTUBE_API_KEY = os.environ.get("YT_API_KEY")

def get_spotify_token():
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    r = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    r.raise_for_status()
    return r.json()['access_token']

def extract_video_id(url):
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None

def get_youtube_title(video_id):
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}'
    r = requests.get(url).json()
    try:
        return r['items'][0]['snippet']['title']
    except (IndexError, KeyError):
        return None

def clean_title_for_spotify(title):
    title = re.sub(r'[\(\[].*?[\)\]]', '', title)
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    return title.strip()

def get_spotify_genres(track_query, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    cleaned_query = clean_title_for_spotify(track_query)

    params = {"q": cleaned_query, "type": "track", "limit": 1}
    r = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    results = r.json()
    print(f"Searching Spotify for: {cleaned_query}")
    print(f"Spotify response: {results}")

    try:
        artist_id = results['tracks']['items'][0]['artists'][0]['id']
    except (IndexError, KeyError):
        return []

    artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
    artist_data = requests.get(artist_url, headers=headers).json()
    return artist_data.get("genres", [])

def on_submit():
    url = entry.get().strip()
    video_id = extract_video_id(url)
    if not video_id:
        messagebox.showerror("Error", "Invalid YouTube URL.")
        return

    title = get_youtube_title(video_id)
    print(f"Video title: {title}")

    if not title:
        messagebox.showerror("Error", "Could not get video title.")
        return

    try:
        token = get_spotify_token()
        genres = get_spotify_genres(title, token)
        result = ", ".join(genres) if genres else "Genre not found"
    except Exception as e:
        result = f"Error: {str(e)}"

    result_label.config(text=f"Predicted Genre(s): {result}")

root = tk.Tk()
root.title("Genre Genie")
root.geometry("500x300")
root.resizable(False, False)

tk.Label(root, text="Paste a YouTube Music Video URL:").pack(pady=10)
entry = tk.Entry(root, width=60)
entry.pack()

tk.Button(root, text="Identify Genre", command=on_submit).pack(pady=10)
result_label = tk.Label(root, text="", font=("Arial", 12, "bold"), wraplength=400)
result_label.pack(pady=10)

root.mainloop()