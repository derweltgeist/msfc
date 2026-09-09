import sys
import itertools

import pandas as pd
import tomlkit
from tomlkit.exceptions import ParseError
from tabulate import tabulate
import matplotlib.pyplot as plt

from src.get import get
from src.other import rupiah
from src.error import InvalidCLIArgument, InvalidControlGraph

def control(choice: str, verbose: bool,  summary: bool, graph: str, range: dict[str, str]) -> None:
    '''python3 run.py database ...'''
    # Get the configuration.
    print(": Loading configuration...")
    try:
        with open("config.toml", "r", encoding="utf-8") as f:
            try:
                config       = tomlkit.parse(f.read())
                limit: float = float(str(config["limit"]))
                save: float  = float(str(config["save"]))
            except ParseError:
                print(": Config file 'config.toml' contains invalid data.")
                sys.exit(1)
    except FileNotFoundError:
        print(": Config file 'config.toml' is missing in the root directory.")
        sys.exit(1)
    # Get the data, aggregate by days.
    print(": Loading database...")
    result = get(range, verbose)
    df     = pd.DataFrame([dict(row) for row in result])
    df_agg = df.groupby("date", as_index=False)["total"].sum() # We only get the negative transactions.
    boundary: float = - limit * (1 - save)
    df_agg["exceed"] = df_agg["total"] < boundary
    df_agg["delta"] = df_agg["total"] - boundary
    df_agg["saved"] = (df_agg["total"] - boundary).clip(lower=0)
    if choice == "graph": # python3 run.py control graph
        var = tuple(graph.strip().split(','))
        items = set(["total", "delta", "saved"])
        if not (set(var).issubset(items) and len(var) == len(set(var))):
            raise InvalidControlGraph(
    "You can only choose any or two or three of total, delta, and saved. Make sure to include no space and seperate by comma.")
        print("")
        print(f"Total exceeded : {df_agg['exceed'].sum()} transaction(s)")
        print(f"Total delta    : {rupiah(df_agg['delta'].sum())}")
        print(f"Total saved    : {rupiah(df_agg['saved'].sum())}")
        print("")
        # Plot total, difference (delta), and saved against date
        df_agg.plot(
            x="date",
            y=graph.strip().split(','),
            kind="line",
            figsize=(10, 5)
        )
        plt.title("Control data of Your Transactions")
        plt.xlabel("Date")
        plt.ylabel("Amount (Rp)")
        plt.xticks(rotation=45, ha="right")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(["Total", "Delta", "Saved"])
        plt.tight_layout()
        plt.show()
    elif choice == "show": # python3 run.py control show
        if not summary:
            print("")
            print(
                tabulate(
                    df_agg, headers="keys", tablefmt="fancy_grid", showindex=False
                )
            )
        print("")
        print(f"Total exceeded : {df_agg['exceed'].sum()} transaction(s)")
        print(f"Total delta    : {rupiah(df_agg['delta'].sum())}")
        print(f"Total saved    : {rupiah(df_agg['saved'].sum())}")
        print("")
    else:
        raise InvalidCLIArgument(
            "Invalid CLI subcommand for command database: only reset and show are valid.")
    print(": Finishing task...")
