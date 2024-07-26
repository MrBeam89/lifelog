#!/usr/bin/env python3
#    Lifelog (main.py)
#    Copyright (C) 2024 MrBeam89_
#
#    This file is part of Lifelog.
#
#    Lifelog is free software: you can redistribute it and/or modify it under the terms of 
#    the GNU General Public License as published by the Free Software Foundation, 
#    either version 3 of the License, or (at your option) any later version.
#
#    Lifelog is distributed in the hope that it will be useful, but WITHOUT ANY 
#    WARRANTY; without even the implied warranty of MERCHANTABILITY or 
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for 
#    more details.
#
#    You should have received a copy of the GNU General Public License along with 
#    Lifelog. If not, see <https://www.gnu.org/licenses/>. 

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from sqlite3 import Binary

import config
import db_handler

class LifelogApp:
    # Initialize the application
    def __init__(self):
        self.selected_date = None
        self.formated_date = None

        # Initialize the Gtk builder and load the glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(config.GLADE_FILEPATH)

        # Load the main window
        self.main_win = self.builder.get_object("main_win")
        self.main_win.connect("destroy", Gtk.main_quit)

        # Load the main window widgets
        self.new_file_button = self.builder.get_object("new_file_button")
        self.open_file_button = self.builder.get_object("open_file_button")
        self.settings_button = self.builder.get_object("settings_button")

        # Load the main window widgets
        self.calendar = self.builder.get_object("calendar")
        self.entry_textview = self.builder.get_object("entry_textview")
        self.entry_textbuffer = self.builder.get_object("entry_textbuffer")
        self.entry_tagtable = self.builder.get_object("entry_tagtable")
        self.apply_entry_changes_button = self.builder.get_object("apply_entry_changes_button")

        # Load the entry tab of settings notebook
        self.title_entry = self.builder.get_object("title_entry")
        self.tags_entry = self.builder.get_object("tags_entry")
        self.mood_scale = self.builder.get_object("mood_scale")
        self.mood_adjustment = self.builder.get_object("mood_adjustment")

        # Load the image tab of settings notebook
        self.image = self.builder.get_object("image")
        self.add_image_button = self.builder.get_object("add_image_button")
        self.remove_image_button = self.builder.get_object("remove_image_button")

        # Load the statusbar
        self.statusbar = self.builder.get_object("statusbar")
        self.error_statusbar_context_id = self.statusbar.get_context_id("error")
        self.info_statusbar_context_id = self.statusbar.get_context_id("info")

        # Set up the signal handlers
        self.handlers = {
            # Toolbar buttons
            "on_new_file_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_open_file_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_settings_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            
            # Other main widgets
            "on_calendar_day_selected": self.on_calendar_day_selected,
            "on_apply_entry_changes_button_clicked": self.on_apply_entry_changes_button_clicked,

            # Format style buttons
            "on_bold_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_italic_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_underline_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_strikethrough_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),

            # Format justification buttons
            "on_justify_left_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_justify_center_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_justify_right_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_justify_fill_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),

            # Format background/foreground text color
            "on_foreground_color_colorbutton_color_set": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_background_color_colorbutton_color_set": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_foreground_color_apply_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_background_color_apply_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),

            # Image tab buttons
            "on_add_image_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_remove_image_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
        }
        self.builder.connect_signals(self.handlers)
        
    
    # Show the main window and start the main loop
    def main(self):
        self.main_win.show_all()

        # Get current date
        self.selected_date = self.calendar.get_date()
        self.formated_date = f"{self.selected_date[0]}-{self.selected_date[1]}-{self.selected_date[2]}"

        statusbar_date_message = f"Welcome! The current date is : {self.formated_date}"
        self.change_statusbar_message(self.info_statusbar_context_id, statusbar_date_message)
    
        # By default, image isn't loaded
        self.image.set_visible(False)
        self.remove_image_button.set_visible(False)

        # Start the main loop
        Gtk.main()


    def on_calendar_day_selected(self, widget):
        # Get the selected date
        self.selected_date = self.calendar.get_date()
        self.formated_date = f"{self.selected_date[0]}-{self.selected_date[1]}-{self.selected_date[2]}"

        # Show the selected date in the status bar
        statusbar_date_message = f"Selected date is : {self.selected_date[0]}-{self.selected_date[1]}-{self.selected_date[2]}"
        self.change_statusbar_message(self.info_statusbar_context_id, statusbar_date_message)


    # Change the statusbar message
    def change_statusbar_message(self, context_id, message):
        self.statusbar.push(context_id, message)


    # Save the changes made to an entry
    def on_apply_entry_changes_button_clicked(self, widget):
        entry_date = self.formated_date
        entry_title = self.title_entry.get_text()
        entry_tags = self.tags_entry.get_text()
        entry_mood = int(self.mood_adjustment.get_value())
        entry_content = self.entry_textbuffer.get_text(self.entry_textbuffer.get_start_iter(), self.entry_textbuffer.get_end_iter(), False)
        entry_texttagtable = "" # Todo later
        entry_image = Binary(b'').tobytes()
 
        db = db_handler.DbHandler(config.DB_FILEPATH)
        db.update_entry(entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_texttagtable, entry_image)
        db.close()

        self.change_statusbar_message(self.info_statusbar_context_id, "Entry saved successfully!")


# Start the application
if __name__ == "__main__":
    app = LifelogApp()
    app.main()
