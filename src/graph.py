from datetime import datetime, timedelta

import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch
import mplfinance as mpf

from src.get import get
from src.error import InvalidCLIArgument

def graph(choice: str, verbose: bool, noadmin: bool, adminfee: bool, cum: bool, candle: bool, range: dict[str, str]):
    rows: list[sqlite3.Row] = get(range, verbose)
    values: list[float] = []
    admin:  list[float] = []
    print(": Plotting graph, please wait...")
    fig, ax = plt.subplots(figsize=(10, 5), num="My Shitty Finance Calculator")
    # 2. Fix the Y-Axis: Convert scientific notation (1e6) into clean Rupiah formatting
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

        if candle:
            # --- DYNAMIC CANDLESTICK & MULTI-LINE PLOTTING ---
            days_span = (max(dates) - min(dates)).days if dates else 0
            if days_span <= 30:
                rule = "D"
            elif days_span <= 180:
                rule = "3D"
            elif days_span <= 365:
                rule = "W"
            else:
                rule = "ME"

            def plot_candlestick(series_data, label_name):
                df_temp = pd.DataFrame(
                    {"val": series_data}, index=pd.to_datetime(dates)
                )
                ohlc = df_temp["val"].resample(rule).ohlc()
                ohlc["close"] = ohlc["close"].ffill().fillna(0)
                ohlc["open"] = ohlc["open"].fillna(ohlc["close"])
                ohlc["high"] = ohlc["high"].fillna(ohlc["close"])
                ohlc["low"] = ohlc["low"].fillna(ohlc["close"])

                # show_nontrading=True forces real datetimes onto the x-axis!
                mpf.plot(
                    ohlc,
                    type="candle",
                    ax=ax,
                    style="charles",
                    show_nontrading=True
                )
                ax.set_title(label_name, fontsize=14, fontweight="bold")

            label_text = "Nominal Value" if noadmin else "Total Value"
            if cum:
                plot_candlestick(np.cumsum(values), label_text)
            else:
                plot_candlestick(values, label_text)

            if adminfee:
                ax.plot(
                    dates,
                    np.cumsum(admin) if cum else admin,
                    linestyle="-",
                    label="Admin Fee",
                    color="#2b5c8f",
                    linewidth=1.5,
                    markersize=3,
                )

            # Manual legend setup
            from matplotlib.artist import Artist
            legend_elements: list[Artist] = [
                Patch(facecolor="#2b8a3e", edgecolor="#2b8a3e", label="Positive"),
                Patch(facecolor="#c92a2a", edgecolor="#c92a2a", label="Negative"),
            ]
            if adminfee:
                legend_elements.append(
                    Line2D([0], [0], color="#d9534f", lw=1.5, label="Admin Fee")
                )

            ax.legend(handles=legend_elements, loc="upper left")
        else:
            if noadmin:
                if cum:
                    ax.plot(dates, np.cumsum(values), linestyle="-", label="Nominal Value", color="#2b5c8f", linewidth=1.5, markersize=3)
                else:
                    ax.plot(dates, values, linestyle="-", label="Nominal Value", color="#2b5c8f", linewidth=1.5, markersize=3)
            else:
                if cum:
                    ax.plot(dates, np.cumsum(values), linestyle="-", label="Total Value", color="#2b5c8f", linewidth=1.5, markersize=3)
                else:
                    ax.plot(dates, values, linestyle="-", label="Total Value", color="#2b5c8f", linewidth=1.5, markersize=3)
            if adminfee:
                if cum:
                     ax.plot(dates, np.cumsum(admin), linestyle="-", label="Admin Fee", color="#d9534f", linewidth=1.5, markersize=3)
                else:
                    ax.plot(dates, admin, linestyle="-", label="Admin Fee", color="#d9534f", linewidth=1.5, markersize=3)
            ax.legend()
        ax.yaxis.set_major_formatter(FuncFormatter(rupiah_formatter))

        # 3. Add titles, labels, and grid for readability
        ax.set_title("Transaction Values Over Time", fontsize=14, fontweight="bold")
        ax.yaxis.set_label_position("left")
        ax.yaxis.tick_left()
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