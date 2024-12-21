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
import datetime
import threading
import time

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

        # Apply color scaling
        mean_color = [
            mean_color[0] * red_factor,
            mean_color[1] * green_factor,
            mean_color[2] * blue_factor
        ]

        # Ensure integer values and adjust brightness
        mean_color = tuple(np.clip(mean_color, 0, 255).astype(int))
        mean_color = self.adjust_brightness(mean_color, factor=brightness_factor)

        # Convert to hex and return
        hex_mean_color = self.rgb_to_hex(mean_color)
        return hex_mean_color


class SpotifyAppGUI:
    def __init__(self,spotify_controller,app_settings):
        self.current_time = datetime.datetime.now()
        response = requests.get("https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
        data = response.json()
        image_url = "https://www.bing.com" + data["images"][0]["url"]
        image_response = requests.get(image_url)
        self.image_data = Image.open(BytesIO(image_response.content))
        self.image_data = self.image_data.resize((800, 480))
        self.home_image = ctk.CTkImage(self.image_data, size=(800,480))
        self.sp = spotify_controller
        self.settings = app_settings
        self.base_folder = Path(r"ButtonImages")
        self.current_song_info = {"album_art": self.load_and_resize_image(image_name="add_image.png", size=(20,20)), "song_name": "", "artists": ""}
        self.album_art = self.current_song_info["album_art"]
        #cutomTKinter
        self.values = ["window_setting1", "window_setting2", "window_setting3", "window_setting4"]
        self.current_frame = None
        self.went_home = False
        self.root = ctk.CTk()
        self.root.title("DeskThing_App")
        self.root.geometry("800x480")
        self.root.attributes("-fullscreen", True)
        # Bind the Escape key to exit full-screen mode
        self.root.bind("<Escape>", self.exit_fullscreen)

        #all button locations and lable locations
        self.timer_bar_locationX= 10
        self.timer_bar_locationY= 10

        self.button_image_size=((50,50))
        self.button_size=((50,50))
        self.addbutton_size=((20,20))

        # Background cover art size and position
        self.background_cover_art_size: tuple = (900, 900)
        self.background_cover_art_x = -100
        self.background_cover_art_y = -250

        # Cover art size and position
        self.cover_art_size: tuple = (250, 250)
        self.cover_art_x = 20
        self.cover_art_y = 20

        # Song label position and size
        self.song_label_x = 320
        self.song_label_y = 60
        self.song_label_width = 480
        self.song_label_height = 60

        # Artist label position and size
        self.artist_label_x = 320
        self.artist_label_y = 120
        self.artist_label_width = 480
        self.artist_label_height = 50

        # Song timer positions
        self.song_time_total_x_offset = 400
        self.song_time_played_x = self.timer_bar_locationX
        self.song_time_played_y = self.timer_bar_locationY
        self.song_time_total_x = self.timer_bar_locationX + self.song_time_total_x_offset
        self.song_time_total_y = self.timer_bar_locationY

        # Clock and date positions
        self.clock_x = 762
        self.clock_y = 440
        self.date_x = 762
        self.date_y = 460

        # Button positions
        self.previous_track_button_x = 250
        self.previous_track_button_y = 370
        self.pause_or_play_button_x = 350
        self.pause_or_play_button_y = 370
        self.next_track_button_x = 450
        self.next_track_button_y = 370
        self.settings_wheel_button_x = 770
        self.settings_wheel_button_y = 1
        self.home_house_button_x = 740
        self.home_house_button_y = 1

        # Progress bar slider position
        self.progress_bar_slider_x = self.timer_bar_locationX + 30
        self.progress_bar_slider_y = self.timer_bar_locationY + 10

        # Offset values
        self.offset_x = 100
        self.offset_y = 250



        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.button_last_image = self.load_and_resize_image("last_button_not_hover.png", self.button_image_size)
        self.button_next_image = self.load_and_resize_image("skip_button_not_hover.png", self.button_image_size)
        self.button_pause_image = self.load_and_resize_image("pause_not_hover.png", self.button_image_size)
        self.button_start_image = self.load_and_resize_image("start_not_hover.png", self.button_image_size)
        self.button_add_image = self.load_and_resize_image("add_image.png", self.addbutton_size)
        self.button_settings_icon = self.load_and_resize_image("settings_icon.png",(20,20))
        self.button_home_icon = self.load_and_resize_image("home_icon.png",(20,20))
        self.background_album_image = None
        self.background_album_image_artist_crop = None  # Initialize the attribute
        self.background_album_image_song_crop = None


        self.button_home_icon = ctk.CTkImage(light_image=self.button_home_icon,size= (20,20))
        self.button_settings_icon =ctk.CTkImage(light_image=self.button_settings_icon,size= (20,20))
        self.button_next_image = ctk.CTkImage(light_image=self.button_next_image, size=self.button_image_size)
        self.button_last_image = ctk.CTkImage(light_image=self.button_last_image,size=self.button_image_size)
        self.button_add_image = ctk.CTkImage(light_image=self.button_add_image, size=self.addbutton_size)
        self.button_start_image = ctk.CTkImage(light_image=self.button_start_image, size=self.button_image_size)
        self.button_pause_image = ctk.CTkImage(light_image=self.button_pause_image, size=self.button_image_size)
        
        #Frames setup
        self.window_player = ctk.CTkFrame(self.root,bg_color="transparent",fg_color="transparent")
        self.window_settings = ctk.CTkFrame(self.root)
        self.window_home = ctk.CTkFrame(self.root)
        for frame in (self.window_player,self.window_settings,self.window_home):
            frame.place(x=0,y=0,relwidth=1,relheight=1)
        #ui setup
        self.setup_ui_window_player()
        self.setup_ui_window_settings(app_settings.settings)
        self.setup_ui_window_home()
        self.user_specific_setup(app_settings.settings,self.current_song_info["album_art"])
        self.show_frame(self.window_home)
        print("User-specific setup completed.")

        #threading
        self.current_playback = None
        self.should_run = True
        # Start background thread
        self.playback_thread = threading.Thread(target=self.update_playback, daemon=True)
        self.playback_thread.start()

    def exit_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)

    def update_playback(self):
        while self.should_run:
            try:
                self.current_playback = self.sp.sp.current_playback()
                time.sleep(0.5)  # Avoid too frequent API calls
            except Exception as e:
                print(f"Error updating playback: {e}")
                time.sleep(0.5)
        

    def crop_background_album_image(self):
        # the size is 900x900 px, position is now, position is -100, -100
        # first two labels are placed with height=60, and second is height 50 both with width=480
        # label named song_label is placed x=320 and y = 60
        # label named artist_label is placed x=320 and y = 120

        
        pil_image = self.background_album_art_darker.resize(self.background_cover_art_size)

        song_label_left = self.song_label_x + self.offset_x
        song_label_right = self.song_label_x + self.offset_x + self.song_label_width
        song_label_top = self.song_label_y + self.offset_y
        song_label_bottom = self.song_label_y + self.song_label_height + self.offset_y

        artist_label_left = self.artist_label_x + self.offset_x
        artist_label_right = self.artist_label_x + self.offset_x + self.artist_label_width
        artist_label_top = self.artist_label_y + self.offset_y
        artist_label_bottom = self.artist_label_y + self.artist_label_height + self.offset_y    

        # Ensure self.background_album_image is a PIL image
        pil_image = pil_image  # Assuming self.background_album_image is a PIL image

        # Crop the image
        artist_crop = pil_image.crop((artist_label_left, artist_label_top, artist_label_right, artist_label_bottom))
        song_crop = pil_image.crop((song_label_left, song_label_top, song_label_right, song_label_bottom))

        # Convert cropped images back to CTkImage
        self.background_album_image_artist_crop = ctk.CTkImage(light_image=artist_crop, size=artist_crop.size)
        self.background_album_image_song_crop = ctk.CTkImage(light_image=song_crop, size=song_crop.size)


        




    def load_and_resize_image(self, image_name, size):
        image_path = self.base_folder / image_name
        return Image.open(image_path).resize(size)

    def optionmenu_callback_background(self,selected_option):
        self.settings.settings["background"] = selected_option
        self.user_specific_setup(self.settings.settings,self.album_art)
        
    def optionmenu_callback_date_and_time(self, selected_option):
        self.settings.settings["datetime"]=selected_option
        self.user_specific_setup(self.settings.settings,self.album_art)
        
    def optionmenu_callback_progress_bar(self,selected_option):
        self.settings.settings["progressbar"]=selected_option
        self.user_specific_setup(self.settings.settings,self.album_art)
    
    def optionmenu_callback_homescreen(self,selected_option):
        self.settings.settings["homescreen"]=selected_option
    
    def slider_Brightness(self, selected_option):
        self.settings.settings["brightness_factor"] = selected_option
        self.user_specific_setup(app_settings.settings, self.album_art)
    
    def slider_red(self, selected_option):
        self.settings.settings["red_factor"] = selected_option
        self.user_specific_setup(app_settings.settings, self.album_art)

    def slider_green(self, selected_option):
        self.settings.settings["green_factor"] = selected_option
        self.user_specific_setup(app_settings.settings, self.album_art)
    
    def slider_blue(self, selected_option):
        self.settings.settings["blue_factor"] = selected_option
        self.user_specific_setup(app_settings.settings, self.album_art)
        
    def save_the_settings(self):
        self.settings.save_settings()
               
    def setup_ui_window_home(self):
        self.home_window_image = ctk.CTkLabel(self.window_home,image=self.home_image,text=f"{self.current_time.hour:02}:{self.current_time.minute:02}\n{self.current_time.month:02}/{self.current_time.day:02}-{self.current_time.year}",font=("Arial",60),text_color="white")
        self.home_window_image.place(x=0,y=0)
        
        self.player_button = ctk.CTkButton(self.window_home,text="back",command=lambda: self.show_frame(self.window_player),width=20,height=20)
        self.player_button.place(x=760,y=1)

    def optionmenu_callback_button_preference(self,selected_option):
        self.settings.settings["ButtonPreference"] = selected_option
        self.user_specific_setup(self.settings.settings,self.album_art)
    
    def going_homescreen(self):
        if self.current_playback == None:
            self.went_home = False
            
        elif (self.current_playback['is_playing']) == True:
            self.went_home = True
        else: 
            self.went_home = False
        self.show_frame(self.window_home)
        return self.went_home
    
    #save location avv progress bar
    def save_xy(self):
        y_input = int(self.progressbar_y_entry.get())
        x_input = int(self.progressbar_x_entry.get())
        if(x_input > 0):
            self.settings.settings["ProgressbarX"] = x_input
        if(y_input > 0):
            self.settings.settings["ProgressbarY"] = y_input
        self.user_specific_setup(self.settings.settings,self.album_art)

    
    def reset_xy(self):
        self.settings.settings["ProgressbarX"] = 320
        self.settings.settings["ProgressbarY"] = 200
        self.progressbar_x_entry.delete(0,'end')
        self.progressbar_y_entry.delete(0,'end')
        self.user_specific_setup(self.settings.settings,self.album_art)


    def setup_ui_window_settings(self,settings):
        self.settings_menu_lable = ctk.CTkLabel(self.window_settings, text="Settings menu", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.settings_menu_lable.pack(side="top",fill="x",padx=100,pady=10)
        
        self.change_window_Settings_window = ctk.CTkButton(self.window_settings, text="Back", corner_radius=10, width=50, height=20, font=("Arial", 16), command=lambda: self.show_frame(self.window_player))
        self.change_window_Settings_window.place(x=10,y=10)

        #scroll
        self.scrollable_frame = ctk.CTkScrollableFrame(self.window_settings, width=500, height=330)
        self.scrollable_frame.pack(side="top",fill="x",padx=40,pady=(10,10))

        #settings        
        self.optionmenu_var_background = ctk.StringVar(value=settings["background"])
        self.optionmenu_background = ctk.CTkOptionMenu(self.scrollable_frame, values=["Minimalistic", "Minimalistic with contrast","Cover art"], command=self.optionmenu_callback_background, variable=self.optionmenu_var_background, height=50, font=("Arial", 16), dropdown_font=("Arial", 16))
        self.optionmenu_background.pack(side="top",fill="x",padx=100,pady=(50,10))

        #lable
        self.settings_menu_settings_lable_1 = ctk.CTkLabel(self.scrollable_frame, text="(only works with Minimalistic)", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.settings_menu_settings_lable_1.pack(side="top",fill="x",padx=100,pady=10)

        #lable
        self.settings_menu_settings_lable_1 = ctk.CTkLabel(self.scrollable_frame, text="Brightness", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.settings_menu_settings_lable_1.pack(side="top",fill="x",padx=100,pady=10)

        #brightness controll
        self.optionmenu_slider_var_brightness = ctk.IntVar(value=settings["brightness_factor"])
        self.optionmenu_slider_brightness = ctk.CTkSlider(self.scrollable_frame, from_=0, to=2, command=self.slider_Brightness, variable=self.optionmenu_slider_var_brightness)
        self.optionmenu_slider_brightness.pack(side="top",fill="x",padx=100,pady=10)

        #lable red color multiplier
        self.settings_menu_settings_lable_colors = ctk.CTkLabel(self.scrollable_frame, text="Red color multiplier", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.settings_menu_settings_lable_colors.pack(side="top",fill="x",padx=100,pady=10)

        #red sccroll
        self.optionmenu_slider_var_red = ctk.IntVar(value=settings["red_factor"])
        self.optionmenu_slider_red = ctk.CTkSlider(self.scrollable_frame, from_=0, to=2, command=self.slider_red, variable=self.optionmenu_slider_var_red)
        self.optionmenu_slider_red.pack(side="top",fill="x",padx=100,pady=10)

        #lable green color multiplier
        self.settings_menu_settings_lable_green = ctk.CTkLabel(self.scrollable_frame, text="Green color multiplier", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.settings_menu_settings_lable_green.pack(side="top",fill="x",padx=100,pady=10)

        #green scroll
        self.optionmenu_slider_var_green = ctk.IntVar(value=settings["green_factor"])
        self.optionmenu_slider_green = ctk.CTkSlider(self.scrollable_frame, from_=0, to=2, command=self.slider_green, variable=self.optionmenu_slider_var_green)
        self.optionmenu_slider_green.pack(side="top",fill="x",padx=100,pady=10)

        #lable blue color multiplier
        self.settings_menu_settings_lable_blue = ctk.CTkLabel(self.scrollable_frame, text="Blue color multiplier", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.settings_menu_settings_lable_blue.pack(side="top",fill="x",padx=100,pady=10)

        #blue scroll
        self.optionmenu_slider_var_blue = ctk.IntVar(value=settings["blue_factor"])
        self.optionmenu_slider_blue = ctk.CTkSlider(self.scrollable_frame, from_=0, to=2, command=self.slider_blue, variable=self.optionmenu_slider_var_blue)
        self.optionmenu_slider_blue.pack(side="top",fill="x",padx=100,pady=10)     

        #date amd time options
        self.optionmenu_var_datetime = ctk.StringVar(value=settings["datetime"])
        self.optionmenu_datetime = ctk.CTkOptionMenu(self.scrollable_frame, values=["No date or time", "Time", "Date" ,"Date and time"], command=self.optionmenu_callback_date_and_time, variable=self.optionmenu_var_datetime, height=50, font=("Arial", 16), dropdown_font=("Arial", 16))
        self.optionmenu_datetime.pack(side="top",fill="x",padx=100,pady=10)
        
        #progressbar options
        self.optionmenu_var_progressbar = ctk.StringVar(value=settings["progressbar"])
        self.optionmenu_progressbar = ctk.CTkOptionMenu(self.scrollable_frame, values=["No progress bar", "Progress bar"], command=self.optionmenu_callback_progress_bar, variable=self.optionmenu_var_progressbar, height=50, font=("Arial", 16), dropdown_font=("Arial", 16))
        self.optionmenu_progressbar.pack(side="top",fill="x",padx=100,pady=10)
        
        #home preference
        self.optionmenu_var_home = ctk.StringVar(value=settings["homescreen"])
        self.optionmenu_home = ctk.CTkOptionMenu(self.scrollable_frame, values=["Go to the player", "Remain in the homescreen"], command=self.optionmenu_callback_homescreen, variable=self.optionmenu_var_home, height=50, font=("Arial", 16), dropdown_font=("Arial", 16))
        self.optionmenu_home.pack(side="top",fill="x",padx=100,pady=10)

        #button preference lable
        self.settings_menu_lable_button_preference = ctk.CTkLabel(self.scrollable_frame, text="Button preference", corner_radius=10, width=50, height=20, font=("Arial", 16))
        #button preference option
        self.optionmenu_var_button_preference = ctk.StringVar(value=settings["ButtonPreference"])
        self.optionmenu_button_preference = ctk.CTkOptionMenu(self.scrollable_frame, values=["Clean", "Default"], command=self.optionmenu_callback_button_preference, variable=self.optionmenu_var_button_preference, height=50, font=("Arial", 16), dropdown_font=("Arial", 16))
        self.optionmenu_button_preference.pack(side="top",fill="x",padx=100,pady=10)

        #frame for xy buttons
        self.xy_frame = ctk.CTkFrame(self.scrollable_frame)
        self.xy_frame.pack(fill="x", padx=10, pady=10)

        # x position progress bar
        self.progressbar_x_entry_var = ctk.IntVar(value=settings["ProgressbarX"])
        self.progressbar_x_lable = ctk.CTkLabel(self.xy_frame, text="X: {progressbar_x_entry_var}", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.progressbar_x_entry = ctk.CTkEntry(self.xy_frame)

        #x settings and progressbar
        self.progressbar_x_lable.pack(side="left")
        self.progressbar_x_entry.pack(side="left")

        #lable and setting
        self.progressbar_y_entry_var = ctk.IntVar(value=settings["ProgressbarY"])
        self.progressbar_y_lable = ctk.CTkLabel(self.xy_frame, text="Y: {progressbar_y_entry_var}", corner_radius=10, width=50, height=20, font=("Arial", 16))
        self.progressbar_y_entry = ctk.CTkEntry(self.xy_frame)
        
        #location y settings
        self.progressbar_y_lable.pack(side="left")
        self.progressbar_y_entry.pack(side="left")

        #save xy location
        self.progressbar_xy_save_button = ctk.CTkButton(self.xy_frame, text="save xy", command=self.save_xy)
        self.progressbar_xy_save_button.pack(side="left",padx=10)

        #reset xy to default
        self.progressbar_xy_reset_save_button = ctk.CTkButton(self.xy_frame, text="reset xy", command=self.reset_xy)
        self.progressbar_xy_reset_save_button.pack(side="left",padx=10)


        self.save_settings_button = ctk.CTkButton(self.window_settings, text="Save", corner_radius=10, width=50, height=20, font=("Arial", 16),command=self.save_the_settings)
        self.save_settings_button.pack(side="top",fill="x",padx=300,pady=10)

    def setup_ui_window_player(self):

        # Cover art label setup
        self.background_cover_art_label = ctk.CTkLabel(self.window_player, text="", width=self.background_cover_art_size[0], height=self.background_cover_art_size[1])
        self.background_cover_art_label.place(x=self.background_cover_art_x, y=self.background_cover_art_y)

        self.cover_art_label = ctk.CTkLabel(self.window_player, text="", fg_color="transparent", corner_radius=0, width=self.cover_art_size[0], height=self.cover_art_size[1])
        self.cover_art_label.place(x=self.cover_art_x, y=self.cover_art_y)

        # Text label setup
        self.song_label = ctk.CTkLabel(self.window_player, text="", font=("Arial", 30, "bold"), text_color="white", anchor="w", fg_color="transparent", bg_color="transparent", height=60, width=480)
        self.song_label.place(x=self.song_label_x, y=self.song_label_y)

        self.artist_label = ctk.CTkLabel(self.window_player, text="", font=("Arial", 20), text_color="white", anchor="w", bg_color="transparent", fg_color="transparent", height=50, width=480)
        self.artist_label.place(x=self.artist_label_x, y=self.artist_label_y)

        # Song timer
        self.song_time_played = ctk.CTkLabel(self.window_player, text="", font=("Arial", 10, "bold"), text_color="white", anchor="w", bg_color="transparent", fg_color="transparent")
        self.song_time_played.place(x=self.song_time_played_x, y=self.song_time_played_y)

        self.song_time_total = ctk.CTkLabel(self.window_player, text="", font=("Arial", 10, "bold"), text_color="white", anchor="w", bg_color="transparent", fg_color="transparent")
        self.song_time_total.place(x=self.song_time_total_x, y=self.song_time_total_y)

        # Clock and date
        self.clock = ctk.CTkLabel(self.window_player, text="", font=("Arial", 15, "bold"), text_color="white", bg_color="transparent")
        self.clock.place(x=self.clock_x, y=self.clock_y)

        self.date = ctk.CTkLabel(self.window_player, text="", font=("Arial", 15, "bold"), text_color="white", bg_color="transparent")
        self.date.place(x=self.date_x, y=self.date_y)

        # Button setup
        self.previous_track_button = ctk.CTkButton(self.window_player, text="", width=self.button_size[0], height=self.button_size[1], command=self.sp.previous_track, fg_color="transparent", bg_color="transparent", hover_color="#FFFFFF")
        self.previous_track_button.place(x=self.previous_track_button_x, y=self.previous_track_button_y)

        self.pause_or_play_button = ctk.CTkButton(self.window_player, text="", width=self.button_size[0], height=self.button_size[1], command=self.sp.pause_or_play, fg_color="transparent", bg_color="transparent", hover_color="#FFFFFF")
        self.pause_or_play_button.place(x=self.pause_or_play_button_x, y=self.pause_or_play_button_y)

        self.next_track_button = ctk.CTkButton(self.window_player, text="", width=self.button_size[0], height=self.button_size[1], command=self.sp.next_track, fg_color="transparent", bg_color="transparent", hover_color="#FFFFFF")
        self.next_track_button.place(x=self.next_track_button_x, y=self.next_track_button_y)

        self.settings_wheel_button = ctk.CTkButton(self.window_player, text="", image=self.button_settings_icon, width=20, height=20, command=lambda: self.show_frame(self.window_settings), fg_color="transparent", bg_color="transparent", hover_color="#FFFFFF")
        self.settings_wheel_button.place(x=self.settings_wheel_button_x, y=self.settings_wheel_button_y)

        self.home_house_button = ctk.CTkButton(self.window_player, text="", image=self.button_home_icon, width=20, height=20, command=self.going_homescreen, fg_color="transparent", bg_color="transparent", hover_color="#FFFFFF")
        self.home_house_button.place(x=self.home_house_button_x, y=self.home_house_button_y)

        # Progress Slider setup
        self.progress_bar_slider = ctk.CTkSlider(self.window_player, progress_color="white",
                                    button_corner_radius=20, button_length=0,
                                    button_color="white", button_hover_color="gray", 
                                    bg_color="transparent", height=11, 
                                    width=360, border_width=0,
                                    from_=0, to=1000, number_of_steps=1000, 
                                    corner_radius=10, command=self.sp.slider_changed)
        self.progress_bar_slider.place(x=self.progress_bar_slider_x, y=self.progress_bar_slider_y)

    def user_specific_setup(self, app_settings, image):
        getting_mean_color = Calculations()
        blank = ctk.CTkImage(Image.new('RGBA', (100, 100), (255, 0, 0, 0)))
        self.progressbar_x_lable.configure(text=f'X: {app_settings["ProgressbarX"]}')
        self.progressbar_y_lable.configure(text=f'Y: {app_settings["ProgressbarY"]}')

        if app_settings["background"] == "Minimalistic with contrast":
            mean_color = getting_mean_color.get_mean_color_from_center(image, 1, app_settings["brightness_factor"],app_settings["red_factor"], app_settings["green_factor"], app_settings["blue_factor"])
            self.background_cover_art_label.configure(image=blank)
            self.artist_label.configure(image="")
            self.song_label.configure(image="")
            self.window_player.configure(fg_color=mean_color)

        elif app_settings["background"] == "Minimalistic":
            mean_color = getting_mean_color.get_mean_color_from_center(image, 2, app_settings["brightness_factor"],app_settings["red_factor"], app_settings["green_factor"], app_settings["blue_factor"])
            self.background_cover_art_label.configure(image=blank)
            self.artist_label.configure(image="")
            self.song_label.configure(image="")
            self.window_player.configure(fg_color=mean_color)

        elif app_settings["background"] == "Cover art":
            self.background_cover_art_label.configure(image=self.background_album_image)
            self.window_player.configure(fg_color="gray")
            self.artist_label.configure(image=self.background_album_image_artist_crop)
            self.song_label.configure(image=self.background_album_image_song_crop)

            
        if app_settings["datetime"] == "No time or date":
            self.date.place(x=1000,y=460)
            self.clock.place(x=1000,y=440)
            
        elif app_settings["datetime"] == "Date":
            self.date.configure(text=f"{self.current_time.month:02}/{self.current_time.day:02}  ")
            self.date.place(x=762,y=460)
            self.clock.place(x=1000,y=440)
            
        elif app_settings["datetime"] == "Time":
            self.clock.configure(text=f"{self.current_time.hour:02}:{self.current_time.minute:02}  ")
            self.clock.place(x=762,y=440)
            self.date.place(x=1000,y=460)
            
        elif app_settings["datetime"] == "Date and time":
            self.date.configure(text=f"{self.current_time.month:02}/{self.current_time.day:02}  ")
            self.date.place(x=762,y=460)
            self.clock.configure(text=f"{self.current_time.hour:02}:{self.current_time.minute:02}  ")
            self.clock.place(x=762,y=440)

        if app_settings["ButtonPreference"] == "Clean":
            self.previous_track_button.place_forget()  # If the button was placed with place()
            self.next_track_button.place_forget()
            self.pause_or_play_button.place_forget()
        else:
            self.previous_track_button.place(x=250, y=370)  # If the button was placed with place()
            self.next_track_button.place(x=450, y=370)
            self.pause_or_play_button.place(x=350,y=370)

        #configure new xy location for progressbar
        self.song_time_played.place(x=app_settings["ProgressbarX"], y=app_settings["ProgressbarY"])
        self.song_time_total.place(x=app_settings["ProgressbarX"]+400, y=app_settings["ProgressbarY"])
        self.progress_bar_slider.place(x=app_settings["ProgressbarX"]+30, y=app_settings["ProgressbarY"]+10)

            
        #Chance to toggle progress bar on and off work in progress
        
        if app_settings["progressbar"] == "No progress bar":
            self.progress_bar_slider.place_forget()
            self.song_time_played.place_forget()
            self.song_time_total.place_forget()

            
        elif app_settings["progressbar"]=="Progress bar":
            self.progress_bar_slider.place(x=333, y=229)      
            self.song_time_played.place(x=307, y=220)
            self.song_time_total.place(x=700, y=220)

            
    

    def show_frame(self, frame:ctk.CTkFrame):
        frame.tkraise()
        self.current_frame = frame
    
    def update_display(self):

        #configure
        self.current_time = datetime.datetime.now()
        self.clock.configure(text=f"{self.current_time.hour:02}:{self.current_time.minute:02}  ")
        self.date.configure(text=f"{self.current_time.month:02}/{self.current_time.day:02}  ")


        if self.current_frame == self.window_home:
            self.home_window_image.configure(text=f"{self.current_time.hour:02}:{self.current_time.minute:02} \n{self.current_time.month:02}/{self.current_time.day:02}-{self.current_time.year}")
        try:
            if self.current_playback:
                artists = ", ".join(artist["name"] for artist in self.current_playback["item"]["artists"])
                self.previous_track_button.configure(image=self.button_last_image)
                self.next_track_button.configure(image=self.button_next_image)
                if (self.current_playback['is_playing']):
                    if (self.current_frame == self.window_home):
                        if app_settings.settings['homescreen']=='Go to the player':
                            if self.went_home == False:
                                self.show_frame(self.window_player)
                    if(app.settings.settings["ButtonPreference"]== "Default"):
                        self.pause_or_play_button.configure(image=self.button_pause_image)
                else:
                    if(app.settings.settings["ButtonPreference"]== "Default"):
                        self.pause_or_play_button.configure(image=self.button_start_image)


                #Only when song changes
                try:
                    if self.current_playback["item"]["name"] != self.current_song_info["song_name"]:
                        self.album_art_url = self.current_playback["item"]["album"]["images"][0]["url"]
                        response = requests.get(self.album_art_url)
                        self.album_art = Image.open(BytesIO(response.content))
                        self.album_image = ctk.CTkImage(self.album_art, size=self.cover_art_size)
                        self.current_song_info.update({"album_art": self.album_image, "song_name": self.current_playback["item"]["name"], "artists": artists})
                        duration_ms = self.current_playback["item"]['duration_ms']
                        self.progress_bar_slider.configure(to=duration_ms)
                        self.song_time_total.configure(text=f"{duration_ms//60000}:{int((duration_ms%60000)/1000):02}")
                        self.background_album_art_darker = ImageEnhance.Brightness(self.album_art).enhance(0.7)
                        self.background_album_image = ctk.CTkImage(self.background_album_art_darker, size=self.background_cover_art_size)
                        self.crop_background_album_image()
                        self.user_specific_setup(app_settings.settings, self.album_art)
                except Exception as e:
                    print(f"updating display: {e}")
                self.song_label.configure(text=self.current_playback["item"]["name"])
                self.artist_label.configure(text=artists)
                self.cover_art_label.configure(image=self.current_song_info["album_art"])
                progress_ms = self.current_playback['progress_ms']
                self.song_time_played.configure(text=f"{progress_ms//60000}:{int((progress_ms%60000)/1000):02}")
                self.progress_bar_slider.set(progress_ms)
            else:
                self.song_label.configure(text="No song playing.")
                self.artist_label.configure(text="")
        except Exception as e:
            print(f"Error updating display: {e}")

        self.window_player.after(100, self.update_display)

    def run(self):
        self.update_display()
        self.root.mainloop()

if __name__ == "__main__":
    #ctk.deactivate_automatic_dpi_awareness()
    spotify_controller = SpotifyController()
    app_settings = AppSettings()
    app = SpotifyAppGUI(spotify_controller, app_settings)
    calculate = Calculations()
    app.run()
