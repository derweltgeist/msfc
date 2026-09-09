from datetime import datetime, timedelta

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch

from src.get import get
from src.error import InvalidCLIArgument

def graph(choice: str, verbose: bool, noadmin: bool, adminfee: bool, range: dict[str, str]):
    rows: list[sqlite3.Row] = get(range, verbose)
    values: list[float] = []
    admin:  list[float] = []
    print(": Plotting graph, please wait...")
    fig, ax = plt.subplots(figsize=(10, 5), num="My Shitty Finance Calculator")
    # 2. Fix the Y-Axis: Convert scientific notation (1e6) into clean Rupiah formatting
    def rupiah_formatter(x: float, pos):
        if x >= 1e6 or x <= -1e6:
            return f"Rp{x*1e-6:.1f}jt"  # e.g., Rp1.0jt for millions
        elif x >= 1e3 or x <= -1e3:
            return f"Rp{x*1e-3:.0f}k"   # e.g., Rp50k for thousands
        else:
            return f"Rp{x:.0f}"
    # python3 run.py graph time (i vibe coded this because i am too lazy sorry)
    if choice == "time":
        # 1. Safely accumulate totals by date so multiple transactions on the same day add up!
        raw_data = {}
        raw_admin = {}
        for row in rows:
            date_str = row["date"].split()[0]
            if noadmin:
                amount = row["total"]  # Use "total" consistently
            else:
                amount = row["value"]
            if adminfee:
                admin_amount = row["admin"]
                raw_admin[date_str] = raw_admin.get(date_str, 0) + admin_amount
            raw_data[date_str] = raw_data.get(date_str, 0) + amount
            
        dates = []
    
        if raw_data:
            # 2. Find the absolute start and end dates from your data
            date_keys = [datetime.strptime(d, "%Y-%m-%d") for d in raw_data.keys()]
            start_date = min(date_keys)
            end_date = max(date_keys)
            # 3. Generate every single day continuously from start to end
            dates = []
            values = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                dates.append(current_date)
                # If a transaction exists for this day, use its summed total; otherwise, fill with 0!
                values.append(raw_data.get(date_str, 0))
                if adminfee:
                    admin.append(raw_admin.get(date_str, 0))
                current_date += timedelta(days=1)

        if noadmin:
            ax.plot(dates, values, linestyle="-", label="Nominal Value", color="#2b5c8f", linewidth=1.5, markersize=3)
        else:
            ax.plot(dates, values, linestyle="-", label="Total Value", color="#2b5c8f", linewidth=1.5, markersize=3)

        if adminfee:
            ax.plot(dates, admin, linestyle="-", label="Admin Fee", color="#d9534f", linewidth=1.5, markersize=3)
            
        ax.yaxis.set_major_formatter(FuncFormatter(rupiah_formatter))

        # 3. Add titles, labels, and grid for readability
        ax.set_title("Transaction Values Over Time", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel("Amount (Rp)", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.6)

        # Intelligent date locator so it doesn't crowd each other (like Google Sheets)
        locator = mdates.AutoDateLocator(minticks=3, maxticks=10)
        formatter = mdates.AutoDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        # Automatically rotate and format date labels cleanly
        fig.autofmt_xdate()
        ax.legend()
    elif choice in ("party", "category", "active", "passive", "wallet"):
        aggregated_values = {}
        aggregated_admin = {}

        for row in rows:
            key = row[choice]
            # Main transaction amount
            amount = row["value"] if noadmin else row["total"]
            aggregated_values[key] = aggregated_values.get(key, 0) + (amount if amount else 0)
            
            if adminfee:
                # Explicitly target the admin fee; use absolute value if stored as negative, 
                # or ensure it doesn't fallback to 'total'/'value'
                try:
                    admin_val = row["admin"]
                    if admin_val is None:
                        admin_val = 0
                except (KeyError, TypeError, IndexError):
                    admin_val = 0
                
                aggregated_admin[key] = aggregated_admin.get(key, 0) + admin_val

        # Extract the shared list of keys/categories
        div = list(aggregated_values.keys())
        
        # Build aligned lists
        values = [aggregated_values[k] for k in div]
        admin = [aggregated_admin.get(k, 0) for k in div] if adminfee else []

        colors = ["#2b8a3e" if v >= 0 else "#c92a2a" for v in values]
        width: float = 0.35

        if adminfee:
            x = np.arange(0, len(div))
            if noadmin:
                ax.bar(x - width/2, values, width, label="Nominal value", color=colors)
            else:
                ax.bar(x - width/2, values, width, label="Total value", color=colors)
            ax.bar(x + width/2, admin, width, label="Admin fees", color="#682196")
            ax.set_xticks(x)
            ax.set_xticklabels(div, rotation=30, ha="right")
            ax.legend(frameon=True)
        else:
            if noadmin:
                ax.bar(div, values, width * 2, label="Nominal value", color=colors)
            else:
                ax.bar(div, values, width * 2, label="Total value", color=colors)
            plt.xticks(rotation=30, ha="right")
        ax.yaxis.set_major_formatter(FuncFormatter(rupiah_formatter))
        ax.axhline(0, color="black", linewidth=0.8, linestyle="-")
        ax.set_title(f"Transactions Values by {choice.capitalize()}", fontsize=14, fontweight="bold")
        ax.set_xlabel(f"{choice.capitalize()}", fontsize=11)
        ax.set_ylabel("Amount (Rp)", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5, axis="y")

        # Create custom multi-colored legend handles manually!
        if noadmin:
            legend_elements = [
                Patch(facecolor="#2b8a3e", label="Nominal Income"),
                Patch(facecolor="#c92a2a", label="Nominal Expense"),
                Patch(facecolor="#682196", label="Admin Fees")
            ]
        else:
            legend_elements = [
                Patch(facecolor="#2b8a3e", label="Total Income"),
                Patch(facecolor="#c92a2a", label="Total Expense"),
                Patch(facecolor="#682196", label="Admin Fees")
            ]            
        ax.legend(handles=legend_elements, frameon=True, loc="upper right")
    else:
        raise InvalidCLIArgument("run.py graph only accepts time, category, party, active, passive, and wallet.")
    # 4. Adjust layout and display the chart
    plt.tight_layout()
    plt.show()
    print(": Finishing task...")