import customtkinter as ctk

def create_settingsFrame(window, switch_frame_callback):
    frame2 = ctk.CTkFrame(window, width=800, height=480)
    label = ctk.CTkLabel(frame2, text="This is Frame for settings", font=("Arial", 24))
    label.pack(pady=20)

    switch_button = ctk.CTkButton(frame2, text="Go to Frame 1", command=switch_frame_callback)
    switch_button.pack(pady=20)

    return frame2