import pandas as pd
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np


#  CHART DESIGN TOKENS  — matches dashboard palette exactly
C_BG       = "#09090B"   # figure background
C_PANEL    = "#18181B"   # axes background
C_SURFACE  = "#27272A"   # bars / elements surface
C_BORDER   = "#3F3F46"   # axis borders, grid
C_TEXT_HI  = "#FAFAFA"   # primary labels
C_TEXT_MED = "#A1A1AA"   # secondary / tick labels
C_TEXT_LO  = "#52525B"   # very muted
C_ACCENT   = "#10B981"   # primary series — emerald green
C_ACCENT_2 = "#059669"   # slightly darker variant

# 8-colour categorical palette — professional, distinct, no neons
PALETTE = [
    "#10B981",  # emerald
    "#3B82F6",  # blue
    "#F59E0B",  # amber
    "#8B5CF6",  # violet
    "#EF4444",  # red
    "#06B6D4",  # cyan
    "#F97316",  # orange
    "#6366F1",  # indigo
]

FONT_SANS = "DejaVu Sans"   # universally available; clean & readable


def _setup():
    """Apply global rcParams once."""
    plt.rcParams.update({
        # figure
        "figure.facecolor":     C_BG,
        "figure.dpi":           130,
        "savefig.facecolor":    C_BG,
        "savefig.bbox":         "tight",
        "savefig.pad_inches":   0.25,

        # axes
        "axes.facecolor":       C_PANEL,
        "axes.edgecolor":       C_BORDER,
        "axes.labelcolor":      C_TEXT_MED,
        "axes.titlecolor":      C_TEXT_HI,
        "axes.titlesize":       12,
        "axes.titleweight":     "bold",
        "axes.titlepad":        14,
        "axes.labelsize":       9,
        "axes.spines.top":      False,
        "axes.spines.right":    False,
        "axes.spines.left":     True,
        "axes.spines.bottom":   True,
        "axes.grid":            True,
        "axes.axisbelow":       True,   # grid behind bars

        # grid
        "grid.color":           C_BORDER,
        "grid.linewidth":       0.6,
        "grid.alpha":           0.5,
        "grid.linestyle":       "--",

        # ticks
        "xtick.color":          C_TEXT_MED,
        "ytick.color":          C_TEXT_MED,
        "xtick.labelsize":      8,
        "ytick.labelsize":      8,
        "xtick.major.pad":      6,
        "ytick.major.pad":      6,

        # text
        "text.color":           C_TEXT_HI,
        "font.family":          "sans-serif",
        "font.sans-serif":      [FONT_SANS, "Segoe UI", "Arial", "Helvetica"],
        "font.size":            9,

        # legend
        "legend.facecolor":     C_SURFACE,
        "legend.edgecolor":     C_BORDER,
        "legend.labelcolor":    C_TEXT_MED,
        "legend.fontsize":      8,
        "legend.framealpha":    0.9,
    })

_setup()



#  HELPERS
def find_col(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k in col:
                return col
    return None


def _fmt_k(ax, axis="y"):
    """Format axis values as 1.2K / 3.4M."""
    def _f(x, _):
        if abs(x) >= 1_000_000: return f"{x/1_000_000:.1f}M"
        if abs(x) >= 1_000:     return f"{x/1_000:.1f}K"
        return f"{x:,.0f}"
    if axis == "y":
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_f))
    else:
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(_f))


def _bar_value_labels(ax, bars, color=C_TEXT_MED, fontsize=7):
    """Add value labels above each bar."""
    for bar in bars:
        h = bar.get_height()
        if h == 0: continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h * 1.012,
            f"{h:,.0f}" if h < 10_000 else (f"{h/1000:.1f}K" if h < 1_000_000 else f"{h/1_000_000:.1f}M"),
            ha="center", va="bottom",
            fontsize=fontsize, color=color,
        )


def _style_bar_ax(ax):
    ax.spines["left"].set_color(C_BORDER)
    ax.spines["bottom"].set_color(C_BORDER)
    ax.tick_params(colors=C_TEXT_MED)


#  CHART FUNCTIONS
def _bar_chart(data, title, xlabel, ylabel, path, top_n=None):
    if top_n:
        data = data.nlargest(top_n)

    data = data.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))

    bars = ax.bar(
        data.index.astype(str),
        data.values,
        color=PALETTE[:len(data)],
        edgecolor=C_PANEL,
        linewidth=0.8
    )

    # 🔥 VALUE LABELS ON TOP
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            h,
            f"{h:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=C_TEXT_HI
        )

    # 🔥 CLEAN STYLE
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    colors = PALETTE[:len(data)]
    colors[0] = "#22C55E"  # highlight top bar

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.grid(axis="y", linestyle="--", alpha=0.3)

    plt.xticks(rotation=30, ha="right")

    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _horizontal_bar(data, title, xlabel, path, top_n=12):
    data = data.nlargest(top_n).sort_values()
    fig, ax = plt.subplots(figsize=(8.5, max(3.5, len(data) * 0.42)))
    bars = ax.barh(
        data.index.astype(str), data.values,
        color=C_ACCENT, edgecolor=C_PANEL, linewidth=0.8, height=0.6,
        zorder=3,
    )
    for bar in bars:
        w = bar.get_width()
        if w == 0: continue
        ax.text(w * 1.01, bar.get_y() + bar.get_height() / 2,
                f"{w:,.0f}" if w < 10_000 else f"{w/1000:.1f}K",
                va="center", fontsize=7, color=C_TEXT_MED)
    ax.spines["bottom"].set_color(C_BORDER)
    ax.spines["left"].set_color(C_BORDER)
    _fmt_k(ax, axis="x")
    ax.set_title(title)
    ax.set_xlabel(xlabel, labelpad=8)
    ax.tick_params(colors=C_TEXT_MED)
    plt.tight_layout()
    plt.savefig(path)
    plt.close(fig)


def _scatter_chart(x, y, title, xlabel, ylabel, path):
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        x, y,
        alpha=0.6,
        color=C_ACCENT,
        edgecolors=C_PANEL,
        s=30
    )

    # 🔥 TREND LINE
    try:
        m, b = np.polyfit(x.values, y.values, 1)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs, m*xs + b,
                color="#F59E0B",
                linestyle="--",
                linewidth=2,
                label="Trend")

        ax.legend()
    except:
        pass

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _donut_chart(data, title, path, top_n=6):
    """Donut (modern take on pie) with a centre label."""
    data = data.nlargest(top_n)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    wedges, texts, autotexts = ax.pie(
        data.values,
        labels=data.index.astype(str),
        autopct="%1.1f%%",
        colors=PALETTE[:len(data)],
        startangle=120,
        pctdistance=0.78,
        wedgeprops=dict(width=0.55, edgecolor=C_PANEL, linewidth=2),
    )
    for t in texts:
        t.set_color(C_TEXT_MED); t.set_fontsize(8)
    for t in autotexts:
        t.set_color(C_TEXT_HI);  t.set_fontsize(7.5); t.set_fontweight("bold")
    ax.set_title(title, pad=18)
    plt.tight_layout()
    plt.savefig(path)
    plt.close(fig)


def _line_chart(series, title, ylabel, path):
    fig, ax = plt.subplots(figsize=(10, 5))

    xs = range(len(series))

    # 🔥 FILL AREA
    ax.fill_between(xs, series.values,
                    color=C_ACCENT, alpha=0.15)

    # 🔥 LINE
    ax.plot(xs, series.values,
            color=C_ACCENT,
            linewidth=2.5)

    # 🔥 POINTS
    ax.scatter(xs, series.values,
               color=C_ACCENT,
               s=40)

    ax.set_xticks(xs)
    ax.set_xticklabels(series.index.astype(str), rotation=30)

    ax.set_title(title)
    ax.set_ylabel(ylabel)

    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(path)
    plt.close()


#  MAIN ENTRY POINT
def run_analysis(file_path):
    _setup()   # re-apply in thread context

    file_name = os.path.basename(file_path)
    base_name = f"cleaned_{file_name}".replace(".csv", "")

    df = pd.read_csv(file_path, encoding="latin1")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.drop_duplicates()

    # Column detection
    sales    = find_col(df, ["sales", "revenue", "amount", "total"])
    profit   = find_col(df, ["profit", "margin", "earn"])
    discount = find_col(df, ["discount"])
    category = find_col(df, ["category", "type"])
    subcat   = find_col(df, ["sub", "subcategory"])
    region   = find_col(df, ["region", "country", "location", "state"])
    date_col = find_col(df, ["date", "order_date", "orderdate", "day"])

    os.makedirs("Data/cleaned", exist_ok=True)
    os.makedirs("charts", exist_ok=True)

    for f in os.listdir("charts"):
        if f.startswith(base_name):
            try:
                os.remove(os.path.join("charts", f))   # ✅ properly indented
            except:
                pass

    # Save cleaned CSV
    df.to_csv(f"Data/cleaned/{base_name}.csv", index=False)

    def safe(fn):
        try:   fn()
        except Exception as e: print(f"  ⚠ chart skipped: {e}")

    # 1. Sales by category (bar)
    if sales and category:
        safe(lambda: _bar_chart(
            df.groupby(category)[sales].sum(),
            "Sales by Category", "Category", "Revenue",
            f"charts/{base_name}_category.png"))

    # 2. Top sub-categories (horizontal bar)
    if sales and subcat:
        safe(lambda: _horizontal_bar(
            df.groupby(subcat)[sales].sum(),
            "Top Sub-categories by Sales", "Revenue",
            f"charts/{base_name}_subcat.png"))

    # 3. Sales by region (bar)
    if sales and region:
        safe(lambda: _bar_chart(
            df.groupby(region)[sales].sum(),
            "Revenue by Region", "Region", "Revenue",
            f"charts/{base_name}_region.png"))

    # 4. Discount vs Profit (scatter)
    if discount and profit:
        dd = df[[discount, profit]].dropna()
        safe(lambda: _scatter_chart(
            dd[discount], dd[profit],
            "Discount vs Profit", "Discount", "Profit",
            f"charts/{base_name}_dp.png"))

    # 5. Profit share by category (donut)
    if profit and category:
        safe(lambda: _donut_chart(
            df.groupby(category)[profit].sum().abs(),
            "Profit Share by Category",
            f"charts/{base_name}_profit_donut.png"))

    # 6. Monthly sales trend (line + fill)
    if sales and date_col:
        def _monthly():
            tmp = df.copy()
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp = tmp.dropna(subset=[date_col])
            monthly = tmp.groupby(tmp[date_col].dt.to_period("M"))[sales].sum()
            if len(monthly) < 2: return
            _line_chart(monthly, "Monthly Revenue Trend", "Revenue",
                        f"charts/{base_name}_trend.png")
        safe(_monthly)

    print(f"✓  {file_name} done")


if __name__ == "__main__":
    import sys
    run_analysis(sys.argv[1])
