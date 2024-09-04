import logging
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox

import customtkinter as ctk
import httpx

from ichrisbirch.config import get_settings
from ichrisbirch.gui.utils import set_app_geometry
from ichrisbirch.models.task import TaskCategory

settings = get_settings()
logger = logging.getLogger('gui.tasks_add')

TASK_CATEGORIES = [t.value for t in TaskCategory]


def submit_form():
    name = name_entry.get()
    category = category_combobox.get()
    priority = priority_entry.get()
    notes = notes_textbox.get('1.0', tk.END).strip()

    if not name or not category or not priority.isdigit():
        messagebox.showwarning('Validation Error', 'Please fill all fields correctly.')
        return

    url = 'http://api.ichrisbirch.com/tasks/'
    # url = 'http://localhost:6201/tasks/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',  # Placeholder for authorization header
    }
    data = {'name': name, 'category': category, 'priority': int(priority), 'notes': notes}

    try:
        response = httpx.post(url, headers=headers, json=data)
        response.raise_for_status()
        messagebox.showinfo('Success', 'Task submitted successfully!')
        app.destroy()
    except httpx.HTTPStatusError as e:
        message = f'Failed to submit task: {e}'
        logger.error(message)
        messagebox.showerror('Error', message)
    except httpx.RequestError as e:
        message = f'An error occurred while making the request: {e}'
        logger.error(message)
        messagebox.showerror('Error', message)


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
app.title('Add New Priority Task')

set_app_geometry(app, width_percent=40, height_percent=70)

center_frame = ctk.CTkFrame(app)
center_frame.pack(padx=ui.bigpad, pady=ui.bigpad, expand=True)

header = ctk.CTkLabel(center_frame, text='Add New Priority Task', font=(ui.font[0], 36))
header.grid(row=0, column=0, padx=ui.bigpad, pady=ui.bigpad)

name_label = ctk.CTkLabel(center_frame, text='Name:', font=ui.font)
name_entry = ctk.CTkEntry(center_frame, font=ui.font, height=45, width=400)
name_label.grid(row=1, column=0, padx=ui.bigpad, pady=(ui.bigpad, ui.smallpad))
name_entry.grid(row=2, column=0, padx=ui.bigpad, pady=(0, ui.bigpad))

category_label = ctk.CTkLabel(center_frame, text='Category:', font=ui.font)
category_combobox = ctk.CTkComboBox(
    center_frame, font=ui.font, dropdown_font=ui.font, height=45, width=400, values=TASK_CATEGORIES
)
category_label.grid(row=3, column=0, padx=ui.bigpad, pady=(ui.bigpad, ui.smallpad))
category_combobox.grid(row=4, column=0, padx=ui.bigpad, pady=(0, ui.bigpad))

priority_label = ctk.CTkLabel(center_frame, text='Priority:', font=ui.font)
priority_entry = ctk.CTkEntry(center_frame, font=ui.font, height=45, width=80)
priority_label.grid(row=5, column=0, padx=ui.bigpad, pady=(ui.bigpad, ui.smallpad))
priority_entry.grid(row=6, column=0, padx=ui.bigpad, pady=(0, ui.bigpad))

notes_label = ctk.CTkLabel(center_frame, text='Notes:', font=ui.font)
notes_textbox = ctk.CTkTextbox(center_frame, font=ui.font, width=600, height=180)
notes_label.grid(row=7, column=0, padx=ui.bigpad, pady=(ui.bigpad, ui.smallpad))
notes_textbox.grid(row=8, column=0, padx=ui.bigpad, pady=(0, ui.bigpad))

submit_button = ctk.CTkButton(center_frame, text='Add Task', font=ui.font, width=300, height=50, command=submit_form)
submit_button.grid(row=9, column=0, columnspan=2, padx=ui.bigpad, pady=ui.bigpad)

name_entry.focus_set()
app.bind('<Command-Return>', cmd_enter_submit_form)

app.mainloop()
