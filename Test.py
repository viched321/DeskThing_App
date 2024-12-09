import spotipy
import customtkinter as ctk
from PIL import Image, ImageEnhance
from io import BytesIO
import requests
from spotipy.oauth2 import SpotifyOAuth
import config
import numpy as np
from pathlib import Path
import json

class SpotifyController:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config.CLIENT_ID,
                                               client_secret=config.CLIENT_SECRET,
                                               redirect_uri=config.REDIRECT_URI,
                                               scope=config.SCOPE))

    def get_current_playback(self):
        return self.sp.current_playback()
        
    def next_track(self):
        self.sp.next_track()

    def previous_track(self):
        self.sp.previous_track()

    def pause_or_play(self):
        playback = self.get_current_playback()
        if playback and playback.get("is_playing"):
            self.sp.pause_playback()
        else:
            self.sp.start_playback()

    def add_song_to_playlist(self):
        current_playback = self.get_current_playback()
        if not current_playback or not current_playback["item"]:
            print("No song is currently playing.")
            return
        
        track_id = current_playback["item"]["id"]
        if self.playlist_id:
            playlist_tracks = self.sp.playlist_tracks(self.playlist_id)
            track_ids_in_playlist = [track["track"]["id"] for track in playlist_tracks["items"]]
            if track_id not in track_ids_in_playlist:
                self.sp.playlist_add_items(self.playlist_id, [track_id])
                print(f"Song added to playlist: {track_id}")
            else:
                print(f"Song with ID {track_id} is already in the playlist.")

    def slider_changed(self, position_ms):
        self.sp.seek_track(int(position_ms))

class AppSettings:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.settings = self.load_settings()

    def load_settings(self):
        with open(self.settings_file,"r") as file:
            return json.load(file)
    
    def save_settings(self):
        with open(self.settings_file,"w") as file:
            json.dump(self.settings, file)
class SpotifyAppGUI:
    def __init__(self,spotify_controller,app_settings):
        self.sp = spotify_controller
        self.settings = app_settings
        self.base_folder = Path(r"ButtonImages")
        self.window = ctk.CTk()
        self.setup_ui()
        self.current_song_info = {"album_art": None, "song_name": "", "artists": ""}

    def setup_ui(self):
        self.window.title("DeskThing is on")
        self.window.geometry("800x480")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        #Cover art label setup
        self.background_cover_art_size: tuple = (900,900)
        self.background_cover_art_label = ctk.CTkLabel(self.window, text="", fg_color="transparent", corner_radius=0, width=self.background_cover_art_size[0], height=self.background_cover_art_size[1])
        self.background_cover_art_label.place(x=-100, y=-100)
        
        self.cover_art_size: tuple = (250,250)
        self.cover_art_label = ctk.CTkLabel(self.window, text="", fg_color="transparent", corner_radius=0, width=self.cover_art_size[0], height=self.cover_art_size[1])
        self.cover_art_label.place(x=20, y=20)
        #Text label setup
        self.song_label = ctk.CTkLabel(self.window, text="", font=("Arial", 30, "bold"), text_color="white", anchor="w",bg_color="transparent")
        self.song_label.place(x=320, y=60)

        self.artist_label = ctk.CTkLabel(self.window, text="", font=("Arial", 20), text_color="white", anchor="w",bg_color="transparent")
        self.artist_label.place(x=320, y=120)

        self.song_time_played = ctk.CTkLabel(self.window, text="",font=("Arial",10,"bold"),text_color="white",anchor="w",bg_color="transparent")
        self.song_time_played.place(x=307, y=220)

        self.song_time_total = ctk.CTkLabel(self.window, text="",font=("Arial",10,"bold"),text_color="white",anchor="w",bg_color="transparent")
        self.song_time_total.place(x=700, y=220)

        #Button setup
        self.button_size = ((50,50))
        self.previous_song_button =ctk.CTkButton(self.window,text="",image="",width=self.button_size[0],height=self.button_size[1],command=self.sp.previous_track, fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
        self.previous_song_button.place(x=250, y=370)

        self.pause_song_touch = ctk.CTkButton(self.window,text="",image="",width=self.button_size[0],height=self.button_size[1],command=self.sp.pause_or_play,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
        self.pause_song_touch.place(x=350,y=370)

        self.next_song_touch = ctk.CTkButton(self.window,text="",image="",width=self.button_size[0],height=self.button_size[1],command=self.sp.next_track,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
        self.next_song_touch.place(x=450, y=370)

        #Progress Slider setup
        self. progress_bar_slider = ctk.CTkSlider(self.window, progress_color="white",
                                    button_corner_radius=20,button_length=0,
                                    button_color="white",button_hover_color="gray", 
                                    bg_color="transparent",height = 11, 
                                    width=360,border_width=0,
                                    from_=0, to=1000, number_of_steps=1000, 
                                    corner_radius=10,command=self.sp.slider_changed)
        self.progress_bar_slider.place(x=333, y=229)


    def update_display(self):
        try:
            current_playback = self.sp.get_current_playback()
            if current_playback:

                song_name = current_playback["item"]["name"]
                artists = ", ".join(artist["name"] for artist in current_playback["item"]["artists"])

                if song_name != self.current_song_info["song_name"]:
                    album_art_url = current_playback["item"]["album"]["images"][0]["url"]
                    response = requests.get(album_art_url)
                    album_art = Image.open(BytesIO(response.content)).resize((self.cover_art_size))
                    album_image = ctk.CTkImage(album_art, size=self.cover_art_size)
                    self.current_song_info.update({"album_art": album_image, "song_name": song_name, "artists": artists})
                    duration_ms = current_playback["item"]['duration_ms']
                    self.progress_bar_slider.configure(to=duration_ms)
                    self.song_time_total.configure(text=f"{duration_ms//60000}:{int((duration_ms%60000)/1000):02}")
                    enhancer = ImageEnhance.Brightness(background_album_art)
                    background_album_art_darker = enhancer.enhance(0.5)
                    background_album_image = ctk.CTkImage(background_album_art_darker, size=self.background_cover_art_size)
                
                progress_ms = current_playback['progress_ms']
                self.song_time_played.configure(text=f"{progress_ms//60000}:{int((progress_ms%60000)/1000):02}")
                self.progress_bar_slider.set(progress_ms)
                self.song_label.configure(text=song_name)
                self.artist_label.configure(text=artists)
                self.cover_art_label.configure(image=self.current_song_info["album_art"])
            else:
                self.song_label.configure(text="No song playing.")
                self.artist_label.configure(text="")
        except Exception as e:
            print(f"Error updating display: {e}")

        self.window.after(1000, self.update_display)

    def run(self):
        self.update_display()
        self.window.mainloop()

if __name__ == "__main__":
    spotify_controller = SpotifyController()
    app_settings = AppSettings()
    app = SpotifyAppGUI(spotify_controller, app_settings)
    app.run()

    