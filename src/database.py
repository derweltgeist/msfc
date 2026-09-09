import os
import sys

import tomlkit
import sqlite3
import statistics
from tabulate import tabulate
from sqlite3 import Connection, Cursor
from tomlkit import exceptions, TOMLDocument

from src.get import get
from src.other import rupiah
from src.error import (InvalidOrMissingConfig, InvalidCLIArgument, InvalidDatabaseError)

def reset(nobackup: bool) -> None:
    '''python3 run.py database reset'''
    # Read config first to get the db path.
    print(": Reading configuration of the database...")
    try:
        with open("config.toml", "r", encoding="utf-8") as f:
            doc: TOMLDocument = tomlkit.parse(f.read())
    except FileNotFoundError:
        raise InvalidOrMissingConfig("Missing config.toml in the root directory.")
    try:
        db_path: str = str(doc["database"])
    except exceptions.NonExistentKey:
        raise InvalidOrMissingConfig("Missing database entry in config.toml.")
    # Connect to the database.
    print(": Connecting to the database...")
    if not os.path.exists(db_path):
        raise InvalidDatabaseError("The database does not exist.")
    conn: Connection = sqlite3.connect(db_path)
    cursor: Cursor   = conn.cursor()
    while True:
        confirm: str = input("> Do you sure you want to reset? This can't be undone! (Y/N) ")
        if confirm.lower().strip() in ("y", "yes"):
            break
        elif confirm.lower().strip() in ("n", "no"):
            print(": Cancelling...")
            sys.exit(0)
        else:
            print(": Invalid response! Repeating...")
    # Save the old database.
    print(": Saving the old database for potential reversion via CTRL+C...")
    with open(db_path, "rb") as f:
        old_db = f.read()
    # Perform reset.
    try:
        while True:
            ask: str = input(
                f"> Are you sure to reset the database with backup = {not nobackup}? (Y/N) ")
            if ask.lower() in ('y', 'yes'):
                break
            elif ask.lower() in ('n', 'no'):
                print(": Cancelling...")
            else:
                print(": Invalid response! Repeating...")
        print(": Performing database reset, deleting all rows...")
        with open("sql/database_reset.sql", "r", encoding="utf-8") as f:
            try:
                cursor.executescript(f.read())
            except sqlite3.OperationalError:
                raise InvalidDatabaseError(": Invalid database, table TRANSACTIONS does not exist.")
        if not nobackup:
            print(": Writing backup...")
            # Read config first to get the db path.
            try:
                db_archive: str = str(doc["archive"])
            except exceptions.NonExistentKey:
                raise InvalidOrMissingConfig("Missing archive entry in config.toml.") 
            if os.path.exists(db_archive):
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
            with open(db_archive, "wb") as f:
                f.write(old_db)           
        conn.commit()
        conn.close()
    except KeyboardInterrupt:
        print("\n: Reverting...")
        with open(db_path, "wb") as f:
            f.write(old_db)
        sys.exit(0)

def database(choice: str, verbose: bool, nobackup: bool, summary: bool, range: dict[str, str]) -> None:
    '''python3 run.py database ...'''
    if choice == "reset": # python3 run.py database reset
        reset(nobackup)
    elif choice == "show": # python3 run.py database show [range]
        rows: list[sqlite3.Row] = get(range, verbose)
        headers = ['id', 'date', 'value', 'admin', 'total', 'party', 'category', 'active', 'passive', 'pathway', 'wallet']
        print("")
        if not summary:
            print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))
            print("")
        # Total row count
        total_rows = len(rows)
        # Value column.
        values = [row["total"] for row in rows]
        # Sum of a specific column (e.g., 'value' or 'total')
        total_sum = sum(values)
        print(f"Total number of row(s)  : {total_rows} transactions.")
        print(f"Sum of transaction(s)   : {rupiah(total_sum)}")
        if len(values) == 0:
            print(f"Average transaction(s)  : Invalid.")
            print(f"Stdev of transaction(s) : Invalid.")
        else:
            print(f"Average transaction(s)  : {rupiah(total_sum/total_rows)}")
            print(f"Stdev of transaction(s) : {statistics.stdev(values)}")
        print(f"Range of transaction(s) : {rupiah(max(values, default=0) - min(values, default=0))}")
        print("")
        print("* Admin fees are included.")
        print("")
    else:
        raise InvalidCLIArgument(
            "Invalid CLI subcommand for command database: only reset and show are valid.")
    print(": Finishing task...")