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



sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config.CLIENT_ID,
                                               client_secret=config.CLIENT_SECRET,
                                               redirect_uri=config.REDIRECT_URI,
                                               scope=config.SCOPE))
user_settings = {
    "background": 1,


}
def save_settings():
    with open("settings.json","w") as infile:
        json.dump(user_settings, infile)

latest_song_name = ""
# Replace with the actual playlist ID
playlist_id = None #'7x5hAkfr7lmHPc41jbq1FC' 
base_folder = Path(r"ButtonImages")


if (playlist_id):
    playlist = sp.playlist(playlist_id)
    playlist_image_url = playlist['images'][0]['url']  # Assuming the first image in the list is the one you want
    print("Playlist Image URL:", playlist_image_url)

 
# Funktion för att ladda och ändra storlek på en bild
def load_and_resize_image(image_name, size):
    image_path = base_folder / image_name
    return Image.open(image_path).resize(size)

latest_song_name = ""
#Background prefrence
background_prefrence= user_settings["background"]
Background_cover_brightness_scaling = 0.5
#buttons
button_size=((50,50))
button_offset=50
button_y = 370
button_x = 250

addbutton_size=((20,20))
add_button_x = 670
add_button_y = 250
# Initialize CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
# Create the main window
window = ctk.CTk()
window.title("Spotify Now Playing")
window.geometry("800x480")




background_cover_art_bevel: int = 10
background_cover_art_size: tuple = (900,900)
background_cover_art_label = ctk.CTkLabel(window, text="", fg_color="transparent", corner_radius=background_cover_art_bevel, width=background_cover_art_size[0], height=background_cover_art_size[1])
background_cover_art_label.place(x=-100, y=-100)

cover_art_bevel: int = 10
cover_art_size: tuple = (250,250)
cover_art_label = ctk.CTkLabel(window, text="", fg_color="transparent", corner_radius=cover_art_bevel, width=cover_art_size[0], height=cover_art_size[1])
cover_art_label.place(x=20, y=20)

song_label = ctk.CTkLabel(window, text="", font=("Arial", 30, "bold"), text_color="white", anchor="w",bg_color="transparent")
song_label.place(x=320, y=60)

artist_label = ctk.CTkLabel(window, text="", font=("Arial", 20), text_color="white", anchor="w")
artist_label.place(x=320, y=120)

song_time_played = ctk.CTkLabel(window, text="",font=("Arial",10,"bold"),text_color="white",anchor="w")
song_time_played.place(x=307, y=220)

save_settings_button = ctk.CTkButton(window,text="Save settings",font=("Arial",10),text_color="White",anchor="w",command=save_settings,corner_radius=25,width=button_size[0],height=button_size[1])
save_settings_button.place(x=600,y=350)

def slider_changed(value):
    sp.seek_track(int(value)) 

def next_song():
    sp.next_track()

def pause_song():
    playback = sp.current_playback()
    is_playing=playback ['is_playing']
    if is_playing:
        sp.pause_playback()
    else:
        sp.start_playback()

def add_song():
    # Get current playback info
    current_playback = sp.current_playback()
    
    if not current_playback or not current_playback['item']:
        print("No song is currently playing.")
        return
    
    track_id = current_playback['item']['id']  # Extract the track ID
    
    # Get the current playlist's tracks
    if(playlist_id):
        playlist_tracks = sp.playlist_tracks(playlist_id)  # Get tracks in the playlist
        track_ids_in_playlist = [track['track']['id'] for track in playlist_tracks['items']]  # Extract track IDs
    
    # Check if the track is already in the playlist
    if track_id in track_ids_in_playlist:
        print(f"Song with ID {track_id} is already in the playlist.")
    else:
        # Add song to playlist if not already present
        sp.playlist_add_items(playlist_id, [track_id])
        print(f"Song added to playlist: {track_id}")



def previous_song():
    sp.previous_track()

def adjust_brightness(color, factor=1):
    """Adjust the brightness of the color by multiplying each RGB component by the factor."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)

def enhance_color_channels(color, red_factor=1.2, green_factor=1.2, blue_factor=1.2):
    """Enhance the red, green, and blue channels by multiplying them with specified factors."""
    r, g, b = color
    r = int(max(0, min(255, r * red_factor)))  # Adjust red channel
    g = int(max(0, min(255, g * green_factor)))  # Adjust green channel
    b = int(max(0, min(255, b * blue_factor)))  # Adjust blue channel
    return (r, g, b)

def get_mean_color_from_center(image, region_size=(100, 100), brightness_factor=0.4, red_factor=1.5, green_factor=1.2, blue_factor=1.5):
    """Get the mean color from the center of the image and optionally darken it."""
    # Convert image to a NumPy array
    color_array = np.array(image)
    
    # Calculate the center of the image
    height, width, _ = color_array.shape
    center_x, center_y = width // 2, height // 2

    # Define the region around the center (half of the region_size in each direction)
    region_width, region_height = region_size
    start_x = max(0, center_x - region_width // 2)
    end_x = min(width, center_x + region_width // 2)
    start_y = max(0, center_y - region_height // 2)
    end_y = min(height, center_y + region_height // 2)

    # Extract the region and calculate the mean color
    center_region = color_array[start_y:end_y, start_x:end_x]
    mean_color = center_region.mean(axis=(0, 1))  # Average over height and width
    
    # Convert mean_color to a NumPy array before applying astype
    mean_color = np.array(mean_color, dtype=int)  # Ensure it's an integer numpy array
    
    # Optionally adjust the brightness of the mean color
    mean_color = adjust_brightness(mean_color, factor=brightness_factor)
    # Optionally enhance the color channels
    mean_color = enhance_color_channels(mean_color, red_factor, green_factor, blue_factor)
    
    return tuple(mean_color)  # Return as tuple after brightness adjustment




progress_bar_slider = ctk.CTkSlider(window, progress_color="white",
                                    button_corner_radius=20,button_length=0,
                                    button_color="white",button_hover_color="gray", 
                                    bg_color="transparent",height = 11, 
                                    width=360,border_width=0,
                                    from_=0, to=1000, number_of_steps=1000, 
                                    corner_radius=10,command=slider_changed)
progress_bar_slider.place(x=333, y=229)



# Ladda och ändra storlek på bilder
button_last_image = load_and_resize_image("last_button_not_hover.png", button_size)
button_next_image = load_and_resize_image("skip_button_not_hover.png", button_size)
button_pause_image = load_and_resize_image("pause_not_hover.png", button_size)
button_start_image = load_and_resize_image("start_not_hover.png", button_size)
button_add_image = load_and_resize_image("add_image.png", addbutton_size)



#skapar ctk bilder
button_next_image = ctk.CTkImage(light_image=button_next_image, size=button_size)
button_last_image = ctk.CTkImage(light_image=button_last_image,size=button_size)
button_add_image = ctk.CTkImage(light_image=button_add_image, size=addbutton_size)

playPauseStatus_img = ctk.CTkImage(light_image=button_pause_image, size=button_size)
#buttons for next button pause/start and prev button
next_song_touch = ctk.CTkButton(window,text="",image="",width=button_size[0],height=button_size[1],command=next_song,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
next_song_touch.place(x=button_x+2*button_size[0]+2*button_offset, y=button_y)

last_song_touch =ctk.CTkButton(window,text="",image="",width=button_size[0],height=button_size[1],command=previous_song,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
last_song_touch.place(x=button_x, y=button_y)

pause_song_touch = ctk.CTkButton(window,text="",image="",width=button_size[0],height=button_size[1],command=pause_song,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
pause_song_touch.place(x=button_x+button_size[0]+button_offset,y=button_y)

#button for add song to playist
if(playlist_id):
    add_song_touch = ctk.CTkButton(window,text="",image="",width=addbutton_size[0],height=addbutton_size[1],command=add_song,fg_color="transparent",bg_color="transparent",hover_color="#FFFFFF")
    add_song_touch.place(x=add_button_x,y=add_button_y)

#lable for timer
song_time_total = ctk.CTkLabel(window, text="",font=("Arial",10,"bold"),text_color="white",anchor="w")
song_time_total.place(x=700, y=220)

# Store current song info
current_song_info = {"album_art": None, "song_name": "", "artists": "", "paused": False}

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def update_display():
    """Fetch currently playing song info and update the display."""
    global current_song_info, playPauseStatus_img, mean_color_center
    try:
        #fetch all information about artist/song
        current_playback = sp.current_playback()
        currenty_playing = current_playback['is_playing']
        Current_playing_track = current_playback['item']
        current_playing_track_song_name = Current_playing_track['name']
        current_playing_artist = ", ".join([artist['name'] for artist in Current_playing_track['artists']])
        current_playing_album_art_url = Current_playing_track['album']['images'][0]['url']
        current_playing_album_art = current_song_info["album_art"]
        response = requests.get(current_playing_album_art_url)
        img_data = BytesIO(response.content)
        

        #assign the right icon for pause/play button
        if currenty_playing:
            playPauseStatus_img.configure(light_image=button_pause_image)
        else:
            playPauseStatus_img.configure(light_image=button_start_image)

        #get the averge color form album art
        if current_playing_album_art:
            mean_color_center = get_mean_color_from_center(current_playing_album_art)
            lable_mean_color_center = rgb_to_hex(mean_color_center)
        else:
            mean_color_center = (255, 255, 255)  # Default to white
            lable_mean_color_center = rgb_to_hex(mean_color_center)

        if current_playback:

            if (background_prefrence):
                if(playlist_id):
                    add_song_touch.configure(image=button_add_image, hover_color=lable_mean_color_center, fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
                next_song_touch.configure(image=button_next_image, hover_color=lable_mean_color_center, fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
                last_song_touch.configure(image=button_last_image, hover_color=lable_mean_color_center, fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
                pause_song_touch.configure(image=playPauseStatus_img, hover_color=lable_mean_color_center, fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
            else:
                if(playlist_id):
                    add_song_touch.configure(image=button_add_image, hover_color="None")
                next_song_touch.configure(image=button_next_image, hover_color="None")
                last_song_touch.configure(image=button_last_image, hover_color="None")
                pause_song_touch.configure(image=playPauseStatus_img, hover_color="None")  
            
            # Update current song info
            progress_ms = current_playback['progress_ms']
            duration_ms = Current_playing_track['duration_ms']
            
            #If song name is != current song name change album art to new album art
            if current_song_info["song_name"] != current_playing_track_song_name:
                current_playing_album_art = Image.open(img_data).resize((400, 400))
                current_song_info["song_name"] = current_playing_track_song_name
                current_song_info["album_art"] = current_playing_album_art
                progress_bar_slider.configure(to=duration_ms)


            current_song_info.update({
                "song_name": current_playing_track_song_name,
                "artists": current_playing_artist,
                "paused": not currenty_playing,
            })

            progress = progress_ms if progress_ms and duration_ms else 0
            progress_bar_slider.set(progress)
            
        if current_song_info["album_art"]:
            # Open and resize images
            background_album_art = Image.open(img_data).resize((400, 400))
            current_playing_album_art = Image.open(img_data).resize((400, 400))

            # Darken the background image
            enhancer = ImageEnhance.Brightness(background_album_art)
            background_album_art_darker = enhancer.enhance(Background_cover_brightness_scaling)  # 90% brightness

            # Create CTkImage objects
            album_image = ctk.CTkImage(current_playing_album_art, size=cover_art_size)
            background_album_image = ctk.CTkImage(background_album_art_darker, size=background_cover_art_size)
            

            cover_art_label.configure(image=album_image)
            if background_prefrence:
                window.configure(fg_color=rgb_to_hex(mean_color_center))
            else:
                #set_album_art_as_image(window, album_art_url)
                print("else")
                background_cover_art_label.configure(image=background_album_image)

            #sheck what color the buttons should be
            if background_prefrence:
                song_label.configure(text=f"{current_song_info['song_name']}", fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
                artist_label.configure(text=f"{current_song_info['artists']}", fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
                song_time_played.configure(text=f"{progress_ms//60000}:{int((progress_ms%60000)/1000):02}", fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
                song_time_total.configure(text=f"{duration_ms//60000}:{int((duration_ms%60000)/1000):02}", fg_color=lable_mean_color_center,bg_color=lable_mean_color_center)
            else:
                song_label.configure(text=f"{current_song_info['song_name']}")
                artist_label.configure(text=f"{current_song_info['artists']}")
                song_time_played.configure(text=f"{progress_ms//60000}:{int((progress_ms%60000)/1000):02}")
                song_time_total.configure(text=f"{duration_ms//60000}:{int((duration_ms%60000)/1000):02}")

            
        else:
            song_label.configure(text="No song is currently playing.")
            artist_label.configure(text="")
            cover_art_label.configure(image="")
            song_time_played.configure(text="")
            song_time_total.configure(text="")
            next_song_touch.configure(image="")
            last_song_touch.configure(image="")
            pause_song_touch.configure(images="")
            if(playlist_id):
                add_song_touch.configure(Image="")
            pause_song_touch.configure(image="")
            progress_bar_slider.configure(width=0)
            

    except Exception as e:
        song_label.configure(text="Error fetching song info.")
        print(f"Error: {e}")

    window.after(100, update_display)



# Start the display update loop
update_display()

# Run the CustomTkinter event loop
window.mainloop()

