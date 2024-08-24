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

import config
import db_handler

class LifelogApp:
    # Initialize the application
    def __init__(self):
        self.db_filepath = ""
        self.is_file_opened = False

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

        # Set up the signal handlers
        self.handlers = {
            # Main window signals
            "on_main_win_destroy": Gtk.main_quit,
            "on_main_win_delete_event": self.on_main_win_delete_event,

            # Toolbar buttons
            "on_new_file_button_clicked": self.on_new_file_button_clicked,
            "on_open_file_button_clicked": self.on_open_file_button_clicked,
            "on_settings_button_clicked": lambda *args: self.change_statusbar_message(self.error_statusbar_context_id,"This feature isn't implemented yet!"),
            
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
        }
        self.builder.connect_signals(self.handlers)
        
    
    # Show the main window and start the main loop
    def main(self):
        self.main_win.show_all()

        # Automatically selects today's entry and updates the date
        self.selected_date = self.calendar.get_date()
        self.selected_date_original = self.selected_date
        self.db_formatted_date = f"{self.selected_date[0]}-{self.selected_date[1]+1}-{self.selected_date[2]}"
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
        self.unsaved_entry_title = self.title_entry.get_text()
        self.unsaved_entry_tags = self.tags_entry.get_text()
        self.unsaved_entry_mood = int(self.mood_adjustment.get_value())
        self.unsaved_entry_image = Binary(b'').tobytes()

        is_entry_title_modified = self.saved_entry_title != self.unsaved_entry_title
        is_entry_tags_modified = self.saved_entry_tags != self.unsaved_entry_tags
        is_entry_mood_modified = self.saved_entry_mood != self.unsaved_entry_mood
        is_textbuffer_modified = self.entry_textbuffer.get_modified()
        is_entry_image_modified = self.saved_entry_image != self.unsaved_entry_image

        return is_entry_title_modified or is_entry_tags_modified or is_entry_mood_modified or is_textbuffer_modified or is_entry_image_modified


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

        # Open the filechooser dialog
        filechooser_win = temp_builder.get_object("filechooser_win")
        ok_button_filechooser_win = temp_builder.get_object("ok_button_filechooser_win")

        # Modify to a save filechooser dialog
        filechooser_win.set_title("Save as")
        filechooser_win.set_action(Gtk.FileChooserAction.SAVE)
        ok_button_filechooser_win.set_label(Gtk.STOCK_SAVE_AS)

        # Get the selected file or cancel the operation
        filechooser_response = filechooser_win.run()
        if filechooser_response == Gtk.ResponseType.OK:
            # Reset the database and enable saving entries
            self.db_filepath = filechooser_win.get_filename()
            db = db_handler.DbHandler(self.db_filepath)
            db.reset_database()
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

        # Open the filechooser dialog
        filechooser_win = temp_builder.get_object("filechooser_win")
        ok_button_filechooser_win = temp_builder.get_object("ok_button_filechooser_win")

        # Modify to an open filechooser dialog
        ok_button_filechooser_win.set_label(Gtk.STOCK_OPEN)
        filechooser_win.set_title("Open File")
        filechooser_win.set_action(Gtk.FileChooserAction.OPEN)

        # Get the selected file or cancel the operation
        filechooser_response = filechooser_win.run()
        if filechooser_response == Gtk.ResponseType.OK:
            # Get the database filepath
            self.db_filepath = filechooser_win.get_filename()
            
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
                self.title_entry.set_text(unsaved_entry_title)
                self.tags_entry.set_text(unsaved_entry_tags)
                self.mood_adjustment.set_value(unsaved_entry_mood)
                
                self.entry_textbuffer.set_text("")               # Clear the buffer
                entry_end = self.entry_textbuffer.get_end_iter() # Get the position of the end of the buffer to insert back the content
                self.entry_textbuffer.deserialize(self.entry_textbuffer, self.entry_textbuffer_tags, entry_end, unsaved_entry_content) # Reinsert the content

                self.entry_textbuffer.set_modified(True)

                return


        # Get the selected date and format it to database and user readable format
        self.selected_date = self.calendar.get_date()
        self.selected_date_original = self.selected_date
        self.db_formatted_date = f"{self.selected_date[0]}-{self.selected_date[1]+1}-{self.selected_date[2]}"
        date_obj = datetime.strptime(self.db_formatted_date, "%Y-%m-%d")
        self.user_formatted_date = date_obj.strftime("%b %d, %Y")

        # Get the entry with the corresponding date from the database
        db = db_handler.DbHandler(self.db_filepath)
        entry = db.get_entry_from_date(self.db_formatted_date)
        db.close()

        # If entry doesn't exist, use default values
        if not entry:
            entry = ["", "", "", "", 50, "", Binary(b'').tobytes()]

        # Used to verify the presence of unsaved changes
        self.saved_entry_title = entry[2]
        self.saved_entry_tags = entry[3]
        self.saved_entry_mood = entry[4]
        self.saved_entry_content = entry[5]
        self.saved_entry_image = entry[6]

        # Display the entry info (not entry content)
        self.title_entry.set_text(self.saved_entry_title)
        self.tags_entry.set_text(self.saved_entry_tags)
        self.mood_adjustment.set_value(int(self.saved_entry_mood))
        
        # Display the entry content
        self.entry_textbuffer.set_text("")               # Clear the buffer
        entry_end = self.entry_textbuffer.get_end_iter() # Get the position of the end of the buffer to insert the new content
        if entry:
            self.entry_textbuffer.deserialize(self.entry_textbuffer, self.entry_textbuffer_tags, entry_end, self.saved_entry_content) # Insert the content

        self.entry_textbuffer.set_modified(False)

        #self.image.set_visible(bool(entry[6]))
        #self.remove_image_button.set_visible(True if self.saved_entry_image else False)

        # Change the window title and statusbar message
        if entry[2]:
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date} - {entry[2]}")
            self.change_statusbar_message(self.info_statusbar_context_id, f"Entry found for date : {self.user_formatted_date}")
        else: # If no entry found for selected date
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date}")
            self.change_statusbar_message(self.info_statusbar_context_id, f"No existing entry found for date : {self.user_formatted_date}")


    # Mark the days of the existing entries
    def on_calendar_month_changed(self, widget):
        # Unmark all days
        for day in range(1, 32):
            if self.calendar.get_day_is_marked(day):
                self.calendar.unmark_day(day)

        # Get the month and year from the calendar
        month = self.calendar.get_property("month")+1
        year = self.calendar.get_property("year")

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

        entry_date = self.db_formatted_date

        # Get the entry data from the widgets (not entry content)
        entry_title = self.title_entry.get_text()
        entry_tags = self.tags_entry.get_text()
        entry_mood = int(self.mood_adjustment.get_value())

        # Serialize the textbuffer
        entry_start, entry_end = self.entry_textbuffer.get_bounds()
        entry_content = self.entry_textbuffer.serialize(self.entry_textbuffer, self.entry_textbuffer_tags, entry_start, entry_end)

        entry_image = Binary(b'').tobytes()
 
        # Update or add the entry in the database
        db = db_handler.DbHandler(self.db_filepath)
        db.update_entry(entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_image)
        db.close()

        self.entry_textbuffer.set_modified(False)

        # Update the title of the main window with the date and entry title if there is one
        if entry_title:
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date} - {entry_title}")
        else:
            self.main_win.set_title(f"Lifelog - {self.user_formatted_date}")

        # Mark the entry day in the calendar
        self.on_calendar_month_changed(self.calendar)

        # Change the statusbar message and mark the buffer as not modified
        self.change_statusbar_message(self.info_statusbar_context_id, "Entry saved successfully!")


    def on_bold_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()   # Get selection bounds
        self.entry_textbuffer.apply_tag_by_name("bold", selection_start, selection_end) # Apply the tag to the selected part of the buffer
    

    def on_italic_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()     # Get selection bounds
        self.entry_textbuffer.apply_tag_by_name("italic", selection_start, selection_end) # Apply the tag to the selected part of the buffer
    

    def on_underline_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()        # Get selection bounds
        self.entry_textbuffer.apply_tag_by_name("underline", selection_start, selection_end) # Apply the tag to the selected part of the buffer

    
    def on_strikethrough_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()            # Get selection bounds
        self.entry_textbuffer.apply_tag_by_name("strikethrough", selection_start, selection_end) # Apply the tag to the selected part of the buffer


    def on_justify_left_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()           # Get selection bounds
        self.reset_justification(selection_start, selection_end)                                # All alignments are mutually exclusive
        self.entry_textbuffer.apply_tag_by_name("justify_left", selection_start, selection_end) # Apply the tag to the selected part of the buffer


    def on_justify_center_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()             # Get selection bounds
        self.reset_justification(selection_start, selection_end)                                  # All alignments are mutually exclusive
        self.entry_textbuffer.apply_tag_by_name("justify_center", selection_start, selection_end) # Apply the tag to the selected part of the buffer


    def on_justify_right_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()            # Get selection bounds
        self.reset_justification(selection_start, selection_end)                                 # All alignments are mutually exclusive
        self.entry_textbuffer.apply_tag_by_name("justify_right", selection_start, selection_end) # Apply the tag to the selected part of the buffer

    
    def on_justify_fill_button_clicked(self, widget):
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()           # Get selection bounds
        self.reset_justification(selection_start, selection_end)                                # All alignments are mutually exclusive
        self.entry_textbuffer.apply_tag_by_name("justify_fill", selection_start, selection_end) # Apply the tag to the selected part of the buffer


    # Reset the justify tags to allow changing the alignment of an already aligned paragraph
    def reset_justification(self, selection_start, selection_end):
        self.entry_textbuffer.remove_tag_by_name("justify_left", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_center", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_right", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_fill", selection_start, selection_end)


    def on_format_reset_button_clicked(self, widget):
        # Remove the tags from the selected text
        selection_start, selection_end = self.entry_textbuffer.get_selection_bounds()
        self.entry_textbuffer.remove_tag_by_name("bold", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("italic", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("underline", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("strikethrough", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_left", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_center", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_right", selection_start, selection_end)
        self.entry_textbuffer.remove_tag_by_name("justify_fill", selection_start, selection_end)


# Start the application
if __name__ == "__main__":
    app = LifelogApp()
    app.main()
