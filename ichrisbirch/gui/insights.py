import logging
from dataclasses import dataclass
from tkinter import messagebox

import customtkinter as ctk
import httpx
import pendulum
from tkhtmlview import HTMLText

from ichrisbirch.config import get_settings
from ichrisbirch.gui.utils import set_app_geometry

logger = logging.getLogger('gui.insights')


def submit_form():
    if not (url := url_entry.get()):
        messagebox.showwarning('Validation Error', 'Please fill all fields correctly.')
        return

    settings = get_settings()
    insights_endpoint = f'{settings.api_url}/articles/insights/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',  # Placeholder for authorization header
    }

    try:
        start = pendulum.now()
        response = httpx.post(insights_endpoint, headers=headers, json={'url': url}, timeout=60)
        response.raise_for_status()
        elapsed = (pendulum.now() - start).in_words()
        article_insights = response.text
        display_elapsed_time(elapsed)
        display_html_response(article_insights)

    except httpx.HTTPStatusError as e:
        message = f'Failed to submit task: {e}'
        logger.error(message)
        messagebox.showerror('Error', message)
    except httpx.RequestError as e:
        message = f'An error occurred while making the request: {e}'
        logger.error(message)
        messagebox.showerror('Error', message)


def display_elapsed_time(elapsed_time):
    elapsed_time_label.configure(text=f'Elapsed Time: {elapsed_time}')


def display_html_response(html_content):
    print(html_content)
    styled_html_content = f"""
    <div style="color: #cccccc; font-size: 20px; font-family: '{ui.font[0]}'; letter-spacing: 3px;">
    {html_content}
    </div>
    """
    response_html_label.set_html(styled_html_content)


def cmd_enter_submit_form(event):
    submit_form()


@dataclass
class UIConfig:
    mode: str
    theme: str
    font: tuple[str, int]
    bigpad: int
    smallpad: int


# Example configuration for a larger UI
ui = UIConfig(mode='System', theme='dark-blue', font=('Droid Sans Mono for Powerline', 24), bigpad=30, smallpad=15)

ctk.set_appearance_mode(ui.mode)
ctk.set_default_color_theme(ui.theme)

app = ctk.CTk()
app.title('Get Insights')

set_app_geometry(app, width_percent=45, height_percent=100)

header = ctk.CTkLabel(app, text='Get Insights', font=(ui.font[0], 36))
header.pack(pady=ui.bigpad)

# Create the URL entry
url_label = ctk.CTkLabel(app, text='URL', font=ui.font)
url_label.pack(pady=0)
url_entry = ctk.CTkEntry(app, width=600)
url_entry.pack(pady=ui.smallpad)

# Create the submit button
submit_button = ctk.CTkButton(app, text='Get Insights!', command=submit_form)
submit_button.pack(pady=ui.smallpad)

# Create the Label to display the elapsed time
elapsed_time_label = ctk.CTkLabel(app, text='')
elapsed_time_label.pack(pady=ui.smallpad)


response_html_label = HTMLText(
    app,
    html='',
    background='#1A1A1A',
    borderwidth=0,
    highlightthickness=0,
    padx=ui.bigpad,
    pady=ui.bigpad,
    spacing2=10,
)
response_html_label.pack(fill='both', expand=True)
response_html_label.fit_height()

url_entry.focus_set()
app.bind('<Return>', cmd_enter_submit_form)

app.mainloop()
