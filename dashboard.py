import tkinter as tk
from tkinter import filedialog, ttk
import os
import shutil
import pandas as pd
from PIL import Image, ImageTk
import zipfile
import threading

from ecommerce_analysis import run_analysis

#  PALETTE
BG          = "#0F0F12"      # page background
CARD        = "#1C1C22"      # card surface  — visibly different from BG
ELEMENT     = "#26262E"      # inputs / list rows
HOVER       = "#32323C"      # hover state

BORDER      = "#3A3A46"      # default border
BORDER_HI   = "#55556A"      # focused / hover border

TXT         = "#F2F2F4"      # primary text
TXT_2       = "#9898A6"      # secondary
TXT_3       = "#55555F"      # muted / placeholder

GREEN       = "#12B981"      # primary action
GREEN_HO    = "#0EA271"      # hover
GREEN_BG    = "#0A2B1E"      # muted green background
GREEN_LT    = "#6EDDB4"      # light green text

FONT        = "Segoe UI"
F_HEAD      = (FONT, 22, "bold")
F_SUB       = (FONT, 10)
F_LABEL     = (FONT, 8, "bold")
F_BODY      = (FONT, 9)
F_SMALL     = (FONT, 8)
F_MONO      = ("Consolas", 8)

selected_files = []
current_image  = None
current_df     = None


#  HELPER WIDGETS
class FlatListbox(tk.Frame):
    def __init__(self, parent, height=5, **kw):
        super().__init__(parent, bg=ELEMENT,
                         highlightthickness=1, highlightbackground=BORDER)
        self._lb = tk.Listbox(self, bg=ELEMENT, fg=TXT,
            selectbackground=GREEN_BG, selectforeground=GREEN_LT,
            activestyle="none", relief="flat", bd=0,
            highlightthickness=0, font=F_BODY, height=height)
        sb = tk.Scrollbar(self, orient="vertical", command=self._lb.yview,
                          bg=ELEMENT, troughcolor=ELEMENT,
                          relief="flat", bd=0, width=5)
        self._lb.config(yscrollcommand=sb.set)
        self._lb.pack(side="left", fill="both", expand=True, padx=2)
        sb.pack(side="right", fill="y")
        self._lb.bind("<Enter>", lambda e: self.config(highlightbackground=BORDER_HI))
        self._lb.bind("<Leave>", lambda e: self.config(highlightbackground=BORDER))

    def insert(self, i, v): self._lb.insert(i, v)
    def delete(self, *a):   self._lb.delete(*a)
    def curselection(self): return self._lb.curselection()
    def get(self, i):       return self._lb.get(i)
    def bind(self, s, f):   self._lb.bind(s, f)


class Btn(tk.Frame):
    """Simple solid button — always rendered, always clickable."""
    def __init__(self, parent, text, cmd=None,
                 bg=GREEN, fg="#fff", fsize=10, py=10, **kw):
        super().__init__(parent, bg=bg, cursor="hand2")
        self._bg  = bg
        self._hbg = GREEN_HO if bg == GREEN else HOVER
        self._cmd = cmd
        self._lbl = tk.Label(self, text=text, bg=bg, fg=fg,
                              font=(FONT, fsize, "bold"), pady=py)
        self._lbl.pack(fill="both", expand=True)
        for w in (self, self._lbl):
            w.bind("<Enter>",           lambda e: self._set(self._hbg))
            w.bind("<Leave>",           lambda e: self._set(self._bg))
            w.bind("<ButtonRelease-1>", lambda e: self._cmd() if self._cmd else None)

    def _set(self, c):
        self.config(bg=c); self._lbl.config(bg=c)


class GhostBtn(tk.Frame):
    def __init__(self, parent, text, cmd=None, **kw):
        super().__init__(parent, bg=CARD,
                         highlightthickness=1, highlightbackground=BORDER,
                         cursor="hand2")
        self._cmd = cmd
        self._lbl = tk.Label(self, text=text, bg=CARD, fg=TXT_2,
                              font=(FONT, 9), padx=14, pady=7)
        self._lbl.pack()
        for w in (self, self._lbl):
            w.bind("<Enter>",           self._on)
            w.bind("<Leave>",           self._off)
            w.bind("<ButtonRelease-1>", lambda e: self._cmd() if self._cmd else None)

    def _on(self, _):
        self.config(highlightbackground=GREEN, bg=GREEN_BG)
        self._lbl.config(bg=GREEN_BG, fg=GREEN_LT)
    def _off(self, _):
        self.config(highlightbackground=BORDER, bg=CARD)
        self._lbl.config(bg=CARD, fg=TXT_2)


class Spinner(tk.Canvas):
    def __init__(self, parent, size=40, bg=BG, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0)
        self._s = size; self._a = 0; self._on = False

    def start(self): self._on = True;  self._tick()
    def stop(self):  self._on = False; self.delete("all")

    def _tick(self):
        if not self._on: return
        self.delete("all")
        p = 5
        self.create_arc(p, p, self._s-p, self._s-p,
                        start=0, extent=359,
                        outline=BORDER, width=3, style="arc")
        self.create_arc(p, p, self._s-p, self._s-p,
                        start=self._a, extent=250,
                        outline=GREEN, width=3, style="arc")
        self._a = (self._a + 8) % 360
        self.after(22, self._tick)



#  LOGIC
def select_files():
    files = filedialog.askopenfilenames(filetypes=[("CSV Files", "*.csv")])
    for f in files:
        name = os.path.basename(f)
        dest = os.path.abspath(f"Data/raw/{name}")
        src  = os.path.abspath(f)
        os.makedirs("Data/raw", exist_ok=True)
        if src != dest:
            shutil.copy(f, dest)
        if dest not in selected_files:
            selected_files.append(dest)
            upload_lb.insert(tk.END, f"  {name}")
    if selected_files:
        n = len(selected_files)
        count_lbl.config(
            text=f"  ✓  {n} file{'s' if n!=1 else ''} selected",
            fg=GREEN_LT)
        run_btn.pack(fill="x", pady=(8, 0))


def go_to_dashboard():
    if not selected_files:
        return
    opening_frame.pack_forget()
    dashboard_frame.pack(fill="both", expand=True)
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay.lift()
    spin.start()
    threading.Thread(target=_work, daemon=True).start()


def _work():
    for f in selected_files:
        run_analysis(f)
    root.after(0, _done)


def _done():
    spin.stop()
    overlay.place_forget()
    for f in selected_files:
        raw_lb.insert(tk.END, f"  {os.path.basename(f)}")
    _load_lists()


def _load_lists():
    clean_lb.delete(0, tk.END)
    chart_lb.delete(0, tk.END)
    if os.path.exists("Data/cleaned"):
        for f in sorted(os.listdir("Data/cleaned")):
            clean_lb.insert(tk.END, f"  {f}")


def _load_charts(name):
    chart_lb.delete(0, tk.END)
    base = os.path.splitext(name.strip())[0]
    if os.path.exists("charts"):
        for f in sorted(os.listdir("charts")):
            if f.startswith(base):
                chart_lb.insert(tk.END, f"  {f}")


def _insights(df):
    out = [
        f"Rows        {df.shape[0]:,}",
        f"Columns     {df.shape[1]}",
        "─" * 22
    ]

    # detect columns
    sales = next((c for c in df.columns if "sales" in c or "revenue" in c), None)
    profit = next((c for c in df.columns if "profit" in c), None)
    discount = next((c for c in df.columns if "discount" in c), None)
    category = next((c for c in df.columns if "category" in c), None)
    region = next((c for c in df.columns if "region" in c), None)

    # basic stats
    if sales:
        out.append(f"Total Sales   {df[sales].sum():,.2f}")
    if profit:
        out.append(f"Avg Profit    {df[profit].mean():,.2f}")
    if discount:
        out.append(f"Avg Discount  {df[discount].mean():,.2f}")

    out.append("─" * 22)

    # REAL INSIGHTS
    try:
        if category and sales:
            top_cat = df.groupby(category)[sales].sum().idxmax()
            out.append(f"Top Category → {top_cat}")

        if region and sales:
            top_region = df.groupby(region)[sales].sum().idxmax()
            out.append(f"Top Region   → {top_region}")

        if discount and profit:
            corr = df[[discount, profit]].corr().iloc[0, 1]
            if corr < -0.2:
                out.append("Insight → High discount reduces profit")
            elif corr > 0.2:
                out.append("Insight → Discount boosts profit")
    except:
        pass

    return "\n".join(out)


def on_clean_select(event):
    global current_df
    sel = clean_lb.curselection()
    if not sel: return
    name = clean_lb.get(sel[0]).strip()
    try:
        current_df = pd.read_csv(f"Data/cleaned/{name}", encoding="latin1")
    except Exception:
        return
    # populate tree
    tree.delete(*tree.get_children())
    tree["columns"] = list(current_df.columns)
    tree["show"]    = "headings"
    for col in current_df.columns:
        tree.heading(col, text=col, anchor="w")
        tree.column(col, width=120, minwidth=80, stretch=False)
    for _, row in current_df.iterrows():
        tree.insert("", "end", values=list(row))
    # insights
    ins_txt.config(state="normal")
    ins_txt.delete("1.0", "end")
    ins_txt.insert("end", _insights(current_df))
    ins_txt.config(state="disabled")
    _load_charts(name)


def on_chart_select(event):
    global current_image
    sel = chart_lb.curselection()
    if not sel: return
    name = chart_lb.get(sel[0]).strip()
    try:
        img = Image.open(f"charts/{name}")
    except Exception:
        return
    root.update_idletasks()
    w = chart_area.winfo_width()
    h = chart_area.winfo_height()
    if w > 10 and h > 10:
        img = img.copy()
        img.thumbnail((w, h), Image.LANCZOS)
    current_image = ImageTk.PhotoImage(img)
    chart_lbl.config(image=current_image)
    chart_lbl.image = current_image
    chart_lbl.config(cursor="hand2")


def download_zip():
    path = filedialog.asksaveasfilename(
        defaultextension=".zip", filetypes=[("ZIP file", "*.zip")])
    if not path: return
    with zipfile.ZipFile(path, "w") as zf:
        if os.path.exists("Data/cleaned"):
            for f in os.listdir("Data/cleaned"):
                base = os.path.splitext(f)[0]
                zf.write(f"Data/cleaned/{f}", f"{base}/{f}")
                if os.path.exists("charts"):
                    for c in os.listdir("charts"):
                        if c.startswith(base):
                            zf.write(f"charts/{c}", f"{base}/{c}")

def open_full_chart(event=None):
    sel = chart_lb.curselection()
    if not sel:
        return

    name = chart_lb.get(sel[0]).strip()

    try:
        img = Image.open(f"charts/{name}")
    except:
        return

    top = tk.Toplevel(root)
    top.title(name)
    top.configure(bg=BG)
    top.geometry("900x600")

    img = img.copy()
    img.thumbnail((900, 600), Image.LANCZOS)

    photo = ImageTk.PhotoImage(img)
    lbl = tk.Label(top, image=photo, bg=BG)
    lbl.image = photo
    lbl.pack(expand=True)


#  ROOT
root = tk.Tk()
root.title("E-commerce Analytics")
root.geometry("1340x780")
root.minsize(960, 600)
root.configure(bg=BG)

# TTK dark style
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview",
    background=CARD, foreground=TXT, fieldbackground=CARD,
    rowheight=26, font=F_MONO, borderwidth=0, relief="flat")
style.configure("Treeview.Heading",
    background=ELEMENT, foreground=TXT_2,
    font=(FONT, 8, "bold"), borderwidth=0, relief="flat", padding=(8, 6))
style.map("Treeview",
    background=[("selected", GREEN_BG)],
    foreground=[("selected", GREEN_LT)])
for orient in ("Vertical", "Horizontal"):
    style.configure(f"{orient}.TScrollbar",
        background=ELEMENT, troughcolor=CARD,
        arrowcolor=BORDER_HI, relief="flat", borderwidth=0, width=7)
    style.map(f"{orient}.TScrollbar", background=[("active", BORDER_HI)])


#  OPENING SCREEN
#  Layout: topbar (fixed) → big centre frame (expands)
#  Inside centre frame: everything just pack()'s naturally
opening_frame = tk.Frame(root, bg=BG)
opening_frame.pack(fill="both", expand=True)

# ── Topbar 
topbar = tk.Frame(opening_frame, bg=CARD, height=52)
topbar.pack(fill="x")
topbar.pack_propagate(False)
tk.Label(topbar, text="●", font=(FONT, 10), fg=GREEN, bg=CARD
         ).pack(side="left", padx=(18, 4), pady=14)
tk.Label(topbar, text="E-commerce Analytics",
         font=(FONT, 11, "bold"), fg=TXT, bg=CARD
         ).pack(side="left", pady=14)
tk.Label(topbar, text="  v1.0", font=F_SMALL, fg=TXT_3, bg=CARD
         ).pack(side="left", pady=14)
tk.Frame(opening_frame, bg=BORDER, height=1).pack(fill="x")

# ── Centre area — uses a single Frame that just packs ───
centre = tk.Frame(opening_frame, bg=BG)
centre.pack(fill="both", expand=True)

# Everything inside centre is just packed — zero place() calls
# Vertical rhythm: top pad → badge → headline → sub → card → footer

tk.Frame(centre, bg=BG, height=60).pack()   # top spacer

# Badge
badge = tk.Frame(centre, bg=GREEN_BG,
                  highlightthickness=1, highlightbackground=GREEN)
badge.pack()
tk.Label(badge, text="  ↑  CSV Analytics Platform  ",
         font=(FONT, 9, "bold"), fg=GREEN_LT, bg=GREEN_BG,
         padx=6, pady=5).pack()

tk.Frame(centre, bg=BG, height=18).pack()  # gap

# Headline
tk.Label(centre, text="Turn your CSV data into insights",
         font=(FONT, 24, "bold"), fg=TXT, bg=BG).pack()

tk.Frame(centre, bg=BG, height=10).pack()

tk.Label(centre,
         text="Upload one or more CSV files — we'll clean, analyse,\nand generate charts automatically.",
         font=(FONT, 10), fg=TXT_2, bg=BG, justify="center").pack()

tk.Frame(centre, bg=BG, height=28).pack()

# ── Upload card 
# Card is a plain Frame with a clearly visible border
card = tk.Frame(centre, bg=CARD,
                highlightthickness=1, highlightbackground=BORDER)
card.pack()   # natural width — no pack_propagate(False) here

inner = tk.Frame(card, bg=CARD, width=480)
inner.pack(padx=28, pady=24)
inner.pack_propagate(False)
inner.config(height=220)   # fix width only; height grows with content

# File list
list_frame = tk.Frame(inner, bg=ELEMENT,
                       highlightthickness=1, highlightbackground=BORDER)
list_frame.pack(fill="x")

upload_lb = tk.Listbox(list_frame, bg=ELEMENT, fg=TXT,
    selectbackground=GREEN_BG, selectforeground=GREEN_LT,
    activestyle="none", relief="flat", bd=0,
    highlightthickness=0, font=F_BODY, height=4)
upload_lb.pack(fill="x", padx=8, pady=8)

# Count line
count_lbl = tk.Label(inner, text="  No files selected yet",
                      font=F_SMALL, fg=TXT_3, bg=CARD, anchor="w")
count_lbl.pack(fill="x", pady=(10, 14))

# Choose Files — always visible
Btn(inner, "＋  Choose CSV Files", cmd=select_files,
    bg=GREEN, fg="#fff", fsize=10, py=11).pack(fill="x")

# Run Analysis — hidden until files are chosen, packed below choose btn
run_btn = Btn(inner, "Run Analysis  →", cmd=go_to_dashboard,
              bg=ELEMENT, fg=TXT_2, fsize=10, py=11)
run_btn._hbg = HOVER

tk.Frame(centre, bg=BG, height=14).pack()

# Footer note
tk.Label(centre,
         text="Supports multiple files  ·  sales, profit, category & region auto-detected",
         font=F_SMALL, fg=TXT_3, bg=BG).pack()



#  DASHBOARD FRAME
dashboard_frame = tk.Frame(root, bg=BG)

dashboard_frame.rowconfigure(0, weight=0)
dashboard_frame.rowconfigure(1, weight=0)
dashboard_frame.rowconfigure(2, weight=1)
dashboard_frame.columnconfigure(0, weight=1)

# Topbar
dash_nav = tk.Frame(dashboard_frame, bg=CARD, height=52)
dash_nav.grid(row=0, column=0, sticky="ew")
dash_nav.grid_propagate(False)
dn_left = tk.Frame(dash_nav, bg=CARD)
dn_left.pack(side="left", fill="y", padx=18)
tk.Label(dn_left, text="●", font=(FONT, 10), fg=GREEN, bg=CARD
         ).pack(side="left", pady=14)
tk.Label(dn_left, text="  E-commerce Analytics",
         font=(FONT, 11, "bold"), fg=TXT, bg=CARD
         ).pack(side="left", pady=14)
GhostBtn(dash_nav, "↓  Export ZIP", cmd=download_zip
         ).pack(side="right", padx=16, pady=10)
tk.Frame(dashboard_frame, bg=BORDER, height=1).grid(
    row=0, column=0, sticky="sew")

# Top panel: 4 equal columns
top_panel = tk.Frame(dashboard_frame, bg=BG, height=220)
top_panel.grid(row=1, column=0, sticky="nsew")
top_panel.grid_propagate(False)
for i in range(4): top_panel.columnconfigure(i, weight=1)
top_panel.rowconfigure(1, weight=1)


def _col(parent, col, title):
    f = tk.Frame(parent, bg=BG)
    f.grid(row=0, column=col, rowspan=2, sticky="nsew",
           padx=(12 if col == 0 else 6, 6), pady=12)
    tk.Label(f, text=title, font=F_LABEL, fg=TXT, bg=BG, anchor="w"
             ).pack(fill="x", pady=(0, 6))
    lb = FlatListbox(f, height=6)
    lb.pack(fill="both", expand=True)
    return lb


raw_lb   = _col(top_panel, 0, "RAW FILES")
clean_lb = _col(top_panel, 1, "CLEANED FILES")
chart_lb = _col(top_panel, 2, "CHARTS")

# Insights column
ins_col = tk.Frame(top_panel, bg=BG)
ins_col.grid(row=0, column=3, rowspan=2, sticky="nsew",
             padx=(6, 12), pady=12)
tk.Label(ins_col, text="INSIGHTS", font=F_LABEL, fg=TXT_3, bg=BG, anchor="w"
         ).pack(fill="x", pady=(0, 6))
ins_box = tk.Frame(ins_col, bg=ELEMENT,
                   highlightthickness=1, highlightbackground=BORDER)
ins_box.pack(fill="both", expand=True)
ins_txt = tk.Text(ins_box, bg=ELEMENT, fg=GREEN_LT,
                  font=(FONT, 9), relief="flat", bd=0,
                  highlightthickness=0, padx=12, pady=10,
                  state="disabled", wrap="word")
ins_txt.pack(fill="both", expand=True)

tk.Frame(dashboard_frame, bg=BORDER, height=1).grid(
    row=1, column=0, sticky="sew")

# Bottom panel: strict 50/50
bot = tk.Frame(dashboard_frame, bg=BG)
bot.grid(row=2, column=0, sticky="nsew")
bot.columnconfigure(0, weight=1, uniform="half")
bot.columnconfigure(1, weight=1, uniform="half")
bot.rowconfigure(0, weight=1)


def _panel(parent, col, title):
    c = tk.Frame(parent, bg=CARD,
                 highlightthickness=1, highlightbackground=BORDER)
    c.grid(row=0, column=col, sticky="nsew",
           padx=(12 if col==0 else 6, 6 if col==0 else 12), pady=12)
    c.grid_propagate(False)
    c.rowconfigure(1, weight=1)
    c.columnconfigure(0, weight=1)
    h = tk.Frame(c, bg=CARD)
    h.grid(row=0, column=0, columnspan=2, sticky="ew")
    tk.Label(h, text=title, font=F_LABEL, fg=TXT_2, bg=CARD,
             padx=14, pady=10, anchor="w").pack(side="left")
    tk.Frame(c, bg=BORDER, height=1).grid(row=0, column=0,
             columnspan=2, sticky="sew")
    return c


# Data preview
lc = _panel(bot, 0, "DATA PREVIEW")
tree = ttk.Treeview(lc, selectmode="browse")
tree.grid(row=1, column=0, sticky="nsew")
sy = ttk.Scrollbar(lc, orient="vertical",   command=tree.yview)
sy.grid(row=1, column=1, sticky="ns")
sx = ttk.Scrollbar(lc, orient="horizontal", command=tree.xview)
sx.grid(row=2, column=0, sticky="ew", columnspan=2)
tree.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)

# Chart viewer
rc = _panel(bot, 1, "CHART VIEWER")
chart_area = tk.Frame(rc, bg=CARD)
chart_area.grid(row=1, column=0, sticky="nsew")
chart_area.rowconfigure(0, weight=1)
chart_area.columnconfigure(0, weight=1)
chart_lbl = tk.Label(chart_area, bg=CARD)
chart_lbl.grid(row=0, column=0)

# Loading overlay
overlay = tk.Frame(dashboard_frame, bg=BG)
_oc = tk.Frame(overlay, bg=BG)
_oc.place(relx=0.5, rely=0.5, anchor="center")
spin = Spinner(_oc, size=44, bg=BG)
spin.pack()
tk.Label(_oc, text="Analysing your data…",
         font=(FONT, 11), fg=TXT_2, bg=BG).pack(pady=(12, 0))

# Treeview striping
tree.tag_configure("even", background=CARD)
tree.tag_configure("odd",  background=ELEMENT)
tree.bind("<Configure>", lambda e: [
    tree.item(iid, tags=("odd" if i%2 else "even",))
    for i, iid in enumerate(tree.get_children())])

# Events
clean_lb.bind("<<ListboxSelect>>", on_clean_select)
chart_lb.bind("<<ListboxSelect>>",  on_chart_select)
chart_lb.bind("<Double-Button-1>", open_full_chart)

root.mainloop()
