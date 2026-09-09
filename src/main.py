'''
    main

    Main entrypoint.
'''

import sys
import argparse

from src.setup import setup
from src.sheet import sheet
from src.database import database
from src.graph import graph
from src.control import control

from src.error import InvalidCLIArgument

class Main:
    '''Main file.'''
    def __init__(self):
        self.__parse() # Parse CLI arguments.
        try:
            self.__run()
        except KeyboardInterrupt:
            print("\n: Receiving keyboard interrupt...")
            sys.exit(0)

    def __parse(self):
        '''Parse arguments'''
        # Setup parser.
        self.__parser = argparse.ArgumentParser()
        self.__subparser_mgr = self.__parser.add_subparsers(dest="command", required=True)
        
        # python3 run.py setup (flags)
        self.__subparser_setup = self.__subparser_mgr.add_parser("setup", help="Setup the config and the database.")
        self.__subparser_setup.add_argument(
            "-db", "--db", "-database", "--database", type=str, default="database.db",
            help="Path of the DB file.")
        self.__subparser_setup.add_argument(
            "--archive", "-a", "--a", "-archive", type=str, default="archive.db",
            help="Path of the DB archive file.")
        self.__subparser_setup.add_argument("--nobackup", "-nobackup", "--nb", "-nb", action="store_true",
                                               help="Do not backup the DB file if it has existed. Default is false.")
        self.__subparser_setup.add_argument(
            "--limit", "-l", "--l", "-limit", type=int, default=50000,
            help="Limit per day.")
        self.__subparser_setup.add_argument(
            "--save", "-s", "--s", "-s", type=int, default=0.2,
            help="Save how much per day.")
                
        # python3 run.py sheet [choice: import, export] [sheet_path] (flags)
        self.__subparser_sheet = self.__subparser_mgr.add_parser("sheet",
            help="Utilize spreadsheets for data management.")
        self.__subparser_sheet.add_argument("choice", type=str,
help="import and export. For import, the only flag is --overwrite, the rest of the flags is for export, and is similar to database show flags.")
        self.__subparser_sheet.add_argument("sheet", type=str, help="Path of the sheet file.")

        self.__subparser_sheet.add_argument("--date", "-date", "-fd", "--fd", type=str,
            help="For export - Time range: Pass date range. Format can be YYYY-MM-DD:YYYY-MM-DD. Use two digits for months & days e.g. 1999-12-01:2005-05-03. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_sheet.add_argument("--yearmonth", "-yearmonth", "--ym", "-ym", type=str,
            help="For export - Time range: Pass year-month range. Format can be YYYY-MM:YYYY-MM. Use two digits for months e.g. 2008-12:2012-01. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_sheet.add_argument("--monthday", "-monthday", "--md", "-md", type=str,
            help="For export - Time range: Pass month-day range within this year. Format is MM-DD:MM-DD. Use two digits e.g. 10-01:06-30. Use , for multiple ranges. Hour is assumed to be midnight.")        
        self.__subparser_sheet.add_argument("--year", "-year", "--y", "-y", type=str,
            help="For export - Time range: Pass year range. Format is YYYY:YYYY. Use two digits e.g. 2008 or 1999. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_sheet.add_argument("--month", "-month", "--m", "-m", type=str,
            help="For export - Time range: Pass month range within this year. Format is MM:MM. Use two digits e.g. 01 or 12. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_sheet.add_argument("--day", "-day", "--d", "-d", type=str,
            help="For export - Time range: Pass day range within this day. Format is DD:DD. Use two digits e.g. 08 or 27. Use , for multiple ranges. Hour is assumed to be midnight.")

        # value
        self.__subparser_sheet.add_argument("--id", "-id", type=str,
help="For export - Filter based on the id. Use <, <=, >, >=, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_sheet.add_argument("--nvalue", "-nvalue", "--nv", "-nv", type=str,
help="For export - Filter based on nominal value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred., comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_sheet.add_argument("--tvalue", "-tvalue", "--tv", "-tv", type=str,
help="For export - Filter based on total value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_sheet.add_argument("--admin", "-admin", "--ad", "-ad", type=str,
help="For export - Filter based on the value of admin fee. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")

        # others
        self.__subparser_sheet.add_argument("--party", "-party", "--p", "-p", type=str,
            help="For export - Filter based on parties. Format: x,y,z (without space)")
        self.__subparser_sheet.add_argument("--category", "-category", "--c", "-c", type=str,
            help="For export - Filter based on categories. Format: x,y,z (without space)")
        self.__subparser_sheet.add_argument("--active", "-active", "--as", "-as", type=str,
            help="For export - Filter based on the active side. Format: x,y,z (without space)")
        self.__subparser_sheet.add_argument("--passive", "-passive", "--ps", "-ps", type=str,
            help="For export - Filter based on the passive side. Format: x,y,z (without space)")
        self.__subparser_sheet.add_argument("--pathway", "-pathway", "--pw", "-pw", type=str,
            help="Filter based on pathway. Format: x,y,z (without space)")
        self.__subparser_sheet.add_argument("--wallet", "-wallet", "--w", "-w", type=str,
            help="For export - Filter based on wallet. Format: x,y,z (without space)")

        self.__subparser_sheet.add_argument("--verbose", "-verbose", "--v", "-v", action="store_true",
                                               help="For export - Display SQL before execution.")
        self.__subparser_sheet.add_argument("--overwrite", "-overwrite", "--o", "-o", action="store_true",
                                               help="For import - Overwrite rather than append.")
        self.__subparser_sheet.add_argument("--nobackup", "-nobackup", "--nb", "-nb", action="store_true",
                                               help="Do not backup the file. Default is false.")

        # python3 run.py version
        self.__subparser_version = self.__subparser_mgr.add_parser("version", help="Show version.")
        self.__subparser_version.add_argument("--license", "-license", "-l", "-l", action="store_true", help="Show license.")

        # python3 run.py database [choice: reset, show] [show: reset]
        self.__subparser_database = self.__subparser_mgr.add_parser("database", help="Manage database.")
        self.__subparser_database.add_argument("choice", type=str,
            help="reset or show. When showing, if you do not use flags below the default is all transactions. --summary is only for show. Use ! at the start of the range for exclusion.")
        
        # Who hates awesome filtration system.
    
        # time flags, only one can be used.
        self.__subparser_database.add_argument("--date", "-date", "-fd", "--fd", type=str,
            help="Time range: Pass date range. Format can be YYYY-MM-DD:YYYY-MM-DD. Use two digits for months & days e.g. 1999-12-01:2005-05-03. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_database.add_argument("--yearmonth", "-yearmonth", "--ym", "-ym", type=str,
            help="Time range: Pass year-month range. Format can be YYYY-MM:YYYY-MM. Use two digits for months e.g. 2008-12:2012-01. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_database.add_argument("--monthday", "-monthday", "--md", "-md", type=str,
            help="Time range: Pass month-day range within this year. Format is MM-DD:MM-DD. Use two digits e.g. 10-01:06-30. Use , for multiple ranges. Hour is assumed to be midnight.")        
        self.__subparser_database.add_argument("--year", "-year", "--y", "-y", type=str,
            help="Time range: Pass year range. Format is YYYY:YYYY. Use two digits e.g. 2008 or 1999. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_database.add_argument("--month", "-month", "--m", "-m", type=str,
            help="Time range: Pass month range within this year. Format is MM:MM. Use two digits e.g. 01 or 12. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_database.add_argument("--day", "-day", "--d", "-d", type=str,
            help="Time range: Pass day range within this day. Format is DD:DD. Use two digits e.g. 08 or 27. Use , for multiple ranges. Hour is assumed to be midnight.")

        # value
        self.__subparser_database.add_argument("--id", "-id", type=str,
help="Filter based on the id. Use <, <=, >, >=, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_database.add_argument("--nvalue", "-nvalue", "--nv", "-nv", type=str,
help="Filter based on nominal value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred., comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_database.add_argument("--tvalue", "-tvalue", "--tv", "-tv", type=str,
help="Filter based on total value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_database.add_argument("--admin", "-admin", "--ad", "-ad", type=str,
help="Filter based on the value of admin fee. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")

        # others
        self.__subparser_database.add_argument("--party", "-party", "--p", "-p", type=str,
            help="Filter based on parties. Format: x,y,z (without space)")
        self.__subparser_database.add_argument("--category", "-category", "--c", "-c", type=str,
            help="Filter based on categories. Format: x,y,z (without space)")
        self.__subparser_database.add_argument("--active", "-active", "--as", "-as", type=str,
            help="For export - Filter based on the active side. Format: x,y,z (without space)")
        self.__subparser_database.add_argument("--passive", "-passive", "--ps", "-ps", type=str,
            help="For export - Filter based on the passive side. Format: x,y,z (without space)")
        self.__subparser_database.add_argument("--pathway", "-pathway", "--pw", "-pw", type=str,
            help="Filter based on pathway. Format: x,y,z (without space)")
        self.__subparser_database.add_argument("--wallet", "-wallet", "--w", "-w", type=str,
            help="Filter based on wallet. Format: x,y,z (without space)")

        self.__subparser_database.add_argument("--verbose", "-verbose", "--v", "-v", action="store_true",
                                               help="Display SQL before execution.")
        self.__subparser_database.add_argument("--nobackup", "-nobackup", "--nb", "-nb", action="store_true",
                                               help="Do not backup the file. Default is false.")
        self.__subparser_database.add_argument("--summary", "-summary", "--sum", "-sum", action="store_true",
                                               help="Only show the summary (minus the table).")

        # python3 run.py control [show, graph] (flags)
        self.__subparser_control = self.__subparser_mgr.add_parser("control",
            help="Utilize matplotlib and tabulate to check your controls.")
        self.__subparser_control.add_argument("choice", type=str, help="Either chart based on time, or print it on the CLI via tabulate. --show is only for control graph")

        self.__subparser_control.add_argument("--date", "-date", "-fd", "--fd", type=str,
            help="For export - Time range: Pass date range. Format can be YYYY-MM-DD:YYYY-MM-DD. Use two digits for months & days e.g. 1999-12-01:2005-05-03. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_control.add_argument("--yearmonth", "-yearmonth", "--ym", "-ym", type=str,
            help="For export - Time range: Pass year-month range. Format can be YYYY-MM:YYYY-MM. Use two digits for months e.g. 2008-12:2012-01. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_control.add_argument("--monthday", "-monthday", "--md", "-md", type=str,
            help="For export - Time range: Pass month-day range within this year. Format is MM-DD:MM-DD. Use two digits e.g. 10-01:06-30. Use , for multiple ranges. Hour is assumed to be midnight.")        
        self.__subparser_control.add_argument("--year", "-year", "--y", "-y", type=str,
            help="For export - Time range: Pass year range. Format is YYYY:YYYY. Use two digits e.g. 2008 or 1999. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_control.add_argument("--month", "-month", "--m", "-m", type=str,
            help="For export - Time range: Pass month range within this year. Format is MM:MM. Use two digits e.g. 01 or 12. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_control.add_argument("--day", "-day", "--d", "-d", type=str,
            help="For export - Time range: Pass day range within this day. Format is DD:DD. Use two digits e.g. 08 or 27. Use , for multiple ranges. Hour is assumed to be midnight.")

        # value
        self.__subparser_control.add_argument("--id", "-id", type=str,
help="For export - Filter based on the id. Use <, <=, >, >=, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_control.add_argument("--nvalue", "-nvalue", "--nv", "-nv", type=str,
help="For export - Filter based on nominal value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred., comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_control.add_argument("--tvalue", "-tvalue", "--tv", "-tv", type=str,
help="For export - Filter based on total value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_control.add_argument("--admin", "-admin", "--ad", "-ad", type=str,
help="For export - Filter based on the value of admin fee. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")

        # others
        self.__subparser_control.add_argument("--party", "-party", "--p", "-p", type=str,
            help="For export - Filter based on parties. Format: x,y,z (without space)")
        self.__subparser_control.add_argument("--category", "-category", "--c", "-c", type=str,
            help="For export - Filter based on categories. Format: x,y,z (without space)")
        self.__subparser_control.add_argument("--active", "-active", "--as", "-as", type=str,
            help="For export - Filter based on the active side. Format: x,y,z (without space)")
        self.__subparser_control.add_argument("--passive", "-passive", "--ps", "-ps", type=str,
            help="For export - Filter based on the passive side. Format: x,y,z (without space)")
        self.__subparser_control.add_argument("--pathway", "-pathway", "--pw", "-pw", type=str,
            help="Filter based on pathway. Format: x,y,z (without space)")
        self.__subparser_control.add_argument("--wallet", "-wallet", "--w", "-w", type=str,
            help="For export - Filter based on wallet. Format: x,y,z (without space)")

        self.__subparser_control.add_argument("--verbose", "-verbose", "--v", "-v", action="store_true",
                                               help="Display SQL before execution.")
        self.__subparser_control.add_argument("--summary", "-summary", "--sum", "-sum", action="store_true",
                                               help="Only show the summary (minus the table) at the CLI.")
        self.__subparser_control.add_argument("--show", "-show", "--s", "-s", type=str, default="total,delta,saved",
                                               help="Shows what graph. You can choose one, two, or three of total, delta, and saved (no space, seperate via comma)")

        # python3 run.py graph [choice: time, party, category, active, passive, wallet] (flags)
        self.__subparser_graph = self.__subparser_mgr.add_parser("graph",
            help="Utilize matplotlib to plot and draw a chart.")
        self.__subparser_graph.add_argument("choice", type=str, help="pie chart (party, category, active, passive, and wallet) or line chart (time). You can use filtration flags.")

        self.__subparser_graph.add_argument("--date", "-date", "-fd", "--fd", type=str,
            help="For export - Time range: Pass date range. Format can be YYYY-MM-DD:YYYY-MM-DD. Use two digits for months & days e.g. 1999-12-01:2005-05-03. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_graph.add_argument("--yearmonth", "-yearmonth", "--ym", "-ym", type=str,
            help="For export - Time range: Pass year-month range. Format can be YYYY-MM:YYYY-MM. Use two digits for months e.g. 2008-12:2012-01. Use , for multiple ranges. Hour is assumed to be midnight.")
        self.__subparser_graph.add_argument("--monthday", "-monthday", "--md", "-md", type=str,
            help="For export - Time range: Pass month-day range within this year. Format is MM-DD:MM-DD. Use two digits e.g. 10-01:06-30. Use , for multiple ranges. Hour is assumed to be midnight.")        
        self.__subparser_graph.add_argument("--year", "-year", "--y", "-y", type=str,
            help="For export - Time range: Pass year range. Format is YYYY:YYYY. Use two digits e.g. 2008 or 1999. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_graph.add_argument("--month", "-month", "--m", "-m", type=str,
            help="For export - Time range: Pass month range within this year. Format is MM:MM. Use two digits e.g. 01 or 12. Use , for multiple ranges. Hour is assumed to be midnight.") 
        self.__subparser_graph.add_argument("--day", "-day", "--d", "-d", type=str,
            help="For export - Time range: Pass day range within this day. Format is DD:DD. Use two digits e.g. 08 or 27. Use , for multiple ranges. Hour is assumed to be midnight.")

        # value
        self.__subparser_graph.add_argument("--id", "-id", type=str,
help="For export - Filter based on the id. Use <, <=, >, >=, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_graph.add_argument("--nvalue", "-nvalue", "--nv", "-nv", type=str,
help="For export - Filter based on nominal value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred., comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_graph.add_argument("--tvalue", "-tvalue", "--tv", "-tv", type=str,
help="For export - Filter based on total value of the transactions. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")
        self.__subparser_graph.add_argument("--admin", "-admin", "--ad", "-ad", type=str,
help="For export - Filter based on the value of admin fee. Use <, <=, >, >=, =, K or k for thousand, H or h for hundred, comma for seperator of ranges, and x for the var. Example: x<500, x<600,x>500")

        # others
        self.__subparser_graph.add_argument("--party", "-party", "--p", "-p", type=str,
            help="For export - Filter based on parties. Format: x,y,z (without space)")
        self.__subparser_graph.add_argument("--category", "-category", "--c", "-c", type=str,
            help="For export - Filter based on categories. Format: x,y,z (without space)")
        self.__subparser_graph.add_argument("--active", "-active", "--as", "-as", type=str,
            help="For export - Filter based on the active side. Format: x,y,z (without space)")
        self.__subparser_graph.add_argument("--passive", "-passive", "--ps", "-ps", type=str,
            help="For export - Filter based on the passive side. Format: x,y,z (without space)")
        self.__subparser_graph.add_argument("--pathway", "-pathway", "--pw", "-pw", type=str,
            help="Filter based on pathway. Format: x,y,z (without space)")
        self.__subparser_graph.add_argument("--wallet", "-wallet", "--w", "-w", type=str,
            help="For export - Filter based on wallet. Format: x,y,z (without space)")

        self.__subparser_graph.add_argument("--verbose", "-verbose", "--v", "-v", action="store_true",
                                               help="Display SQL before execution.")
        self.__subparser_graph.add_argument("--noadmin", "-noadmin", "--na", "-na", action="store_true",
                                               help="Do not include admin fees.")
        self.__subparser_graph.add_argument("--adminfee", "-adminfee", "--af", "-af", action="store_true",
                                               help="Show seperate graph of admin fees.")

        # Finalize parser.
        self.__args = self.__parser.parse_args()

    def __run(self):
        '''Run the program.'''
        self.__OPTION = self.__args.command
        if self.__OPTION == "setup": # python3 run.py setup
            setup(self.__args.db, self.__args.archive, self.__args.nobackup, self.__args.limit, self.__args.save)
        elif self.__OPTION == "sheet": # python3 run.py sheet
            sheet(self.__args.choice, self.__args.sheet, self.__args.verbose,
                  self.__args.overwrite, self.__args.nobackup, {
                "date"      : self.__args.date,
                "yearmonth" : self.__args.yearmonth,
                "monthday"  : self.__args.monthday,
                "year"      : self.__args.year,
                "month"     : self.__args.month,
                "day"       : self.__args.day,
                "id"        : self.__args.id,
                "party"     : self.__args.party,
                "category"  : self.__args.category,
                "active"    : self.__args.active,
                "passive"   : self.__args.passive,
                "pathway"   : self.__args.pathway,
                "wallet"    : self.__args.wallet,
                "nvalue"    : self.__args.nvalue,
                "tvalue"    : self.__args.tvalue,
                "admin"     : self.__args.admin
            })
        elif self.__OPTION == "database": # python3 run.py database
            database(self.__args.choice, self.__args.verbose, self.__args.nobackup, self.__args.summary, {
                "date"      : self.__args.date,
                "yearmonth" : self.__args.yearmonth,
                "monthday"  : self.__args.monthday,
                "year"      : self.__args.year,
                "month"     : self.__args.month,
                "day"       : self.__args.day,
                "id"        : self.__args.id,
                "party"     : self.__args.party,
                "category"  : self.__args.category,
                "active"    : self.__args.active,
                "passive"   : self.__args.passive,
                "pathway"   : self.__args.pathway,
                "wallet"    : self.__args.wallet,
                "nvalue"    : self.__args.nvalue,
                "tvalue"    : self.__args.tvalue,
                "admin"     : self.__args.admin
            })
        elif self.__OPTION == "control": # python3 run.py database
            control(self.__args.choice, self.__args.verbose, self.__args.summary, self.__args.show, {
                "date"      : self.__args.date,
                "yearmonth" : self.__args.yearmonth,
                "monthday"  : self.__args.monthday,
                "year"      : self.__args.year,
                "month"     : self.__args.month,
                "day"       : self.__args.day,
                "id"        : self.__args.id,
                "party"     : self.__args.party,
                "category"  : self.__args.category,
                "active"    : self.__args.active,
                "passive"   : self.__args.passive,
                "pathway"   : self.__args.pathway,
                "wallet"    : self.__args.wallet,
                "nvalue"    : self.__args.nvalue,
                "tvalue"    : self.__args.tvalue,
                "admin"     : self.__args.admin
            })
        elif self.__OPTION == "graph": # python3 run.py database
            graph(self.__args.choice, self.__args.verbose, self.__args.noadmin, self.__args.adminfee, {
                "date"      : self.__args.date,
                "yearmonth" : self.__args.yearmonth,
                "monthday"  : self.__args.monthday,
                "year"      : self.__args.year,
                "month"     : self.__args.month,
                "day"       : self.__args.day,
                "id"        : self.__args.id,
                "party"     : self.__args.party,
                "category"  : self.__args.category,
                "active"    : self.__args.active,
                "passive"   : self.__args.passive,
                "pathway"   : self.__args.pathway,
                "wallet"    : self.__args.wallet,
                "nvalue"    : self.__args.nvalue,
                "tvalue"    : self.__args.tvalue,
                "admin"     : self.__args.admin
            })
        elif self.__OPTION == "version":
            if self.__args.license:
                print("Licensed in MIT License.")
            else:
                print("Shitty finance calculator v1.0, for budget tracking and filtering.")
        else:
            raise InvalidCLIArgument(f"Invalid option {self.__OPTION}")
