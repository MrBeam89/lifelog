#    Lifelog (db_handler.py)
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

import sqlite3

import config

class DbHandler:
    # Initialize the database connection
    def __init__(self, db_filepath:str):
        # Connect to the database and create the cursor
        self.conn = sqlite3.connect(db_filepath)
        self.cursor = self.conn.cursor()

        # If the table doesn't exist, create it
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
	db_id INTEGER PRIMARY KEY AUTOINCREMENT,
	entry_date DATE UNIQUE,
	entry_title TEXT,
	entry_tags TEXT,
	entry_mood INTEGER,
    entry_content TEXT,
	entry_texttagtable TEXT,
	entry_image BLOB
);
        ''')


    # Commit and close the connection database
    def close(self):
        self.conn.commit()
        if self.conn:
            self.conn.close()
            self.conn = None


    # Add or update an entry in the database
    def update_entry(self, entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_texttagtable, entry_image):
        self.cursor.execute('''
        INSERT OR REPLACE INTO entries (entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_texttagtable, entry_image) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_texttagtable, entry_image))


    # Get an entry from the database by its date
    def get_entry_from_date(self, entry_date):
        self.cursor.execute('''
        SELECT * FROM entries WHERE entry_date = ?
        ''', (entry_date,))
        return self.cursor.fetchone()


    # Get all existing entries for a given month and year
    def get_existing_entry_dates_for_month_year(self, month, year):
        query = "SELECT entry_date FROM entries WHERE entry_date LIKE ?"
        self.cursor.execute(query, (f"{year}-{month}-%",))
        return self.cursor.fetchall()