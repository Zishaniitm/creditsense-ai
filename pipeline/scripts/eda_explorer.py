"""
eda_explorer.py
Performs Exploratory Data Analysis on the credit scoring dataset.
Outputs: printed stats + 3 chart PNG files saved to data/raw/eda_charts/
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# ── Config ─────────────────────────────────────────────────────────────────
CREDIT_DATA_PATH = "data/raw/credit_raw.csv"
FRAUD_DATA_PATH  = "data/synthetic/fraud_transactions.csv"
CHARTS_DIR       = "data/raw/eda_charts"

# Clean column names for display
CREDIT_COLUMNS = {
    "SeriousDlqin2yrs":                        "target",
    "RevolvingUtilizationOfUnsecuredLines":     "revolving_utilization",
    "age":                                      "age",
    "NumberOfTime30-59DaysPastDueNotWorse":     "late_30_59_days",
    "DebtRatio":                                "debt_ratio",
    "MonthlyIncome":                            "monthly_income",
    "NumberOfOpenCreditLinesAndLoans":          "open_credit_lines",
    "NumberOfTimes90DaysLate":                  "late_90_days",
    "NumberRealEstateLoansOrLines":             "real_estate_loans",
    "NumberOfTime60-89DaysPastDueNotWorse":     "late_60_89_days",
    "NumberOfDependents":                       "num_dependents"
}

sns.set_theme(style="whitegrid", palette="muted")
os.makedirs(CHARTS_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
#  CREDIT DATASET EDA
# ══════════════════════════════════════════════════════════════════

def load_and_rename(path, col_map=None):
    df = pd.read_csv(path)
    if col_map:
        df.rename(columns=col_map, inplace=True)
    # Drop unnamed index column if present
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


def print_basic_stats(df, name):
    print(f"\n{'='*60}")
    print(f"  DATASET: {name}")
    print(f"{'='*60}")
    print(f"  Shape         : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Memory usage  : {df.memory_usage(deep=True).sum()/1024/1024:.2f} MB")
    print(f"\n  Column Types:")
    for dtype, count in df.dtypes.value_counts().items():
        print(f"    {str(dtype):<12} → {count} columns")


def print_null_report(df):
    null_counts = df.isnull().sum()
    null_pct    = (null_counts / len(df) * 100).round(2)
    null_df     = pd.DataFrame({
        "Missing Count": null_counts,
        "Missing %":     null_pct
    }).query("`Missing Count` > 0").sort_values("Missing %", ascending=False)

    if null_df.empty:
        print("\n  ✅ No missing values found.")
    else:
        print(f"\n  ⚠️  Missing Values ({len(null_df)} columns affected):")
        print(null_df.to_string())


def print_target_distribution(df, target_col):
    vc = df[target_col].value_counts()
    pct = (vc / len(df) * 100).round(2)
    print(f"\n  Target Distribution ('{target_col}'):")
    for label, count in vc.items():
        bar = "█" * int(pct[label] / 2)
        print(f"    {label} → {count:>7,} ({pct[label]:>5.1f}%)  {bar}")


def print_numeric_summary(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print(f"\n  Numeric Summary ({len(numeric_cols)} columns):")
    summary = df[numeric_cols].describe().T[["mean","std","min","50%","max"]]
    summary.columns = ["Mean","Std","Min","Median","Max"]
    summary = summary.round(2)
    print(summary.to_string())


# ── Chart 1: Class Imbalance ────────────────────────────────────────────────
def plot_class_imbalance(df, target_col, title, filename):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)

    counts = df[target_col].value_counts()
    labels = ["Non-Default (0)", "Default (1)"] if 0 in counts.index \
             else ["Legitimate", "Fraudulent"]
    colors = ["#3B82F6", "#EF4444"]

    # Bar chart
    axes[0].bar(labels, counts.values, color=colors, edgecolor='white', linewidth=1.5)
    axes[0].set_title("Class Counts")
    axes[0].set_ylabel("Number of Records")
    for i, v in enumerate(counts.values):
        axes[0].text(i, v + counts.max()*0.01, f"{v:,}", ha='center', fontweight='bold')

    # Pie chart
    axes[1].pie(counts.values, labels=labels, colors=colors,
                autopct='%1.1f%%', startangle=90,
                wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    axes[1].set_title("Class Distribution (%)")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📊 Chart saved: {path}")


# ── Chart 2: Feature Distributions ─────────────────────────────────────────
def plot_feature_distributions(df, target_col, filename):
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c != target_col][:8]   # plot max 8 features

    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    fig.suptitle("Feature Distributions", fontsize=14, fontweight='bold')
    axes = axes.flatten()

    for i, col in enumerate(feature_cols):
        # Cap extreme outliers for display only
        cap = df[col].quantile(0.99)
        data = df[col].clip(upper=cap)

        axes[i].hist(data[df[target_col]==0], bins=40, alpha=0.6,
                     color='#3B82F6', label='Non-Fraud/Default')
        axes[i].hist(data[df[target_col]==1], bins=40, alpha=0.6,
                     color='#EF4444', label='Fraud/Default')
        axes[i].set_title(col.replace('_', ' ').title(), fontsize=10)
        axes[i].set_xlabel('')
        axes[i].legend(fontsize=7)

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📊 Chart saved: {path}")


# ── Chart 3: Correlation Heatmap ───────────────────────────────────────────
def plot_correlation_heatmap(df, target_col, filename):
    numeric_df = df.select_dtypes(include=[np.number])

    # Clip extreme outliers for correlation accuracy
    numeric_df = numeric_df.clip(
        lower=numeric_df.quantile(0.01),
        upper=numeric_df.quantile(0.99),
        axis=1
    )

    corr = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(12, 9))
    mask = np.triu(np.ones_like(corr, dtype=bool))   # upper triangle mask

    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f",
        cmap="RdBu_r", center=0, vmin=-1, vmax=1,
        linewidths=0.5, ax=ax,
        annot_kws={"size": 9}
    )
    ax.set_title("Feature Correlation Heatmap", fontsize=14, fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📊 Chart saved: {path}")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*60)
    print("  CreditSense AI — EDA Explorer")
    print("="*60)

    # ── Credit Dataset ──────────────────────────────────────────
    print("\n>>> Analysing Credit Scoring Dataset...")
    credit_df = load_and_rename(CREDIT_DATA_PATH, CREDIT_COLUMNS)

    print_basic_stats(credit_df, "Credit Scoring (Give Me Some Credit)")
    print_null_report(credit_df)
    print_target_distribution(credit_df, "target")
    print_numeric_summary(credit_df)

    plot_class_imbalance(credit_df, "target",
                         "Credit Default — Class Imbalance",
                         "credit_class_imbalance.png")
    plot_feature_distributions(credit_df, "target",
                               "credit_feature_distributions.png")
    plot_correlation_heatmap(credit_df, "target",
                             "credit_correlation_heatmap.png")

    # ── Fraud Dataset ────────────────────────────────────────────
    print("\n>>> Analysing Synthetic Fraud Dataset...")
    fraud_df = load_and_rename(FRAUD_DATA_PATH)

    print_basic_stats(fraud_df, "Synthetic Fraud Transactions")
    print_null_report(fraud_df)
    print_target_distribution(fraud_df, "is_fraud")

    plot_class_imbalance(fraud_df, "is_fraud",
                         "Fraud Transactions — Class Imbalance",
                         "fraud_class_imbalance.png")
    plot_feature_distributions(fraud_df, "is_fraud",
                               "fraud_feature_distributions.png")
    plot_correlation_heatmap(fraud_df, "is_fraud",
                             "fraud_correlation_heatmap.png")

    print(f"\n{'='*60}")
    print(f"  ✅ EDA Complete! All charts saved to: {CHARTS_DIR}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()