import re
import os
import sys
import calendar
from datetime import datetime
from datetime import date

import tomlkit
import sqlite3
import pandas as pd
from sqlite3 import Connection, Cursor
from tomlkit import exceptions, TOMLDocument

from src.error import (InvalidValueFlagsFormat, InvalidDateIndex, InvalidDatabaseError,
                               InvalidDatabaseShowFlags, InvalidDate, InvalidOrMissingConfig, InvalidGetArg)

def get(range: dict[str, str], verbose: bool, panda: str = "") -> list[sqlite3.Row]:
    '''Retrive data from the database.'''

    query       : str  = "" # Placeholders for queries that will be cleared constantly.
    fquery      : str  = "SELECT * FROM transactions" # This is the actual query that will be send with ? parameters.
    dquery      : str  = "SELECT * FROM transactions" # This is for showcase of the query, not actual query (which may contain parameters)
    single      : bool = True             # Check if only one flag is entered.
    parameters  : list = []               # Parameters for SQL query, only used for other flags (time and value flags are sanitized)
    rows        : list[sqlite3.Row]  = [] # The actual result.

    no_nonexempt: bool = True             # Indicating that there is no non-exempt.

    exempt_other : dict[str, list[str]] = { # List of exempted queries.
        "party"    : [],
        "category" : [],
        "active"   : [],
        "passive"  : [],
        "pathway"  : [],
        "wallet"   : []
    }

    if not all(v is None for v in range.values()): # If no filter flags are provided do not inject WHERE, this is useful for select all.
        fquery += " WHERE"
        dquery += " WHERE"

    fquery += "\n"
    dquery += "\n"

    for arg, value in range.items():
        # Treat the value first.
        if value is None: # If the flag is empty, skip it.
            continue
        else:
            value = value.strip() # Strip value from any whitespace to clean it up.

        # If we are not the first flag, we must append OR or AND to the start of our query.
        if single: # Single being true means only one parameter is inserted.
            fquery += "         "
            dquery += "         "
        else: # If there has been a flag entered before, insert AND or OR
            if arg in ("date", "yearmonth", "monthday", "year", "month", "day", "nvalue", "tvalue", "admin", "id"):
                fquery += "      OR " # This is for time and value flags
                dquery += "      OR "
            else: # The other flags
                fquery += "     AND "
                dquery += "     AND "

        # ======================== TIME FLAGS
        if arg in ("date", "yearmonth", "monthday", "year", "month", "day"):
            time_data: list[str] = value.split(",") # List of ranges.
            time_rang: bool      = False # If there has been a range, this will be set to true.
            form_time: str       = ""    # Temporary container to hold sanitized and formatted YYYY-MM-DD
            match arg:
                case "date": # YYYY-MM-DD:YYYY-MM-DD (--date)
                    length     = 3                         # This means it is X-Y-Z (two dashes, three units)
                    units      = [4, 2, 2]                 # Length of each unit, this means year has 4 chars, month has 2 chars, etc
                    units_name = ["Year", "Month", "Day"]  # Name of each unit
                case "yearmonth": # YYYY-MM:YYYY-MM (--yearmonth)
                    length     = 2
                    units      = [4, 2]
                    units_name = ["Year", "Month"]
                case "monthday": # MM-DD:MM-DD (--monthday)
                    length     = 2
                    units      = [2, 2]
                    units_name = ["Month", "Day"]
                case "year": # YYYY:YYYY (--year)
                    length     = 1
                    units      = [4]
                    units_name = ["Year"]
                case "month": # MM:MM (--month)
                    length     = 1
                    units      = [2]
                    units_name = ["Month"]
                case "day": # DD:DD (--day)
                    length     = 1
                    units      = [2]
                    units_name = ["Day"]
                case _:
                    raise InvalidDateIndex("This is an internal error at show() of database.py, check your date index.")
            for ind, time in enumerate(time_data):
                if time == "":
                    raise InvalidDate(f"Invalid data, there is an empty range at index {ind}")
                if time[0] == "!":
                    time = time[1:]
                    exempt: bool = True
                else:
                    exempt: bool = False
                    no_nonexempt = False
                    single = False # Single is only set to false if we found a non-exempt entry (because if exempt it is injected later)
                if time_rang: # If there has been a time range before, we insert OR.
                    if exempt:
                        query += " OR (date NOT BETWEEN " # If this is the first time range, do not insert OR.
                    else:
                        query += " OR (date BETWEEN"
                else:
                    if exempt:
                        query += "(date NOT BETWEEN "
                    else:
                        query += "(date BETWEEN"
                result = time.split(":") # Split into the start range and end range.
                if len(result) != 2: # There can only be start and end.
                    raise InvalidDatabaseShowFlags(
                        f"Colon usage in --{arg} is invalid, check again.")
                else:
                    start, end = result # Get the start range and end range.

                    # ------------------------- Check the start range.
                    start_split = start.split("-") # Split into units.
                    if len(start_split) != length: # Check if the units array length is correct.
                        raise InvalidDatabaseShowFlags(
                            f"Dash usage in start range {ind} of --{arg} is invalid or you have too little/much units, check again.")
                    # Check the first unit.  
                    if len(start_split[0]) != units[0] or not start_split[0].isdigit():
                        raise InvalidDatabaseShowFlags(
                            f"{units_name[0]} format in start range {ind} of --{arg} is invalid, check again.")
                    else:
                        form_time += f"{start_split[0]}" # Since the first unit is valid, we append it.
                    # Check for the second unit.
                    try:
                        if len(start_split[1]) != units[1] or not start_split[1].isdigit():
                            raise InvalidDatabaseShowFlags(
                                f"{units_name[1]} format in start range {ind} of --{arg} is invalid, check again.")
                        else:
                            form_time += f"-{start_split[1]}"
                    except IndexError: # This means there is only one unit, so skip.
                        pass
                    # Check for the third unit.
                    try:
                        if len(start_split[2]) != units[2] or not start_split[2].isdigit():
                            raise InvalidDatabaseShowFlags(
                                f"{units_name[2]} format in start range {ind} of --{arg} is invalid, check again.")
                        else:
                            form_time +=  f"-{start_split[2]}"
                    except IndexError:
                        pass
                    # We have to format form_time first if it is not a full date, wait.
                    if arg == "yearmonth":
                        form_time += "-01" # We assume the start of the month.
                    elif arg == "monthday":
                        form_time = f"{date.today().year}-" + form_time
                    elif arg == "year":
                        form_time += "-01-01"
                    elif arg == "month":
                        form_time = f"{date.today().year}-" + form_time + "-01"
                    elif arg == "day":
                        form_time = f"{date.today().year}-{date.today().strftime('%m')}-" + form_time               
                    try: # Test the start date range.
                        datetime.strptime(form_time, "%Y-%m-%d")
                        query += f"'{form_time}' AND " # Append the start range.
                    except ValueError:
                        raise InvalidDate(f"Start date range {form_time} (index: {ind}) of --{arg} is invalid.")
                    form_time = "" # Reset it.

                    # ------------------------- Check the end range.
                    end_split = end.split("-")
                    if len(end_split) != length:
                        raise InvalidDatabaseShowFlags(
                            f"Dash usage in end range {ind} of --{arg} is invalid or you have too little/much units, check again.")  
                    # Check for the first unit.
                    if len(end_split[0]) != units[0] or not end_split[0].isdigit():
                        raise InvalidDatabaseShowFlags(
                            f"{units_name[0]} format in end range {ind} of --{arg} is invalid, check again.")
                    else:
                        form_time +=  f"{end_split[0]}"
                    # Check for the second unit.
                    try:
                        if len(end_split[1]) != units[1] or not end_split[1].isdigit():
                            raise InvalidDatabaseShowFlags(
                                f"{units_name[1]} format in end range {ind} of --{arg} is invalid, check again.")
                        else:
                            form_time +=  f"-{end_split[1]}"
                    except IndexError:
                        pass
                    # Check for the third unit.
                    try:
                        if len(end_split[2]) != units[2] or not end_split[2].isdigit():
                            raise InvalidDatabaseShowFlags(
                                f"{units_name[2]} format in end range {ind} of --{arg} is invalid, check again.")
                        else:
                            form_time +=  f"-{end_split[2]}"
                    except IndexError:
                        pass
                    # We have to format form_time first if it is not a full date, wait.
                    if arg == "yearmonth":
                        target_year = int(end_split[0])
                        target_month = int(end_split[1])
                        form_time += f"-{calendar.monthrange(target_year, target_month)[1]}" # We assume the start of the month.
                    elif arg == "monthday":
                        form_time = f"{date.today().year}-" + form_time
                    elif arg == "year":
                        form_time += f"-12-{calendar.monthrange(int(end_split[0]), 12)[1]}"
                    elif arg == "month":
                        target_year = date.today().year
                        target_month = int(end_split[0])
                        form_time = f"{target_year}-" + form_time + "-" + str(calendar.monthrange(target_year, target_month)[1])
                    elif arg == "day":
                        form_time = f"{date.today().year}-{date.today().strftime('%m')}-" + form_time
                    time_rang = True # This marks that one range has been parsed.
                    try: # Test the end range date.
                        datetime.strptime(form_time, "%Y-%m-%d")
                        query += f"'{form_time}')\n" # Append the end range.
                    except ValueError:
                        raise InvalidDate(f"End date range {form_time} (index: {ind}) of --{arg} is invalid.")
                    form_time = "" # Reset.
                    # Add it to the query.
                    fquery += query
                    dquery += query
                    query = "" # Reset query.
        # ======================== VALUE FLAGS
        elif arg in ("nvalue", "tvalue", "id", "admin"):
            if arg == "nvalue": 
                edited_arg = "value"
            elif arg == "tvalue":
                edited_arg = "total"
            else:
                edited_arg = arg
            ranges: list[str] = value.split(",")
            first_range: bool = False
            for ind, r in enumerate(ranges):
                if r[0] == "!":
                    r = r[1:]
                    exempt = True
                else:
                    exempt = False
                    no_nonexempt = False
                    single = False # Single is only set to false if we found a non-exempt entry (because if exempt it is injected later)
                if not first_range:
                    if exempt:
                        query += "NOT ("
                    else:
                        query += "("
                    first_range = True
                else:
                    if exempt:
                        query += "      OR NOT ("
                    else:
                        query += "      OR ("
                equivalence: list[str] = re.split(r'(?<![<=>])=(?![<=>])', r)
                equivalence = [item for item in equivalence if item] # Purge from empty strings.
                if len(equivalence) == 2: # Simple equivalence statements.
                    if equivalence[0] != "x":
                        raise InvalidValueFlagsFormat(f"Equivalence statement index {ind} of --{arg} must be x=[number]")
                    try:
                        number = float(equivalence[1])
                    except ValueError:
                        raise InvalidValueFlagsFormat(f"Equivalence statement index {ind} of --{arg} must be x=[number]")
                    query += f"{edited_arg} = {number}"
                elif len(equivalence) == 1: # Non-equivalence, eg 500<x<900
                    tokens = re.split(r"(>=|<=|>|<|x)", r)
                    tokens = [item for item in tokens if item] # Purge from empty strings.
                    if len(tokens) not in (5, 3):
                        raise InvalidValueFlagsFormat(
                            f"Non-equivalence statement index {ind} of --{arg} must be [number][operator]x[operator][number], [number]x[operator], or [operator]x[number]")
                    operator_facing_left: bool  = False # This means literally 1000>x>500 or 1000>=x>500 or 1000>x>=500 or 1000>=x>=500 is left.
                    first_has_found:      bool  = False  # This means the first operator that indicates facing has been found.
                    first_number:         float = 0     # First number.
                    second_number:        float = 0     # Second number
                    first_number_modifie: bool  = False # Indicating first number has been found, so the program stores the num token to the 2nd.
                    second_number_modifi: bool  = False # Indicating second number has been modified.
                    x_found:              bool  = False # Indicating x has been found.
                    for token_ind, token in enumerate(tokens):
                        if token in (">=", "<=", "<", ">"):
                            if token_ind not in (1, 3):
                                raise InvalidValueFlagsFormat(
                            f"Non-equivalence statement index {ind} of --{arg} must be [number][operator]x[operator][number], [number]x[operator], or [operator]x[number]")
                            if not first_has_found:
                                if token in (">", ">="):
                                    operator_facing_left = True
                                first_has_found = True
                            else: # This is for second operator.
                                second_has_found = True
                                if operator_facing_left:
                                    if token in ("<", "<="):
                                        raise InvalidValueFlagsFormat(
                                        f"Non-equivalence statement index {ind} of --{arg} must have its operators aligned.")
                                else:
                                    if token in (">", ">="):
                                        raise InvalidValueFlagsFormat(
                                        f"Non-equivalence statement index {ind} of --{arg} must have its operators aligned.")    
                        elif token == "x":
                            x_found = True
                            token = f"{edited_arg} AND {edited_arg}"
                        else:
                            if token_ind not in (0, 4): # Kills any numbers that are not placed in index 0 or 4
                                if token_ind == 2 and len(tokens) == 3 and x_found: # So forms like x operator number is valid
                                    pass
                                else:
                                    raise InvalidValueFlagsFormat(
                            f"Non-equivalence statement index {ind} of --{arg} must be [number][operator]x[operator][number], [number]x[operator], or [operator]x[number]")   
                            try:
                                token = token.replace("H", "00").replace("h", "00").replace("K", "000").replace("k", "000")
                                numbe  = float(token)
                                if first_number_modifie:
                                    second_number = numbe
                                    second_number_modifi = True
                                else:
                                    first_number = numbe
                                    first_number_modifie = True
                            except ValueError:
                                raise InvalidValueFlagsFormat(
                            f"Non-equivalence statement index {ind} of --{arg} must be [number][operator]x[operator][number], [number]x[operator], or [operator]x[number]")                      
                        if token_ind == 0:
                            query += token
                        else:
                            query += f" {token}"
                    if second_number_modifi:
                        if operator_facing_left:
                            if first_number < second_number:
                                raise InvalidValueFlagsFormat(
                                f"Non-equivalence statement index {ind} of --{arg} min and max are misplaced.") 
                        else:
                            if first_number > second_number:
                                raise InvalidValueFlagsFormat(
                                f"Non-equivalence statement index {ind} of --{arg} min and max are misplaced.") 
                else:
                    raise InvalidValueFlagsFormat(f"Equivalence statement index {ind} of --{arg} can only contain one equal sign.")
                query = query + ")\n"
            dquery += query
            fquery += query
            query = ""
        # ======================== OTHER FLAGS
        elif arg in ("party", "category", "active", "passive", "pathway", "wallet"):
            data: list[str] = value.split(",")
            # 1. Grab the items (stripping the '!') and store them in another variable
            exempt_other[arg] = [item[1:] for item in data if item.startswith("!")]
            # 2. Re-assign the original list to only keep items that DO NOT start with '!'
            data = [item for item in data if not item.startswith("!")]
            if data == []:
                fquery = fquery[:-9] # remove the indentation since well... there is no data!
                dquery = dquery[:-9]
                continue
            else:
                no_nonexempt = False
                single = False # Single is only set to false if we found a non-exempt entry (because if exempt it is injected later)
            query += f"({arg} IN ("
            dquery += f"({arg} IN ("
            query += ", ".join(["?"] * len(data)) + "))\n"
            fquery += query
            query = ""
            dquery += ", ".join(f"'{item}'" for item in data) + "))\n"
            parameters.extend(data)
        else:
            raise InvalidGetArg("Internal error: Invalid argument for get()")

    # Add those that are exempted, only for other flags.
    for arg, data in exempt_other.items():
            if data == []:
                continue
            if no_nonexempt: # indicating there are no non-exempt queries
                fquery = fquery[:33]
                dquery = dquery[:33]
                query += f"         ({arg} NOT IN ("
                dquery += f"        ({arg} NOT IN ("
            else:
                query += f"    AND ({arg} NOT IN ("
                dquery += f"     AND ({arg} NOT IN ("
            query += ", ".join(["?"] * len(data)) + "))\n"
            fquery += query
            query = ""
            dquery += ", ".join(f"'{item}'" for item in data) + "))\n"
            parameters.extend(data)

    # Execute the query.
    while True:
        if verbose:
            print(": Here is the SQL statement that will be executed (actual SQL is parameterized and sanitizied)\n")
            print(dquery)
            confirm = input ("> Proceed? (Y/N) ")
        else:
            confirm = "y" # Auto-confirm.
        if confirm.strip().lower() in ("yes", "y"):
            # Reading configurations.
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
            print(": Connecting to the database...")
            if not os.path.exists(db_path):
                raise InvalidDatabaseError("The database does not exist.")
            try:
                conn: Connection = sqlite3.connect(db_path)
                if panda: # Directly write the rows the spreadsheet file.
                    print(f": Exporting database rows to spreadsheet {panda}...")
                    if os.path.exists(panda):
                        while True:
                            ask = input("> The spreadsheet file has already existed. Are you sure to overwrite? (Y/N) ")
                            if ask.lower() in ('y', 'yes'):
                                print(": Overwriting the old spreadsheet file...")
                                break
                            elif ask.lower() in ('n', 'no'):
                                print(": Cancelling...")
                                sys.exit(0)
                            else:
                                print(": Invalid response! Repeating...")
                    df: pd.DataFrame = pd.read_sql_query(fquery, conn, params=parameters)
                    df.to_excel(panda, sheet_name='sheet1', index=False)
                    return []
                else: # Obtain the data, just return.
                    print(": Fetching database rows...")
                    conn.row_factory = sqlite3.Row
                    cursor: Cursor   = conn.cursor()
                    cursor.execute(fquery, parameters)
                    rows = cursor.fetchall()
                conn.close()
                break
            except sqlite3.OperationalError:
                raise InvalidDatabaseError(": Invalid database, table 'transactions' does not exist, is invalid, or there is a bug.")
            except KeyboardInterrupt:
                print("\n: Canceling...")    
                sys.exit(0)       
        elif confirm.strip().lower() in ("no", "n"):
            print(": Skipping...")
            sys.exit(0)
        else:
            print(": Invalid response! Repeating...")
    return rows
