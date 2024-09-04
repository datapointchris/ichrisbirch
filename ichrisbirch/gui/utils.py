from customtkinter import CTk


def set_app_geometry(app: CTk, width_percent: int, height_percent: int):
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    window_width = screen_width * width_percent / 100
    window_height = screen_height * height_percent / 100
    x = (screen_width / 2) - (window_width / 2)
    y = (screen_height / 2) - (window_height / 2)
    app.geometry('%dx%d+%d+%d' % (window_width, window_height, x, y))
