import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime 
import os
import base64
import schedule
import time
import logging
from scipy import stats
import numpy as np


def generate_report():
    
    df = pd.read_csv("nutrition_data.csv")

    df["attendance_rate"] = df["sessions_attended"] / (df["months_in_program"] * 4)

    df["gain_per_month"] = df["weight_gain_kg"] / df["months_in_program"]

    best_county = df.groupby("county")["weight_gain_kg"].sum().idxmax()

    best_age_group = df.groupby("age_group")["weight_gain_kg"].sum().idxmax()
    
    charts = []
        
    top_county = df.groupby("county")["weight_gain_kg"].mean().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10, 4))
    colors = ["#424BCA" if i > 8 else "#AED6F1" for i in range(10)]
    top_county.plot(kind="barh", ax=ax, color=colors[::-1])
    ax.set_title("Performance per county")
    ax.set_xlabel("Weight Gain (KG)")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig("best_performing_county.png")
    plt.close()
    charts.append(("Performance per county", "best_performing_county.png"))

    age_group = df.groupby("age_group")["weight_gain_kg"].mean().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#489F26" if i > 8 else "#AED6F1" for i in range(10)]
    age_group.plot(kind="bar", ax=ax, color=colors[::-1])
    ax.set_title("Performance per age-group")
    ax.set_xlabel("Age Group")
    ax.bar_label(ax.containers[0], fmt="%.2f kg", padding=3, fontsize=12)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("best_performing_agegroup.png")
    plt.close()
    charts.append(("Performance per age-group", "best_performing_agegroup.png"))


    analysis = df.dropna(subset=["attendance_rate", "gain_per_month"])

    r, p = stats.pearsonr(analysis["attendance_rate"], analysis["gain_per_month"])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(analysis["attendance_rate"], analysis["gain_per_month"], color="#1F4E79", alpha=0.3, s=30)
    slope, intercept = np.polyfit(analysis["attendance_rate"], analysis["gain_per_month"], 1)
    x = np.linspace(analysis["attendance_rate"].min(), analysis["attendance_rate"].max(), 100)
    ax.plot(x, slope * x + intercept, color="#FF6B6B", linewidth=2)
    ax.text(x[-1], slope * x[-1] + intercept + 0.03, "Overall trend", color="red", ha="right", fontsize=11)        
    ax.set_title("Attendance vs weight gain")
    ax.set_xlabel("Share of sessions attended")
    ax.set_ylabel("Weight gain per month (kg)")
    plt.tight_layout()
    plt.savefig("attendance_vs_gain.png", dpi=150)
    plt.close()
    charts.append(("Attendance vs weight gain", "attendance_vs_gain.png"))

    return {
        "avg_attendance": df["attendance_rate"].mean(),
        "avg_gain_per_month": df["gain_per_month"].mean(),
        "best_county": best_county,
        "best_age_group": best_age_group,      
        "charts": charts,
    }

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def build_html_report(data, timestamp, run_date):
    chart_html = ""
    for title, path in data["charts"]:
        img_b64 = encode_image(path)
        chart_html += (
            f'<h3>{title}</h3>'
            f'<img src="data:image/png;base64,{img_b64}" width="600">'
        )
    summary = (
        f"Across the program, average attendance is {data['avg_attendance']:.0%} and children "
        f"gain {data['avg_gain_per_month']:.2f} kg per month on average. "
        f"{data['best_county']} is the best-performing county, and the {data['best_age_group']} "
        f"age group shows the strongest gains."
    )
    html = (
        '<html><body style="font-family:Arial">'
        f'<h2>NGO Food Program: {timestamp}</h2>'
        f'<p>{summary}</p>'
        f'{chart_html}'
        '</body></html>'
    )

    os.makedirs("reports", exist_ok=True)
    path = f"reports/report_{run_date}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Report saved to {path}")



logging.basicConfig(filename="report.log", level=logging.INFO,
                    format="%(asctime)s | %(message)s")

def weekly_job():
    try:
        timestamp = datetime.now().strftime("%A %d %B %Y at %H:%M")
        data = generate_report()
        run_date = datetime.now().strftime("%Y-%m-%d")
        build_html_report(data, timestamp, run_date)
        logging.info("Report generated and saved OK")
    except Exception as e:
        logging.error(f"Report failed: {e}")

schedule.every().monday.at("07:00").do(weekly_job)

while True:
    schedule.run_pending()
    time.sleep(60)
