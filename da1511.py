import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "bookDA.csv"

def clean_number(x):
    if pd.isna(x):
        return 0.0
    if isinstance(x, str):
        s = (x.replace("\xa0", " ")
               .replace("$", "")
               .replace(" ", "")
               .replace(".", "")
               .replace(",", ".")
               .strip())
        if s == "":
            return 0.0
        try:
            return float(s)
        except ValueError:
            return 0.0
    try:
        return float(x)
    except Exception:
        return 0.0

def load_and_normalize(csv_path: str) -> pd.DataFrame:
    for skip in (0, 1, 2):
        try:
            tmp = pd.read_csv(csv_path, sep=";", skiprows=skip)
        except Exception:
            continue
        header_upper = [str(c).upper() for c in tmp.columns]
        if any(k in header_upper for k in ["EMPLOYEE", "GROSS", "DIVISION", "STATUS", "HOURLY", "HRS"]):
            df = tmp.copy()
            break
    else:
        raw = pd.read_csv(csv_path, sep=";", header=None)
        df = raw.copy()
        df.columns = [f"COL_{i}" for i in range(df.shape[1])]

    def columns_look_like_data(cols):
        return any(isinstance(c,str) and ("$" in c or "," in c or c.replace(" ","").isdigit()) for c in cols)
    if columns_look_like_data(df.columns):
        first_row = df.iloc[0].tolist()
        df = df.iloc[1:].reset_index(drop=True)
        df.insert(0, "_RECOVERED_ROW_0", first_row[0])
        cols = list(df.columns)
        mapping = {
            0: "EMPLOYEE ID",
            1: "EMPLOYEE",
            2: "LOCATION",
            3: "DIVISION",
            4: "HIRE DATE",
            5: "HRS",
            6: "HOURLY RATE",
            7: "GROSS PAY",
            8: "STATUS",
        }
        new_cols = []
        for i, old in enumerate(cols):
            new_cols.append(mapping.get(i, f"EXTRA_{i}"))
        df.columns = new_cols
    else:
        df.columns = (df.columns
                        .str.replace("\xa0", " ")
                        .str.replace("  ", " ")
                        .str.strip()
                        .str.upper())

    required_defaults = {
        "EMPLOYEE": lambda d: d.iloc[:,1] if d.shape[1] > 1 else pd.RangeIndex(len(d)).astype(str),
        "DIVISION": lambda d: ["UNKNOWN"]*len(d),
        "STATUS": lambda d: ["UNKNOWN"]*len(d),
        "HRS": lambda d: [0]*len(d),
        "HOURLY RATE": lambda d: [0]*len(d),
        "GROSS PAY": lambda d: [0]*len(d),
    }
    for col, factory in required_defaults.items():
        if col not in df.columns:
            df[col] = factory(df)

    for c in ["HRS", "HOURLY RATE", "GROSS PAY"]:
        df[c] = df[c].apply(clean_number)
    return df

df = load_and_normalize(CSV_PATH)

def plot_first_10_employees(df):
    first10 = df.head(10)
    names = first10["EMPLOYEE"].astype(str)
    pay = first10["GROSS PAY"].astype(float)
    plt.figure(figsize=(10,5))
    bars = plt.bar(names, pay, color="steelblue")
    plt.title("Gross Pay of First 10 Employees")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Gross Pay")
    for b in bars:
        plt.text(b.get_x()+b.get_width()/2, b.get_height(), f"${b.get_height():.2f}", ha="center", va="bottom")
    plt.tight_layout(); plt.savefig("part1_first10.png"); plt.show()

def plot_avg_pay_by_division(df):
    avg = df.groupby("DIVISION")["GROSS PAY"].mean().sort_values(ascending=False)
    plt.figure(figsize=(10,5))
    bars = plt.bar(avg.index, avg.values, color="teal")
    plt.title("Average Gross Pay by Division")
    plt.xlabel("Division"); plt.ylabel("Average Gross Pay")
    for b in bars:
        plt.text(b.get_x()+b.get_width()/2, b.get_height(), f"${b.get_height():.2f}", ha="center", va="bottom")
    plt.tight_layout(); plt.savefig("part2_avg_pay_division.png"); plt.show()

def scatter_hours_pay(df):
    plt.figure(figsize=(7,5))
    statuses = df["STATUS"].unique()
    palette = {s:"blue" if "FULL" in str(s).upper() else "red" for s in statuses}
    for s in statuses:
        subset = df[df["STATUS"]==s]
        plt.scatter(subset["HRS"], subset["GROSS PAY"], label=s, c=palette[s], alpha=0.75)
    plt.title("Hours Worked vs Gross Pay")
    plt.xlabel("Hours Worked"); plt.ylabel("Gross Pay")
    plt.grid(True); plt.legend(); plt.tight_layout(); plt.savefig("part3_scatter_hours_pay.png"); plt.show()

def histogram_hourly_rate(df):
    plt.figure(figsize=(7,5))
    plt.hist(df["HOURLY RATE"], bins=10, color="purple", edgecolor="white")
    plt.title("Distribution of Hourly Rates")
    plt.xlabel("Hourly Rate"); plt.ylabel("Frequency")
    plt.tight_layout(); plt.savefig("part4_hourly_hist.png"); plt.show()

def pie_status(df):
    counts = df["STATUS"].value_counts()
    explode = [0.1 if v==counts.max() else 0 for v in counts]
    plt.figure(figsize=(6,6))
    plt.pie(counts, labels=counts.index, autopct="%1.1f%%", explode=explode, shadow=True, startangle=140)
    plt.title("Employee Status Distribution")
    plt.tight_layout(); plt.savefig("part5_status_pie.png"); plt.show()

def subplots_2x2(df):
    fig, axs = plt.subplots(2,2, figsize=(12,10))
    fig.suptitle("Payroll Data Visualizations", fontsize=16)
    avg = df.groupby("DIVISION")["GROSS PAY"].mean()
    axs[0,0].bar(avg.index, avg.values, color="teal")
    axs[0,0].set_title("Avg Gross Pay / Division")
    axs[0,1].hist(df["HOURLY RATE"], bins=10, color="purple", edgecolor="white")
    axs[0,1].set_title("Hourly Rate Distribution")
    statuses = df["STATUS"].unique(); palette = {s:"blue" if "FULL" in str(s).upper() else "red" for s in statuses}
    for s in statuses:
        sub = df[df["STATUS"]==s]
        axs[1,0].scatter(sub["HRS"], sub["GROSS PAY"], c=palette[s], label=s, alpha=0.75)
    axs[1,0].set_title("Hours vs Gross Pay"); axs[1,0].legend()
    counts = df["STATUS"].value_counts(); axs[1,1].pie(counts, labels=counts.index, autopct="%1.1f%%")
    axs[1,1].set_title("Status Breakdown")
    plt.tight_layout(); plt.savefig("part6_subplots.png"); plt.show()

def mini_project(df):
    plt.figure(figsize=(9,5))
    df.boxplot(column="GROSS PAY", by="DIVISION", grid=False)
    plt.title("Pay Distribution by Division"); plt.suptitle("")
    plt.tight_layout(); plt.savefig("mini_pay_division.png"); plt.show()
    plt.figure(figsize=(8,5))
    plt.scatter(df["HRS"], df["GROSS PAY"], c="green", alpha=0.7)
    plt.title("Hours Worked vs Gross Pay"); plt.xlabel("Hours"); plt.ylabel("Gross Pay"); plt.grid(True)
    plt.tight_layout(); plt.savefig("mini_hours_pay.png"); plt.show()
    plt.figure(figsize=(8,5))
    df["STATUS"].value_counts().plot(kind="bar", color=["orange","purple"])
    plt.title("Employee Status Breakdown"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig("mini_status_bar.png"); plt.show()

df_summary = df.head(1).to_dict(orient="records")[0]
print("Loaded & normalized columns:", list(df.columns))
print("Sample first row (normalized):", df_summary)

plot_first_10_employees(df)
plot_avg_pay_by_division(df)
scatter_hours_pay(df)
histogram_hourly_rate(df)
pie_status(df)
subplots_2x2(df)
mini_project(df)

