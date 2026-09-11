import sys

import numpy as np
import pandas as pd
import tomlkit
from tomlkit.exceptions import ParseError
from tabulate import tabulate
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from src.get import get
from src.other import rupiah
from src.error import InvalidCLIArgument, InvalidControlGraph

def control(choice: str, verbose: bool,  summary: bool, graph: str, cum: bool, range: dict[str, str]) -> None:
    '''python3 run.py database ...'''
    # Get the configuration.
    print(": Loading configuration...")
    try:
        with open("config.toml", "r", encoding="utf-8") as f:
            try:
                config       = tomlkit.parse(f.read())
                limit: float = float(str(config["limit"]))
                save: float  = float(str(config["cut"]))
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
    boundary: float = limit * (1 - save)
    df_agg["exceed"] = df_agg["total"] < - limit    # Indicates whether you have exceeded the limit.
    df_agg["saved"]  = df_agg["total"] > - boundary # Indicates whether your spending is <= boundary.
    # 1. Define conditions
    conds = [
        df_agg["total"] > 0,
        df_agg["total"] < 0
    ]
    # 2. Define corresponding outputs for 'delta'
    delta_choices = [
        df_agg["total"] - limit,
        limit - abs(df_agg["total"])
    ]
    # 3. Define corresponding outputs for 'extra'
    extra_choices = [
        df_agg["total"],
        (df_agg["total"] - limit).clip(lower=0)
    ]
    # 4. Assign vectorized results (default=0 handles the 'else' case)
    df_agg["delta"] = np.select(conds, delta_choices, default=0)
    df_agg["extra"] = np.select(conds, extra_choices, default=0)
    if choice == "graph": # python3 run.py control graph
        var = tuple(graph.strip().split(','))
        items = set(["total", "delta", "extra"])
        if not (set(var).issubset(items) and len(var) == len(set(var))):
            raise InvalidControlGraph(
    "You can only choose any or two or three of total, delta, and extra. Make sure to include no space and seperate by comma.")
        print("")
        print(f"Total exceeded : {df_agg['exceed'].sum()} transaction(s)")
        print(f"Total saved    : {df_agg['saved'].sum()} transaction(s)")
        print(f"Total delta    : {rupiah(df_agg['delta'].sum())}")
        print(f"Total extra    : {rupiah(df_agg['extra'].sum())}")
        print("")
        def rupiah_formatter(x: float, pos) -> str:
            if x == 0:
                return "Rp0"
            is_neg = x < 0
            val = abs(x)
            if val >= 1e12:
                formatted = f"Rp{val * 1e-12:.1f} T"
            elif val >= 1e9:
                formatted = f"Rp{val * 1e-9:.1f} B"
            elif val >= 1e6:
                formatted = f"Rp{val * 1e-6:.1f} M"
            elif val >= 1e3:
                formatted = f"Rp{val * 1e-3:.0f} K"
            else:
                formatted = f"Rp{val:.0f}"
            return f"({formatted})" if is_neg else formatted
        ax = plt.subplots(figsize=(10, 5), num="My Shitty Finance Calculator")[1]
        ax.yaxis.set_major_formatter(FuncFormatter(rupiah_formatter))
        if cum:
            df_agg['total'] = df_agg['total'].cumsum()
            df_agg['delta'] = df_agg['delta'].cumsum()
            df_agg['extra'] = df_agg['extra'].cumsum()
        # Plot total, difference (delta), and saved against date
        df_agg.plot(
            x="date",
            y=graph.strip().split(','),
            kind="line",
            figsize=(10, 5),
            ax=ax
        )
        plt.title("Control Data of Your Transactions", fontsize=14, fontweight="bold")
        plt.xlabel("Date", fontsize=11)
        plt.ylabel("Amount (Rp)", fontsize=11)
        plt.xticks(rotation=45, ha="right")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(graph.strip().split(','))
        plt.tight_layout()
        plt.show()
    elif choice == "show": # python3 run.py control show
        if not summary:
            print("")
            new_df_agg = df_agg.copy()
            if cum:
                new_df_agg['exceed'] = df_agg['exceed'].cumsum()
                new_df_agg['saved'] = df_agg['saved'].cumsum()    
                new_df_agg['total'] = df_agg['total'].cumsum()
                new_df_agg['delta'] = df_agg['delta'].cumsum()
                new_df_agg['extra'] = df_agg['extra'].cumsum()
            for col in ["total", "delta", "extra"]:
                new_df_agg[col] = new_df_agg[col].apply(rupiah)
            print(
                tabulate(
                    new_df_agg, headers="keys", tablefmt="fancy_grid", showindex=False
                )
            )
        print("")
        print(f"Total exceeded : {df_agg['exceed'].sum()} transaction(s)")
        print(f"Total saved    : {df_agg['saved'].sum()} transaction(s)")
        print(f"Total delta    : {rupiah(df_agg['delta'].sum())}")
        print(f"Total extra    : {rupiah(df_agg['extra'].sum())}")
        print("")
    else:
        raise InvalidCLIArgument(
            "Invalid CLI subcommand for command database: only reset and show are valid.")
    print(": Finishing task...")
