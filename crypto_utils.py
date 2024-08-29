#    Lifelog (crypto_utils.py)
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

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad

from hashlib import scrypt

import argon2

class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        raw = pad(raw, AES.block_size)
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc):
        try:
            iv = enc[:AES.block_size]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return unpad(cipher.decrypt(enc[AES.block_size:]), AES.block_size)
        # Return an empty byte string for empty input
        except ValueError:
            return b''


class scryptHasher:
    @staticmethod
    def hash_password(password, salt):
        n = 2**14 # CPU/Memory cost factor
        r = 8     # Block size
        p = 1     # Parallelization factor
        return scrypt(password=password, salt=salt, n=2**14, r=8, p=1, dklen=32)
