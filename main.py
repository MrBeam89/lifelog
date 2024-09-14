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
from gi.repository import Gtk, Pango
from sqlite3 import Binary
from datetime import date, datetime
from os import urandom

import config
import db_handler
import crypto_utils

class LifelogApp:
    # Initialize the application
    def __init__(self):
        self.db_filepath = ""
        self.is_file_opened = False

        # Used for encryption
        self.password = b""
        self.aes_key = b"\x00" * 32
        self.aes_cipher = crypto_utils.AESCipher(self.aes_key)
        self.scrypt_hasher = crypto_utils.scryptHasher()

        # Date related variables for the calendar, the database and the user
        self.current_date = str(date.today()).split("-")
        self.selected_date = None
        self.selected_date_original = None
        self.db_formatted_date = None
        self.user_formatted_date = None

        # Used to check if there are unsaved changes
        self.unsaved_entry_title = ""
        self.unsaved_entry_tags = ""
        self.unsaved_entry_mood = 50
        self.unsaved_entry_image = Binary(b'').tobytes()

        # Default entry details
        self.saved_entry_title = ""
        self.saved_entry_tags = ""
        self.saved_entry_mood = 50
        self.saved_entry_image = Binary(b'').tobytes()

        self.trigger_callback_func = True # Set to False to avoid recursion when necessary

        # Initialize the Gtk builder and load the glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(config.GLADE_FILEPATH)

        # Load the main window
        self.main_win = self.builder.get_object("main_win")

        # Load the main window widgets
        self.calendar = self.builder.get_object("calendar")
        self.entry_textview = self.builder.get_object("entry_textview")
        self.entry_textbuffer = self.builder.get_object("entry_textbuffer")
        self.entry_textbuffer_tags = self.entry_textbuffer.register_deserialize_tagset()
        self.apply_entry_changes_button = self.builder.get_object("apply_entry_changes_button")

        # Load the entry tab of settings notebook
        self.title_entry = self.builder.get_object("title_entry")
        self.tags_entry = self.builder.get_object("tags_entry")
        self.mood_scale = self.builder.get_object("mood_scale")
        self.mood_adjustment = self.builder.get_object("mood_adjustment")

        # Tags for the styling the text
        self.bold_tag = self.entry_textbuffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.italic_tag = self.entry_textbuffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.underline_tag = self.entry_textbuffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        self.strikethrough_tag = self.entry_textbuffer.create_tag("strikethrough", strikethrough=True)

        # Tags for aligning the text (all are mutually exclusive)
        self.justify_left_tag = self.entry_textbuffer.create_tag("justify_left", justification=Gtk.Justification.LEFT)
        self.justify_center_tag = self.entry_textbuffer.create_tag("justify_center", justification=Gtk.Justification.CENTER)
        self.justify_right_tag = self.entry_textbuffer.create_tag("justify_right", justification=Gtk.Justification.RIGHT)
        self.justify_fill_tag = self.entry_textbuffer.create_tag("justify_fill", justification=Gtk.Justification.FILL)

        # Load the image tab of settings notebook
        self.image = self.builder.get_object("image")
        self.add_image_button = self.builder.get_object("add_image_button")
        self.remove_image_button = self.builder.get_object("remove_image_button")

        # Load the statusbar
        self.statusbar = self.builder.get_object("statusbar")
        self.error_statusbar_context_id = self.statusbar.get_context_id("error")
        self.info_statusbar_context_id = self.statusbar.get_context_id("info")

        # Widgets for the password dialogs, loaded when necessary
        self.password_set_entry = None
        self.password_set_retype_entry = None
        self.message_label_password_set_dialog = None

        # Set up the signal handlers
        self.handlers = {
            # Main window signals
            "on_main_win_destroy": Gtk.main_quit,
            "on_main_win_delete_event": self.on_main_win_delete_event,

            # Password dialogs signals
            "on_password_set_dialog_response": self.on_password_set_dialog_response,
            "on_password_verify_dialog_response": self.on_password_verify_dialog_response,

            # Toolbar buttons
            "on_new_file_button_clicked": self.on_new_file_button_clicked,
            "on_open_file_button_clicked": self.on_open_file_button_clicked,
            "on_search_button_clicked": self.on_search_button_clicked,
            "on_today_button_clicked": self.on_today_button_clicked,
            "on_settings_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_about_button_clicked": self.on_about_button_clicked,
            
            # Other main widgets
            "on_calendar_day_selected": self.on_calendar_day_selected,
            "on_calendar_month_changed": self.on_calendar_month_changed,
            "on_calendar_next_year": self.on_calendar_month_changed, # Logic is the same as "on_calendar_month_changed"
            "on_calendar_prev_year": self.on_calendar_month_changed, # Same
            "on_apply_entry_changes_button_clicked": self.on_apply_entry_changes_button_clicked,

            # Format style buttons
            "on_bold_button_clicked": self.on_bold_button_clicked,
            "on_italic_button_clicked": self.on_italic_button_clicked,
            "on_underline_button_clicked": self.on_underline_button_clicked,
            "on_strikethrough_button_clicked": self.on_strikethrough_button_clicked,

            # Format justification buttons
            "on_justify_left_button_clicked": self.on_justify_left_button_clicked,
            "on_justify_center_button_clicked": self.on_justify_center_button_clicked,
            "on_justify_right_button_clicked": self.on_justify_right_button_clicked,
            "on_justify_fill_button_clicked": self.on_justify_fill_button_clicked,

            # Format reset button
            "on_format_reset_button_clicked": self.on_format_reset_button_clicked,

            # Image tab buttons
            "on_add_image_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            "on_remove_image_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),

            # Signals for the search dialog
            "on_search_button_search_win_clicked": self.on_search_button_search_win_clicked,
            "on_search_treeview_row_activated": self.on_search_treeview_row_activated,
        }
        self.builder.connect_signals(self.handlers)
        
    
    # Show the main window and start the main loop
    def main(self):
        self.main_win.show_all()

        # Automatically selects today's entry and updates the date
        self.selected_date = self.calendar.get_date()
        self.selected_date_original = self.selected_date
        self.db_formatted_date = f"{self.selected_date[0]}-{str(self.selected_date[1]+1).zfill(2)}-{str(self.selected_date[2]).zfill(2)}"
        date_obj = datetime.strptime(self.db_formatted_date, "%Y-%m-%d")
        self.user_formatted_date = date_obj.strftime("%b %d, %Y")

        self.on_calendar_day_selected(self.calendar)
        self.on_calendar_month_changed(self.calendar)

        statusbar_date_message = f"Welcome! The current date is : {self.user_formatted_date}"
        self.change_statusbar_message(self.info_statusbar_context_id, statusbar_date_message)

        # By default, image isn't loaded
        self.image.set_visible(False)
        self.remove_image_button.set_visible(False)

        # Start the main loop
        Gtk.main()


    def check_for_unsaved_changes(self):
        # Get the unsaved entry changes
        self.unsaved_entry_title = self.title_entry.get_text()
        self.unsaved_entry_tags = self.tags_entry.get_text()
        self.unsaved_entry_mood = int(self.mood_adjustment.get_value())
        entry_start, entry_end = self.entry_textbuffer.get_bounds()
        self.unsaved_entry_content = self.entry_textbuffer.serialize(self.entry_textbuffer, self.entry_textbuffer_tags, entry_start, entry_end)
        self.unsaved_entry_image = Binary(b'').tobytes()

        # Compare them to the saved entry details
        is_entry_title_modified = self.saved_entry_title != self.unsaved_entry_title
        is_entry_tags_modified = self.saved_entry_tags != self.unsaved_entry_tags
        is_entry_mood_modified = self.saved_entry_mood != self.unsaved_entry_mood
        is_entry_content_modified = self.entry_textbuffer.get_modified()
        is_entry_image_modified = self.saved_entry_image != self.unsaved_entry_image

        # Return True if any change has been made
        return is_entry_title_modified or is_entry_tags_modified or is_entry_mood_modified or is_entry_content_modified or is_entry_image_modified


    def open_unsaved_changes_dialog(self):
        # Temporary builder to fix the filechooser dialog being empty after closing and reopening
        temp_builder = Gtk.Builder()
        temp_builder.add_from_file(config.GLADE_FILEPATH)
        temp_builder.connect_signals(self.handlers)

        unsaved_changes_dialog = temp_builder.get_object("unsaved_changes_dialog")
        dialog_response = unsaved_changes_dialog.run()
        if dialog_response == Gtk.ResponseType.NO:
            unsaved_changes_dialog.destroy()
            return False

        # If the user wants to ignore the changes
        elif dialog_response == Gtk.ResponseType.YES:
            unsaved_changes_dialog.destroy()
            return True


    def on_password_set_dialog_response(self, dialog, response):        
        if response == Gtk.ResponseType.OK:
            # Get the password from both Gtk.Entry(s)
            password = self.password_set_entry.get_text()
            retyped_password = self.password_set_retype_entry.get_text()
            
            # If the passwords are not the same, stop the dialog from closing
            if password != retyped_password:
                self.message_label_password_set_dialog.set_text("Passwords don't match!")
                dialog.stop_emission_by_name("response")
                return True

            # If the password is too short, stop the dialog from closing
            elif len(password) < 8:
                self.message_label_password_set_dialog.set_text("Password must be at least 8 characters long!")
                dialog.stop_emission_by_name("response")
                return True

            # If the passwords are the same and long enough, store the password, close the dialog and proceed
            else:
                self.password = password.encode('utf-8')
                return False
            

    def on_password_verify_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            self.password = self.password_verify_entry.get_text().encode('utf-8')

            # Get the encryption details
            db = db_handler.DbHandler(self.temp_db_filepath)
            encryption_salt = db.get_setting("encryption_salt")
            password_verification_salt = db.get_setting("password_verification_salt")
            password_verification_hash = db.get_setting("password_verification_hash")
            db.close()

            # Hash the input password with the password verification salt
            input_password_hash = self.scrypt_hasher.hash_password(self.password, password_verification_salt)

            # If the hashes match (password is correct)
            if input_password_hash == password_verification_hash:
                # Generate the key and load it
                self.aes_key = self.scrypt_hasher.hash_password(self.password, encryption_salt)
                self.aes_cipher = crypto_utils.AESCipher(self.aes_key)

                # Close the dialog and proceed
                return False

            # If the hashes don't match (password is incorrect)
            else:
                # Display a message and stop the dialog from closing
                self.message_label_password_verify_dialog.set_text("Wrong password!")
                dialog.stop_emission_by_name("response")
                return True


    def on_main_win_delete_event(self, widget, event):
        # Check for unsaved changes
        if self.check_for_unsaved_changes():
            unsaved_changes_dialog_response = self.open_unsaved_changes_dialog()
        
            # If the user wants to quit and ignore the unsaved changes
            if unsaved_changes_dialog_response == True:
                Gtk.main_quit()
        
            # If the user doesn't want to ignore the changes, don't quit
            else:
                return True

        # If there are no unsaved changes
        Gtk.main_quit()


    def on_new_file_button_clicked(self, widget):
        # Check for unsaved changes
        if self.check_for_unsaved_changes():
            unsaved_changes_dialog_response = self.open_unsaved_changes_dialog()
            if unsaved_changes_dialog_response == False:
                return

        # Temporary builder to fix the filechooser dialog being empty after closing and reopening
        temp_builder = Gtk.Builder()
        temp_builder.add_from_file(config.GLADE_FILEPATH)
        temp_builder.connect_signals(self.handlers)

        # Load the filechooser dialog and button, and the password set dialog with its entries
        filechooser_win = temp_builder.get_object("filechooser_win")
        ok_button_filechooser_win = temp_builder.get_object("ok_button_filechooser_win")
        password_set_dialog = temp_builder.get_object("password_set_dialog")
        self.password_set_entry = temp_builder.get_object("password_set_entry")
        self.password_set_retype_entry = temp_builder.get_object("password_set_retype_entry")
        self.message_label_password_set_dialog = temp_builder.get_object("message_label_password_set_dialog")

        # Modify to a save filechooser dialog
        filechooser_win.set_title("Save as")
        filechooser_win.set_action(Gtk.FileChooserAction.SAVE)
        ok_button_filechooser_win.set_label(Gtk.STOCK_SAVE_AS)

        # Get the selected file or cancel the operation
        filechooser_response = filechooser_win.run()
        if filechooser_response == Gtk.ResponseType.OK:
            self.temp_db_filepath = filechooser_win.get_filename()
            filechooser_win.destroy()

            # Run the dialog to get the password used for encryption
            self.message_label_password_set_dialog.set_text("Waiting for password confirmation...")
            password_set_response = password_set_dialog.run()

            # Stop the process if the user cancels the password dialog, proceed otherwise
            if password_set_response == Gtk.ResponseType.CANCEL:
                password_set_dialog.destroy()
                return

            password_set_dialog.destroy()

            # Reset the database and enable saving entries
            self.db_filepath = self.temp_db_filepath
            db = db_handler.DbHandler(self.db_filepath)
            db.reset_database()

            # Setup the encryption
            encryption_salt = urandom(16)
            password_verification_salt = urandom(16)
            password_verification_hash = self.scrypt_hasher.hash_password(self.password, password_verification_salt)
            self.aes_key = self.scrypt_hasher.hash_password(self.password, encryption_salt) # Use a scrypt hash as the encryption key for AES-256
            self.aes_cipher = crypto_utils.AESCipher(self.aes_key) # Load the key

            # Save the encryption settings to the database
            db.update_setting("encryption_salt", encryption_salt)
            db.update_setting("password_verification_salt", password_verification_salt)
            db.update_setting("password_verification_hash", password_verification_hash)

            # Close the database
            db.close()

            self.is_file_opened = True
            self.entry_textbuffer.set_modified(False)

            # Set the selected calendar date to today
            self.current_date = str(date.today()).split("-")
            self.calendar.select_day(int(self.current_date[2]))
            self.calendar.select_month(int(self.current_date[1])-1, int(self.current_date[0]))

            # Update the statusbar to the greet message
            statusbar_date_message = f"Welcome! The current date is : {self.user_formatted_date}"
            self.change_statusbar_message(self.info_statusbar_context_id, statusbar_date_message)

            # By default, image isn't loaded
            self.image.set_visible(False)
            self.remove_image_button.set_visible(False)
        elif filechooser_response == Gtk.ResponseType.CANCEL:
            pass
        
        # Close the filechooser dialog
        filechooser_win.destroy()


    def on_open_file_button_clicked(self, widget):
        # Check for unsaved changes
        if self.check_for_unsaved_changes():
            unsaved_changes_dialog_response = self.open_unsaved_changes_dialog()
            if unsaved_changes_dialog_response == False:
                return
            
        # Temporary builder to fix the filechooser dialog being empty after closing and reopening
        temp_builder = Gtk.Builder()
        temp_builder.add_from_file(config.GLADE_FILEPATH)
        temp_builder.connect_signals(self.handlers)

        # Load the filechooser dialog and button, and the password verify dialog with its entry and label
        filechooser_win = temp_builder.get_object("filechooser_win")
        ok_button_filechooser_win = temp_builder.get_object("ok_button_filechooser_win")
        password_verify_dialog = temp_builder.get_object("password_verify_dialog")
        self.password_verify_entry = temp_builder.get_object("password_verify_entry")
        self.message_label_password_verify_dialog = temp_builder.get_object("message_label_password_verify_dialog")

        # Modify to an open filechooser dialog
        ok_button_filechooser_win.set_label(Gtk.STOCK_OPEN)
        filechooser_win.set_title("Open File")
        filechooser_win.set_action(Gtk.FileChooserAction.OPEN)

        # Get the selected file or cancel the operation
        filechooser_response = filechooser_win.run()
        if filechooser_response == Gtk.ResponseType.OK:
            # Temporarily store the database file path and close the filechooser dialog
            self.temp_db_filepath = filechooser_win.get_filename()
            filechooser_win.destroy()

            # Run the dialog to verify the password
            password_verify_dialog_response = password_verify_dialog.run()
            
            # Stop the process if the user cancels the password dialog, proceed otherwise
            if password_verify_dialog_response == Gtk.ResponseType.CANCEL:
                password_verify_dialog.destroy()
                return
            password_verify_dialog.destroy()

            # Set the database filepath
            self.db_filepath = self.temp_db_filepath

            # Set the selected calendar date to today
            self.entry_textbuffer.set_modified(False)
            self.current_date = str(date.today()).split("-")
            self.calendar.select_day(int(self.current_date[2]))
            self.calendar.select_month(int(self.current_date[1])-1, int(self.current_date[0]))

            # Update the statusbar to the greet message and enable saving entries
            self.is_file_opened = True
            statusbar_date_message = f"Welcome! The current date is : {self.user_formatted_date}"
            self.change_statusbar_message(self.info_statusbar_context_id, statusbar_date_message)

            # By default, image isn't loaded
            self.image.set_visible(False)
            self.remove_image_button.set_visible(False)
        elif filechooser_response == Gtk.ResponseType.CANCEL:
            pass
        
        # Close the filechooser dialog
        filechooser_win.destroy()
        

    def on_search_button_clicked(self, widget):
        # Unable to search if no file is opened
        if self.is_file_opened == False:
            self.change_statusbar_message(self.info_statusbar_context_id, "No file is opened!")
            return
        
        # Temporary builder to fix the search dialog being empty after closing and reopening
        temp_builder = Gtk.Builder()
        temp_builder.add_from_file(config.GLADE_FILEPATH)
        temp_builder.connect_signals(self.handlers)
        
        # Load the search dialog and the used widgets for them to be able to be accessed by on_search_button_search_win_clicked
        search_dialog = temp_builder.get_object("search_dialog")
        self.from_month_combobox = temp_builder.get_object("from_month_combobox")
        self.from_day_combobox = temp_builder.get_object("from_day_combobox")
        self.from_year_entry = temp_builder.get_object("from_year_entry")
        self.to_month_combobox = temp_builder.get_object("to_month_combobox")
        self.to_day_combobox = temp_builder.get_object("to_day_combobox")
        self.to_year_entry = temp_builder.get_object("to_year_entry")
        self.search_criteria_combobox = temp_builder.get_object("search_criteria_combobox")
        self.search_entry = temp_builder.get_object("search_entry")
        self.search_treeview = temp_builder.get_object("search_treeview")
        self.search_liststore = temp_builder.get_object("search_liststore")
        self.search_message_label = temp_builder.get_object("search_message_label")
        self.jump_to_button = temp_builder.get_object("jump_to_button")

        # Resize the search dialog to have the same size as the main window
        main_win_size = self.main_win.get_size()
        search_dialog.set_default_size(main_win_size[0], main_win_size[1])

        # Set the to date to today
        self.from_year_entry.set_text(self.current_date[0])
        self.from_month_combobox.set_active(int(self.current_date[1])-1)
        self.from_day_combobox.set_active(int(self.current_date[2])-1)

        self.to_year_entry.set_text(self.current_date[0])
        self.to_month_combobox.set_active(int(self.current_date[1])-1)
        self.to_day_combobox.set_active(int(self.current_date[2])-1)

        # Make the jump to button not visible until search has been executed and entry selected
        self.jump_to_button.set_visible(False)

        # Run the dialog
        response = search_dialog.run()
        if response == Gtk.ResponseType.OK:
            # Get the selected entry's date (ISO 8601 format), then separate the date into year, month, and day
            selection = self.search_treeview.get_selection()
            model, treeiter = selection.get_selected()
            selected_entry_date = model[treeiter][0].split("-")

            # Check if there are unsaved changes before jumping to the selected entry
            if self.check_for_unsaved_changes():
                unsaved_changes_dialog_response = self.open_unsaved_changes_dialog()
                if unsaved_changes_dialog_response == False:
                    search_dialog.destroy()
                    return
            
            # Set the calendar to the selected entry's date
            self.calendar.select_day(int(selected_entry_date[2]))
            self.calendar.select_month(int(selected_entry_date[1])-1, int(selected_entry_date[0]))
            self.on_calendar_day_selected(self.calendar)
            self.on_calendar_month_changed(self.calendar)

            search_dialog.destroy()

        else: # Cancel button clicked
            search_dialog.destroy()


    def on_search_treeview_row_activated(self, *_):
        # Make the jump to button visible when an entry is selected
        self.jump_to_button.set_visible(True)


    def on_search_button_search_win_clicked(self, widget):
        # Get the date range
        from_month = str(self.from_month_combobox.get_active() + 1).zfill(2)
        from_day = self.from_day_combobox.get_active_text().zfill(2)
        from_year = self.from_year_entry.get_text()
        to_month = str(self.to_month_combobox.get_active() + 1).zfill(2)
        to_day = self.to_day_combobox.get_active_text().zfill(2)
        to_year = self.to_year_entry.get_text()

        # Check if the years are numbers
        if not from_year.isnumeric() or not to_year.isnumeric():
            self.search_message_label.set_text("Invalid year!")
            return

        # Convert the date to the ISO 8601 format (used with the database)
        from_date = f"{from_year}-{from_month}-{from_day}"
        to_date = f"{to_year}-{to_month}-{to_day}"
        
        # Check if the date range is valid
        if from_date > to_date:
            self.search_message_label.set_text("Invalid date range!")
            return

        # Get the search criteria
        criteria_index_entry = {"Title": 1, # Title is the first column
                                "Tags": 2,  # Tags are the second column 
                                "Mood": 3}  # Mood is the third column
        search_criteria = criteria_index_entry[self.search_criteria_combobox.get_active_text()]
        search_content = self.search_entry.get_text()

        # Remove the previous search results
        self.jump_to_button.set_visible(False)
        self.search_liststore.clear()

        # Search from the db
        self.search_message_label.set_text("Searching...")
        db = db_handler.DbHandler(self.db_filepath)
        entries_found = db.get_all_entries_between(from_date, to_date)
        db.close()

        # Filter the entries based on the search criteria
        filtered_entries = []
        for entry in entries_found:
            entry_data = list(entry[1:5]) # Ignore the entry id (from the database) and the entry content

            # Decrypt the entry data for each column except the date column (the first one) as it isn't encrypted
            for column_i in range(1, len(entry_data)):
                entry_data[column_i] = self.aes_cipher.decrypt(entry_data[column_i]).decode("utf-8")
            
            # Check if the entry data contains the search content
            if search_content in entry_data[search_criteria]:
                # Display a more user-friendly date (the original is kept for jumping to the entry)
                user_formatted_date = datetime.fromisoformat(entry_data[0]).strftime("%b %d, %Y")
                entry_data.insert(1, user_formatted_date)

                # Add the entry to the filtered list
                filtered_entries.append(entry_data)

        # Add the elements to the Gtk.Liststore and therefore to the Gtk.TreeView
        for filtered_entry in filtered_entries:
            self.search_liststore.append(filtered_entry)

        # Update the search message to the adequate quantity
        result_message = "Search done! "
        if len(filtered_entries) == 0: result_message += "No matching entry found."
        elif len(filtered_entries) == 1: result_message += "1 matching entry found."
        else: result_message += f"{len(filtered_entries)} matching entries found."
        self.search_message_label.set_text(result_message)


    def on_today_button_clicked(self, widget):
        self.calendar.select_day(int(self.current_date[2]))
        self.calendar.select_month(int(self.current_date[1])-1, int(self.current_date[0]))
        self.on_calendar_day_selected(self.calendar)
        self.on_calendar_month_changed(self.calendar)

    def on_about_button_clicked(self, widget):
        temp_builder = Gtk.Builder()
        temp_builder.add_from_file(config.GLADE_FILEPATH)
        about_dialog = temp_builder.get_object("about_dialog")
        about_dialog.run()
        about_dialog.destroy()


    def on_calendar_day_selected(self, widget):
        if self.trigger_callback_func == False:
            return

        # Check for unsaved changes
        if self.check_for_unsaved_changes():
            unsaved_changes_dialog_response = self.open_unsaved_changes_dialog()

            if unsaved_changes_dialog_response == False:
                # Change the date back without calling this function again (avoid infinite loop)
                self.trigger_callback_func = False
                y, m, d = self.selected_date
                self.calendar.select_day(d)
                self.calendar.select_month(m, y)
                self.trigger_callback_func = True
                
                # Reapply the changes
                self.title_entry.set_text(self.unsaved_entry_title)
                self.tags_entry.set_text(self.unsaved_entry_tags)
                self.mood_adjustment.set_value(self.unsaved_entry_mood)
                
                self.entry_textbuffer.set_text("")               # Clear the buffer
                entry_end = self.entry_textbuffer.get_end_iter() # Get the position of the end of the buffer to insert back the content
                self.entry_textbuffer.deserialize(self.entry_textbuffer, self.entry_textbuffer_tags, entry_end, self.unsaved_entry_content) # Reinsert the content

                self.entry_textbuffer.set_modified(True)

                return False


        # Get the selected date and format it to database and user readable format
        self.selected_date = self.calendar.get_date()
        self.selected_date_original = self.selected_date
        self.db_formatted_date = f"{self.selected_date[0]}-{str(self.selected_date[1]+1).zfill(2)}-{str(self.selected_date[2]).zfill(2)}"
        date_obj = datetime.strptime(self.db_formatted_date, "%Y-%m-%d")
        self.user_formatted_date = date_obj.strftime("%b %d, %Y")

        # Get the entry with the corresponding date from the database
        db = db_handler.DbHandler(self.db_filepath)
        entry = db.get_entry_from_date(self.db_formatted_date)
        db.close()

        # If entry doesn't exist, use default values
        if not entry:
            entry = ["", "", "", "", "", "", Binary(b'').tobytes()]

        # Used to verify the presence of unsaved changes
        encrypted_entry_title = entry[2]
        encrypted_entry_tags = entry[3]
        encrypted_entry_mood = entry[4]
        encrypted_entry_content = entry[5]

        # Decrypt the entry data (and use the default values for empty values)
        self.saved_entry_title = self.aes_cipher.decrypt(encrypted_entry_title).decode("utf-8")
        self.saved_entry_tags = self.aes_cipher.decrypt(encrypted_entry_tags).decode("utf-8")
        self.saved_entry_mood = int(self.aes_cipher.decrypt(encrypted_entry_mood).decode("utf-8") or "50")
        saved_entry_content = self.aes_cipher.decrypt(encrypted_entry_content)
        self.saved_entry_image = entry[6]

        # Display the entry info (not entry content)
        self.title_entry.set_text(self.saved_entry_title)
        self.tags_entry.set_text(self.saved_entry_tags)
        self.mood_adjustment.set_value(int(self.saved_entry_mood))
        
        # Display the entry content
        self.entry_textbuffer.set_text("") # Clear the buffer
        if saved_entry_content: # If there is content
            entry_end = self.entry_textbuffer.get_end_iter() # Get the position of the end of the buffer to insert the new content
            self.entry_textbuffer.deserialize(self.entry_textbuffer, self.entry_textbuffer_tags, entry_end, saved_entry_content) # Insert the content
        self.entry_textbuffer.set_modified(False)

        #self.image.set_visible(bool(entry[6]))
        #self.remove_image_button.set_visible(True if self.saved_entry_image else False)

        # Change the window title and statusbar message
        if self.saved_entry_title:
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date} - {self.saved_entry_title}")
            self.change_statusbar_message(self.info_statusbar_context_id, f"Entry found for date : {self.user_formatted_date}")
        else: # If no entry found for selected date
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date}")
            self.change_statusbar_message(self.info_statusbar_context_id, f"No existing entry found for date : {self.user_formatted_date}")

        return True

    # Mark the days of the existing entries
    def on_calendar_month_changed(self, widget):
        # Unmark all days
        for day in range(1, 32):
            if self.calendar.get_day_is_marked(day):
                self.calendar.unmark_day(day)

        # Get the month and year from the calendar
        month = str(self.calendar.get_property("month")+1).zfill(2)
        year = str(self.calendar.get_property("year"))

        # Get the existing entry dates for the selected month and year
        db = db_handler.DbHandler(self.db_filepath)
        existing_entry_dates = db.get_existing_entry_dates_for_month_year(month, year)
        db.close()

        # Mark the days of the existing entries
        for existing_entry_date in existing_entry_dates:
            day = int(existing_entry_date[0].split("-")[2])
            self.calendar.mark_day(day)


    # Change the statusbar message
    def change_statusbar_message(self, context_id, message):
        self.statusbar.push(context_id, message)


    # Save the changes made to an entry
    def on_apply_entry_changes_button_clicked(self, widget):
        # Check if saving entries is possible
        if self.is_file_opened == False:
            self.change_statusbar_message(self.info_statusbar_context_id, "No file is opened!")
            return

        # Get the entry data from the widgets (not entry content)
        encoded_entry_title = self.title_entry.get_text().encode("utf-8")
        encoded_entry_tags = self.tags_entry.get_text().encode("utf-8")
        encoded_entry_mood = str(int((self.mood_adjustment.get_value()))).encode("utf-8")

        # Serialize the textbuffer
        entry_start, entry_end = self.entry_textbuffer.get_bounds()
        entry_content = self.entry_textbuffer.serialize(self.entry_textbuffer, self.entry_textbuffer_tags, entry_start, entry_end)

        entry_image = Binary(b'').tobytes()
 
        # Encrypt the entry data
        encrypted_entry_title = self.aes_cipher.encrypt(encoded_entry_title)
        encrypted_entry_tags = self.aes_cipher.encrypt(encoded_entry_tags)
        encrypted_entry_mood = self.aes_cipher.encrypt(encoded_entry_mood)
        encrypted_entry_content = self.aes_cipher.encrypt(entry_content)

        # Update or add the entry in the database
        db = db_handler.DbHandler(self.db_filepath)
        db.update_entry(self.db_formatted_date, encrypted_entry_title, encrypted_entry_tags, encrypted_entry_mood, encrypted_entry_content, entry_image)
        db.close()

        # Set the entry data as saved
        self.saved_entry_title = encoded_entry_title.decode("utf-8")
        self.saved_entry_tags = encoded_entry_tags.decode("utf-8")
        self.saved_entry_mood = int(encoded_entry_mood.decode("utf-8"))
        self.entry_textbuffer.set_modified(False)
        self.saved_entry_image = entry_image

        # Update the title of the main window with the date and entry title if there is one
        if self.saved_entry_title:
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date} - {self.saved_entry_title}")
        else:
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date}")

        # Mark the entry day in the calendar
        self.on_calendar_month_changed(self.calendar)

        # Change the statusbar message and mark the buffer as not modified
        self.change_statusbar_message(self.info_statusbar_context_id, "Entry saved successfully!")


    def on_bold_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()   # Get selection bounds
            self.entry_textbuffer.apply_tag_by_name("bold", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                        # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass
    

    def on_italic_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()     # Get selection bounds
            self.entry_textbuffer.apply_tag_by_name("italic", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                          # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass


    def on_underline_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()        # Get selection bounds
            self.entry_textbuffer.apply_tag_by_name("underline", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                             # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass
    
    def on_strikethrough_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()            # Get selection bounds
            self.entry_textbuffer.apply_tag_by_name("strikethrough", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                                 # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass


    def on_justify_left_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()           # Get selection bounds
            self.reset_justification(selection_start, selection_end)                                # All alignments are mutually exclusive
            self.entry_textbuffer.apply_tag_by_name("justify_left", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                                # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass


    def on_justify_center_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()             # Get selection bounds
            self.reset_justification(selection_start, selection_end)                                  # All alignments are mutually exclusive
            self.entry_textbuffer.apply_tag_by_name("justify_center", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                                  # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass


    def on_justify_right_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()            # Get selection bounds
            self.reset_justification(selection_start, selection_end)                                 # All alignments are mutually exclusive
            self.entry_textbuffer.apply_tag_by_name("justify_right", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                                 # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass
    

    def on_justify_fill_button_clicked(self, widget):
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()           # Get selection bounds
            self.reset_justification(selection_start, selection_end)                                # All alignments are mutually exclusive
            self.entry_textbuffer.apply_tag_by_name("justify_fill", selection_start, selection_end) # Apply the tag to the selected part of the buffer
            self.entry_textbuffer.set_modified(True)                                                # Mark the buffer as modified
        # If no text is selected, do nothing
        except ValueError:
            pass


    # Reset the justify tags to allow changing the alignment of an already aligned paragraph
    def reset_justification(self, selection_start, selection_end):
        self.entry_textbuffer.remove_tag_by_name("justify_left", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_center", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_right", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_fill", selection_start, selection_end)


    def on_format_reset_button_clicked(self, widget):
        # Remove the tags from the selected text
        try:
            selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()
            self.entry_textbuffer.remove_tag_by_name("bold", selection_start, selection_end)
            self.entry_textbuffer.remove_tag_by_name("italic", selection_start, selection_end)
            self.entry_textbuffer.remove_tag_by_name("underline", selection_start, selection_end)
            self.entry_textbuffer.remove_tag_by_name("strikethrough", selection_start, selection_end)

            self.reset_justification(selection_start, selection_end)

            self.entry_textbuffer.set_modified(True) # Mark the buffer as modified
        except ValueError:
            pass


# Start the application
if __name__ == "__main__":
    app = LifelogApp()
    app.main()
