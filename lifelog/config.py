#    Lifelog (config.py)
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

import os

APP_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
RES_DIRECTORY = os.path.join(APP_DIRECTORY, "res")
GLADE_FILENAME = "ui.glade"
GLADE_FILEPATH = os.path.join(APP_DIRECTORY, RES_DIRECTORY, GLADE_FILENAME)
