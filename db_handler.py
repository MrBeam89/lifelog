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
    def __init__(self, db_filepath:str):
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

    def close(self):
        self.conn.commit()
        if self.conn:
            self.conn.close()
            self.conn = None

    def update_entry(self, entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_texttagtable, entry_image):
        self.cursor.execute('''
        INSERT OR REPLACE INTO entries (entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_texttagtable, entry_image) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (entry_date, entry_title, entry_tags, entry_mood, entry_content, entry_texttagtable, entry_image))