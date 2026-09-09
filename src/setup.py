'''
    setup

    To set up the configuration.
'''

import os
import sys

import sqlite3
import tomlkit
from sqlite3 import Connection, Cursor
from tomlkit.exceptions import ParseError
from tomlkit import TOMLDocument

from src.error import InvalidDatabaseError

def setup_db(nobackup: bool):
    '''Setup the database.'''
    while True:
        confirm_again: str = input(
            "> Do you wish to setup the database? Note that this will destroy old database! (Y/N) ")
        if confirm_again.strip().lower() in ("yes", "y"):
            # Read the configs.
            try:
                with open("config.toml", "r", encoding="utf-8") as f:
                    try:
                        config = tomlkit.parse(f.read())
                        db_path: str = str(config["database"])
                        db_arch: str = str(config["archive"])
                    except ParseError:
                        print(": Config file 'config.toml' contains invalid data.")
                        sys.exit(1)
            except FileNotFoundError:
                print(": Config file 'config.toml' is missing in the root directory.")
                sys.exit(1)
            # Save the old database if the user wants to cancel.
            print(": Saving the old database for potential reversion via CTRL+C...")
            try:
                with open(db_path, "rb") as f:
                    old_db: bytes = f.read()
            except FileNotFoundError:
                raise InvalidDatabaseError("The database is not found.")
            print(": Connecting to the database...")
            # Connect to the database.
            conn: Connection = sqlite3.connect(db_path)
            cursor: Cursor   = conn.cursor()
            try:
                if os.path.exists(db_arch) and not nobackup:
                    while True:
                        ask = input("> Backup file has existed, are you sure to overwrite the old backup file? (Y/N) ")
                        if ask.lower() in ('y', 'yes'):
                            print(": Overwriting the old backup file...")
                            break
                        elif ask.lower() in ('n', 'no'):
                            print(": Cancelling...")
                            sys.exit(0)
                        else:
                            print(": Invalid response! Repeating...")
                if not nobackup:
                    with open(db_arch, "wb") as f:
                        f.write(old_db)
                print(": Writing to the database...")
                with open("sql/database_setup.sql", "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())
                conn.commit()
                conn.close()
                break
            except KeyboardInterrupt:
                print("\n: Reversing...")
                with open(db_path, "wb") as f:
                    f.write(old_db)
                break                   
        elif confirm_again.strip().lower() in ("no", "n"):
            print(": Skipping database setup...")
            break
        else:
            print(": Invalid response! Repeating...")

def setup(db_path: str, db_archive: str, nobackup: bool, limit: float, save: float) -> None:
    '''python3 run.py setup'''
    print(": Initiating setup...")
    # Open or create TOMLDocument if the file does not exist.
    try:
        with open("config.toml", "r", encoding="utf-8") as f:
            doc: TOMLDocument = tomlkit.parse(f.read())
    except FileNotFoundError:
        doc: TOMLDocument = tomlkit.document()
    doc["database"] = db_path
    doc["archive"]  = db_archive
    doc["limit"]    = limit
    doc["save"]     = save
    # Check if the user wishes.
    print("> Here is the config that you are about to apply:\n")
    print(tomlkit.dumps(doc).strip() + "\n")
    # Confirm if the user wants to setup the config.
    while True:
        confirm: str = input("> Do you wish to setup config? Note that this will overwrite the config! (Y/N) ")
        if confirm.strip().lower() in ("yes", "y"):
            with open("config.toml", "r", encoding="utf-8") as f:
                previous: str = f.read()
            try:
                print(": Writing to the config file...")
                with open("config.toml", "w", encoding="utf-8") as f:
                    f.write(tomlkit.dumps(doc))
                break
            except KeyboardInterrupt:
                print("\n: Reversing...")
                with open("config.toml", "w", encoding="utf-8") as f:
                    f.write(previous)
                break                
        elif confirm.strip().lower() in ("no", "n"):
            print(": Skipping setup config...")
            break
        else:
            print(": Invalid response! Repeating...")
    # Set up database as a clean sheet if the user wants.
    setup_db(nobackup)
    print(": Finishing setup...")   
