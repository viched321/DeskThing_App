#!/usr/bin/env pythonp
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
#Fix inte klart
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
        

class Calculations:
    def __init__(self):
        self

    def rgb_to_hex(self,rgb):
        return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
    
    def adjust_brightness(self,color, factor=1):
        return tuple(max(0, min(255, int(c * factor))) for c in color)
    
    def enhance_color_channels(color, red_factor=1.2, green_factor=1.2, blue_factor=1.2):
        r, g, b = color
        r = int(max(0, min(255, r * red_factor)))  # Adjust red channel
        g = int(max(0, min(255, g * green_factor)))  # Adjust green channel
        b = int(max(0, min(255, b * blue_factor)))  # Adjust blue channel
        return (r, g, b)
    
    def get_mean_color_from_center(self, image, user_preference, brightness_factor=1, red_factor=1, green_factor=1, blue_factor=1):
    # Handle None or invalid images early
        if image is None:
            return (0, 0, 0)  # Return black color as a default
    
    # Convert image to a NumPy array
        try:
            color_array = np.array(image)
        except Exception as e:
            return (0, 0, 0)  # Default to black

    # Proceed with the logic
        if user_preference == 1:
            region_size = (100, 100)
            height, width, _ = color_array.shape
            center_x, center_y = width // 2, height // 2

            region_width, region_height = region_size
            start_x = max(0, center_x - region_width // 2)
            end_x = min(width, center_x + region_width // 2)
            start_y = max(0, center_y - region_height // 2)
            end_y = min(height, center_y + region_height // 2)

            center_region = color_array[start_y:end_y, start_x:end_x]
            mean_color = center_region.mean(axis=(0, 1))

        elif user_preference == 2:
            mean_color = color_array.mean(axis=(0, 1))
    
        mean_color = tuple(mean_color.astype(int))
        mean_color = self.adjust_brightness(mean_color, factor=brightness_factor)
        hex_mean_color = self.rgb_to_hex(mean_color)
        return hex_mean_color


class SpotifyAppGUI:
    def __init__(self,spotify_controller,app_settings):
        self.sp = spotify_controller
        self.settings = app_settings
        self.base_folder = Path(r"ButtonImages")
        self.current_song_info = {"album_art": self.load_and_resize_image(image_name="add_image.png", size=(20,20)), "song_name": "", "artists": ""}
        self.root = ctk.CTk()
        self.root.title("Spunkify")
        self.root.geometry("800x480")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.button_image_size=((50,50))
        self.addbutton_size=((20,20))
        self.button_last_image = self.load_and_resize_image("last_button_not_hover.png", self.button_image_size)
        self.button_next_image = self.load_and_resize_image("skip_button_not_hover.png", self.button_image_size)
        self.button_pause_image = self.load_and_resize_image("pause_not_hover.png", self.button_image_size)
        self.button_start_image = self.load_and_resize_image("start_not_hover.png", self.button_image_size)
        self.button_add_image = self.load_and_resize_image("add_image.png", self.addbutton_size)
        self.button_settings_icon = self.load_and_resize_image("settings_icon.png",(20,20))
        self.background_album_image = None


        self.button_settings_icon =ctk.CTkImage(light_image=self.button_settings_icon,size= (20,20))
        self.button_next_image = ctk.CTkImage(light_image=self.button_next_image, size=self.button_image_size)
        self.button_last_image = ctk.CTkImage(light_image=self.button_last_image,size=self.button_image_size)
        self.button_add_image = ctk.CTkImage(light_image=self.button_add_image, size=self.addbutton_size)
        self.button_start_image = ctk.CTkImage(light_image=self.button_start_image, size=self.button_image_size)
        self.button_pause_image = ctk.CTkImage(light_image=self.button_pause_image, size=self.button_image_size)
        #Frames setup
        self.window_player = ctk.CTkFrame(self.root,bg_color="transparent",fg_color="transparent")
        self.window_settings = ctk.CTkFrame(self.root)
        for frame in (self.window_player,self.window_settings):
            frame.place(x=0,y=0,relwidth=1,relheight=1)
        #ui setup
        self.setup_ui_window_player()
        self.setup_ui_window_settings(app_settings.settings)
        self.configure_settings_window()
        self.user_specific_setup(app_settings.settings,self.current_song_info["album_art"])
        self.show_frame(self.window_settings)
        print("User-specific setup completed.")


    def load_and_resize_image(self, image_name, size):
        image_path = self.base_folder / image_name
        return Image.open(image_path).resize(size)

    def optionmenu_callback(self,selected_option):
        print(f"Selected option: {selected_option}")

    def optionmenu_callback_background(self,selected_option):
        self.settings.settings["background"] = selected_option
        self.settings.save_settings()
        print(f"Selected option: {selected_option}")
        self.user_specific_setup(self.settings.settings,self.album_art)

    def slider_event(self,value):
        print(value)

    def setup_ui_window_settings(self,settings):
        self.settings_menu_lable = ctk.CTkLabel(self.window_settings, text="Settings menu", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.settings_menu_lable.pack(side="top",fill="x",padx=100,pady=10)
        self.change_window_Settings_window = ctk.CTkButton(self.window_settings, text="Back", corner_radius=10, width=50, height=20, font=("Arial", 16), command=lambda: self.show_frame(self.window_player))
        self.change_window_Settings_window.place(x=10,y=10)
        
        #väljer vad är valt sedan tidigare
        self.optionmenu_var_1 = ctk.StringVar(value=settings["background"])
        self.optionmenu_1 = ctk.CTkOptionMenu(self.window_settings, values=["Minimalistic", "Minimalistic with contrast","Cover art"], command=self.optionmenu_callback_background, variable=self.optionmenu_var_1)
        self.optionmenu_1.pack(side="top",fill="x",padx=100,pady=(50,10))

        self.optionmenu_var_2 = ctk.StringVar(value="option 1")
        self.optionmenu_2 = ctk.CTkOptionMenu(self.window_settings, values=["option 1", "option 2","option 3"], command=self.optionmenu_callback, variable=self.optionmenu_var_2)
        self.optionmenu_2.pack(side="top",fill="x",padx=100,pady=10)
        
        self.optionmenu_var_3 = ctk.StringVar(value="option 1")
        self.optionmenu_3 = ctk.CTkOptionMenu(self.window_settings, values=["option 1", "option 2","option 3"], command=self.optionmenu_callback, variable=self.optionmenu_var_3)
        self.optionmenu_3.pack(side="top",fill="x",padx=100,pady=10)
        
        self.settings_menu_settings_lable_1 = ctk.CTkLabel(self.window_settings, text="Slider 1", corner_radius=10, width=50, height=20, font=("Arial", 12))
        self.settings_menu_settings_lable_1.pack(side="top",fill="x",padx=100,pady=10)

        self.optionmenu_slider_var_1 = ctk.IntVar(value=1)
        self.optionmenu_slider_1 = ctk.CTkSlider(self.window_settings, from_=0, to=1, command=self.slider_event, variable=self.optionmenu_slider_var_1)
        self.optionmenu_slider_1.pack(side="top",fill="x",padx=100,pady=10)

        self.save_settings_button = ctk.CTkButton(self.window_settings, text="Save settings", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.save_settings_button.pack(side="top",fill="x",padx=320,pady=10)

    def setup_ui_window_player(self):
        #Cover art label setup
        self.background_cover_art_size: tuple = (900,900)
        self.background_cover_art_label = ctk.CTkLabel(self.window_player, text="", width=self.background_cover_art_size[0], height=self.background_cover_art_size[1])
        self.background_cover_art_label.place(x=-100, y=-100)
        
        self.cover_art_size: tuple = (250,250)
        self.cover_art_label = ctk.CTkLabel(self.window_player, text="", fg_color="transparent", corner_radius=0, width=self.cover_art_size[0], height=self.cover_art_size[1])
        self.cover_art_label.place(x=20, y=20)

        #Text label setup
        self.song_label = ctk.CTkLabel(self.window_player, text="", font=("Arial", 30, "bold"), text_color="white", anchor="w",fg_color="transparent",bg_color="transparent")
        self.song_label.place(x=320, y=60)

        self.artist_label = ctk.CTkLabel(self.window_player,width=1,height=1, text="", font=("Arial", 20), text_color="white", anchor="w",bg_color="transparent",fg_color="transparent")
        self.artist_label.place(x=320, y=120)

        self.song_time_played = ctk.CTkLabel(self.window_player, text="",font=("Arial",10,"bold"),text_color="white",anchor="w",bg_color="transparent",fg_color="transparent")
        self.song_time_played.place(x=307, y=220)

        self.song_time_total = ctk.CTkLabel(self.window_player, text="",font=("Arial",10,"bold"),text_color="white",anchor="w",bg_color="transparent",fg_color="transparent")
        self.song_time_total.place(x=700, y=220)

        #Button setup
        self.button_size = ((1,1))
        self.previous_track_button =ctk.CTkButton(self.window_player,text="",width=self.button_size[0],height=self.button_size[1],command=self.sp.previous_track, fg_color="transparent", bg_color ="transparent",hover_color="#FFFFFF")
        self.previous_track_button.place(x=250, y=370)

        self.pause_or_play_button = ctk.CTkButton(self.window_player,text="",width=self.button_size[0],height=self.button_size[1],command=self.sp.pause_or_play,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
        self.pause_or_play_button.place(x=350,y=370)

        self.next_track_button = ctk.CTkButton(self.window_player,text="",width=self.button_size[0],height=self.button_size[1],command=self.sp.next_track,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
        self.next_track_button.place(x=450, y=370)

        self.settings_wheel_button =ctk.CTkButton(self.window_player,text="",width=20,height=20,command=lambda: self.show_frame(self.window_settings), fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
        self.settings_wheel_button.place(x=770, y=1)

        #Progress Slider setup
        self. progress_bar_slider = ctk.CTkSlider(self.window_player, progress_color="white",
                                    button_corner_radius=20,button_length=0,
                                    button_color="white",button_hover_color="gray", 
                                    bg_color="transparent",height = 11, 
                                    width=360,border_width=0,
                                    from_=0, to=1000, number_of_steps=1000, 
                                    corner_radius=10,command=self.sp.slider_changed)
        self.progress_bar_slider.place(x=333, y=229)

        #Button Images setup

        self.settings_wheel_button.configure(image=self.button_settings_icon)

    def user_specific_setup(self, app_settings, image):
        getting_mean_color = Calculations()
        blank = ctk.CTkImage(Image.new('RGBA', (100, 100), (255, 0, 0, 0)))

        if app_settings["background"] == "Minimalistic with contrast":
            mean_color = getting_mean_color.get_mean_color_from_center(image, 1)
            print(mean_color)
            self.background_cover_art_label.configure(image=blank)
            self.window_player.configure(fg_color=mean_color)

        elif app_settings["background"] == "Minimalistic":
            mean_color = getting_mean_color.get_mean_color_from_center(image, 2)
            self.background_cover_art_label.configure(image=blank)
            self.window_player.configure(fg_color=mean_color)

        elif app_settings["background"] == "Cover art":
            self.background_cover_art_label.configure(image=self.background_album_image)
            self.window_player.configure(fg_color="gray")
    

    def show_frame(self, frame: ctk.CTkFrame):
        frame.tkraise()
    
    def configure_settings_window(self):
        print("this is where we configure settings window")
        self.settings_menu_lable.configure()
        self.optionmenu_1.configure()
        self.optionmenu_2.configure()
        self.optionmenu_3.configure()
        self.optionmenu_slider_1.configure()
        self.change_window_Settings_window.configure()

    def update_display(self):
        try:
            current_playback = self.sp.get_current_playback()

            #Always when song running
            
            if current_playback:
                artists = ", ".join(artist["name"] for artist in current_playback["item"]["artists"])
                self.previous_track_button.configure(image=self.button_last_image)
                self.next_track_button.configure(image=self.button_next_image)
                if (current_playback['is_playing']):
                    self.pause_or_play_button.configure(image=self.button_pause_image)

                else:
                    self.pause_or_play_button.configure(image=self.button_start_image)


                #Only when song changes
                try:
                    if current_playback["item"]["name"] != self.current_song_info["song_name"]:
                        album_art_url = current_playback["item"]["album"]["images"][0]["url"]
                        response = requests.get(album_art_url)
                        self.album_art = Image.open(BytesIO(response.content))
                        self.album_image = ctk.CTkImage(self.album_art, size=self.cover_art_size)
                        self.current_song_info.update({"album_art": self.album_image, "song_name": current_playback["item"]["name"], "artists": artists})
                        duration_ms = current_playback["item"]['duration_ms']
                        self.progress_bar_slider.configure(to=duration_ms)
                        self.song_time_total.configure(text=f"{duration_ms//60000}:{int((duration_ms%60000)/1000):02}")
                        background_album_art_darker = ImageEnhance.Brightness(self.album_art).enhance(0.5)
                        self.background_album_image = ctk.CTkImage(background_album_art_darker, size=self.background_cover_art_size)
                        self.user_specific_setup(app_settings.settings, self.album_art)
                except Exception as e:
                    print(f"oijdsajoioijdsajwqdiowqj updating display: {e}")

                self.song_label.configure(text=current_playback["item"]["name"])
                self.artist_label.configure(text=artists)
                self.cover_art_label.configure(image=self.current_song_info["album_art"])
                progress_ms = current_playback['progress_ms']
                self.song_time_played.configure(text=f"{progress_ms//60000}:{int((progress_ms%60000)/1000):02}")
                self.progress_bar_slider.set(progress_ms)
            else:
                self.song_label.configure(text="No song playing.")
                self.artist_label.configure(text="")
        except Exception as e:
            print(f"Error updating display: {e}")

        self.window_player.after(50, self.update_display)

    def run(self):
        print("configure display")
        self.update_display()
        self.root.mainloop()

if __name__ == "__main__":
    #ctk.deactivate_automatic_dpi_awareness()
    spotify_controller = SpotifyController()
    app_settings = AppSettings()
    app = SpotifyAppGUI(spotify_controller, app_settings)
    calculate = Calculations()
    app.run()
