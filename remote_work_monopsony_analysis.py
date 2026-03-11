from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.ticker import PercentFormatter


# ----------------------------
# CONFIGURATION
# ----------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"

WAGE_2019_FILE = DATA_DIR / "national_M2019_dl.xlsx"
WAGE_2023_FILE = DATA_DIR / "national_M2023_dl.xlsx"
WORK_CONTEXT_FILE = DATA_DIR / "Work Context.xlsx"
WORK_ACTIVITIES_FILE = DATA_DIR / "Work Activities.xlsx"

DATASET_OUTPUT_FILE = OUTPUT_DIR / "remote_monopsony_dataset.csv"
FIGURE_OUTPUT_FILE = OUTPUT_DIR / "Figure_1.png"


def load_bls_wage_data(file_2019: Path, file_2023: Path) -> pd.DataFrame:
    """Load and clean BLS OEWS wage data for 2019 and 2023."""
    w19 = pd.read_excel(file_2019)
    w23 = pd.read_excel(file_2023)

    w19.columns = [c.upper() for c in w19.columns]
    w23.columns = [c.upper() for c in w23.columns]

    w19 = keep_detailed_occupations(w19)
    w23 = keep_detailed_occupations(w23)

    w19 = w19[["OCC_CODE", "OCC_TITLE", "A_MEAN"]].copy()
    w23 = w23[["OCC_CODE", "OCC_TITLE", "A_MEAN"]].copy()

    w19 = w19.rename(columns={"A_MEAN": "wage_2019"})
    w23 = w23.rename(columns={"A_MEAN": "wage_2023"})

    w19["wage_2019"] = pd.to_numeric(w19["wage_2019"], errors="coerce")
    w23["wage_2023"] = pd.to_numeric(w23["wage_2023"], errors="coerce")

    w19 = w19.dropna(subset=["wage_2019"])
    w23 = w23.dropna(subset=["wage_2023"])

    wages = pd.merge(w19, w23, on=["OCC_CODE", "OCC_TITLE"], how="inner")
    wages["wage_growth"] = (wages["wage_2023"] - wages["wage_2019"]) / wages["wage_2019"]

    # Keep detailed SOC-style occupation codes such as 11-1011
    wages = wages[wages["OCC_CODE"].astype(str).str.match(r"^\d{2}-\d{4}$", na=False)].copy()

    return wages


def keep_detailed_occupations(df: pd.DataFrame) -> pd.DataFrame:
    """Keep detailed occupations when the grouping column is available."""
    if "OCC_GROUP" in df.columns:
        df["OCC_GROUP"] = df["OCC_GROUP"].astype(str).str.lower()
        return df[df["OCC_GROUP"] == "detailed"].copy()

    if "O_GROUP" in df.columns:
        df["O_GROUP"] = df["O_GROUP"].astype(str).str.lower()
        return df[df["O_GROUP"] == "detailed"].copy()

    return df.copy()


def build_remote_index(work_context_file: Path, work_activities_file: Path) -> pd.DataFrame:
    """Construct an occupation-level remote-work feasibility index from O*NET."""
    work_context = pd.read_excel(work_context_file)
    work_activities = pd.read_excel(work_activities_file)

    context_vars = [
        "Physical Proximity",
        "Face-to-Face Discussions",
        "Deal With External Customers",
    ]
    activity_vars = [
        "Performing for or Working Directly with the Public",
    ]

    wc_sub = work_context[work_context["Element Name"].isin(context_vars)].copy()
    wa_sub = work_activities[work_activities["Element Name"].isin(activity_vars)].copy()

    wc_sub = wc_sub[["O*NET-SOC Code", "Title", "Element Name", "Data Value"]]
    wa_sub = wa_sub[["O*NET-SOC Code", "Title", "Element Name", "Data Value"]]

    onet = pd.concat([wc_sub, wa_sub], ignore_index=True)
    onet["Data Value"] = pd.to_numeric(onet["Data Value"], errors="coerce")
    onet = onet.dropna(subset=["Data Value"])

    onet_wide = onet.pivot_table(
        index=["O*NET-SOC Code", "Title"],
        columns="Element Name",
        values="Data Value",
        aggfunc="mean",
    ).reset_index()

    selected_cols = [col for col in context_vars + activity_vars if col in onet_wide.columns]
    onet_wide["less_remote_score"] = onet_wide[selected_cols].mean(axis=1)

    min_val = onet_wide["less_remote_score"].min()
    max_val = onet_wide["less_remote_score"].max()

    onet_wide["remote_index"] = 1 - (
        (onet_wide["less_remote_score"] - min_val) / (max_val - min_val)
    )

    onet_wide["OCC_CODE"] = (
        onet_wide["O*NET-SOC Code"]
        .astype(str)
        .str.replace(".00", "", regex=False)
        .str.strip()
    )

    return onet_wide[["OCC_CODE", "Title", "remote_index"]].copy()


def merge_datasets(wages: pd.DataFrame, remote_index: pd.DataFrame) -> pd.DataFrame:
    """Merge BLS wages with the constructed O*NET remote-work index."""
    final_df = pd.merge(
        wages,
        remote_index,
        on="OCC_CODE",
        how="inner",
    )

    final_df = final_df[
        ["OCC_CODE", "OCC_TITLE", "wage_2019", "wage_2023", "wage_growth", "remote_index"]
    ].copy()

    return final_df


def make_figure(df: pd.DataFrame, output_file: Path) -> None:
    """Create the descriptive scatter plot used in the paper."""
    plot_df = df.copy()

    low = plot_df["wage_growth"].quantile(0.01)
    high = plot_df["wage_growth"].quantile(0.99)
    plot_df = plot_df[
        (plot_df["wage_growth"] >= low) & (plot_df["wage_growth"] <= high)
    ].copy()

    plt.figure(figsize=(8, 5.5))
    plt.scatter(
        plot_df["remote_index"],
        plot_df["wage_growth"],
        s=14,
        alpha=0.45,
    )

    x = plot_df["remote_index"]
    y = plot_df["wage_growth"]
    coeffs = np.polyfit(x, y, 1)
    fit_line = np.poly1d(coeffs)

    x_line = np.linspace(x.min(), x.max(), 200)
    plt.plot(x_line, fit_line(x_line), linewidth=2)

    plt.xlabel("Remote-work feasibility index (O*NET-based)")
    plt.ylabel("Wage growth, 2019–2023")
    plt.ylim(-0.05, 0.45)
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()


def run_baseline_regression(df: pd.DataFrame):
    """Estimate baseline OLS regression with robust standard errors."""
    X = sm.add_constant(df[["remote_index"]])
    y = df["wage_growth"]
    return sm.OLS(y, X).fit(cov_type="HC1")


def run_controlled_regression(df: pd.DataFrame):
    """Estimate OLS regression controlling for initial wage level."""
    X = sm.add_constant(df[["remote_index", "wage_2019"]])
    y = df["wage_growth"]
    return sm.OLS(y, X).fit(cov_type="HC1")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading and cleaning BLS wage data...")
    wages = load_bls_wage_data(WAGE_2019_FILE, WAGE_2023_FILE)
    print(f"Loaded {len(wages)} detailed occupations from BLS.")

    print("Constructing O*NET remote-work feasibility index...")
    remote_index = build_remote_index(WORK_CONTEXT_FILE, WORK_ACTIVITIES_FILE)

    print("Merging BLS and O*NET data...")
    final_df = merge_datasets(wages, remote_index)
    print(f"Final merged sample: {len(final_df)} occupations.")

    print("Saving merged dataset...")
    final_df.to_csv(DATASET_OUTPUT_FILE, index=False)
    print(f"Dataset saved to: {DATASET_OUTPUT_FILE}")

    print("Creating figure...")
    make_figure(final_df, FIGURE_OUTPUT_FILE)
    print(f"Figure saved to: {FIGURE_OUTPUT_FILE}")

    print("\nBaseline regression:")
    baseline_model = run_baseline_regression(final_df)
    print(baseline_model.summary())

    print("\nControlled regression:")
    controlled_model = run_controlled_regression(final_df)
    print(controlled_model.summary())


if __name__ == "__main__":
    main()
