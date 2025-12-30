import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import webbrowser
from PIL import Image, ImageTk

# 匯入資料核心
try:
    from searching_main import ClientDB
except ImportError:
    print("錯誤：找不到 searching_main.py 檔案。")
    sys.exit(1)

# 配色
BG_COLOR = "#000000"
SIDEBAR_BG = "#1C1C1E"
CARD_BG = "#2C2C2E"
BLUE = "#0A84FF"
RED = "#FF453A"
GREEN = "#00B327"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY = "#98989D"

# 字體設定
FONT_TITLE = ("Microsoft JhengHei UI", 25, "bold")
FONT_MAIN = ("Microsoft JhengHei UI", 20)
FONT_BOLD = ("Microsoft JhengHei UI", 20, "bold")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def startapp():
    # 自動尋找或選擇檔案
    DEFAULT_FILE = "cust.csv"
    target_file = DEFAULT_FILE
    
    if not os.path.exists(target_file):
        root = tk.Tk(); root.withdraw()
        target_file = filedialog.askopenfilename(filetypes=(("Excel", "*.xlsx"), ("CSV", "*.csv")))
        root.destroy()
    
    if target_file:
        app = ClientApp(target_file)
        app.mainloop()

class ClientApp(ctk.CTk):
    def __init__(self, file_path):
        super().__init__()
        self.title("Client Manager Pro")
        self.geometry("1580x700") # 視窗大小
        
        # 設定整體背景
        self.configure(fg_color=BG_COLOR)

        # 1. 載入資料庫
        self.file_path = file_path
        try:
            self.db = ClientDB(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"載入失敗：{e}")
            self.destroy()
            return

        # 2. 佈局設定：左右分割 (左邊側邊欄，右邊內容)
        self.grid_columnconfigure(1, weight=1) # 右邊內容區自動縮放
        self.grid_rowconfigure(0, weight=1)    # 高度自動填滿

        # 3. 建立介面
        self.create_sidebar()
        self.create_main_area()

        # 4. 載入初始資料
        self.load_data_to_treeview(self.db.df)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, corner_radius=0, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) # 固定寬度不被撐開

        # App 標題
        ctk.CTkLabel(self.sidebar, text="客戶管理系統", font=FONT_TITLE, text_color=TEXT_WHITE).pack(pady=(30, 20), padx=20, anchor="w")

        # --- 搜尋區塊 ---
        ctk.CTkLabel(self.sidebar, text="SEARCH", font=("Arial", 10, "bold"), text_color=TEXT_GRAY).pack(pady=(10, 5), padx=20, anchor="w")
        
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="姓名 / 電話...", 
                                         height=35, corner_radius=10, border_width=0, fg_color="#3A3A3C")
        self.search_entry.pack(fill="x", padx=20, pady=5)
        self.search_entry.bind("<Return>", lambda e: self.run_search())

        ctk.CTkButton(self.sidebar, text="搜尋", command=self.run_search, 
                      fg_color=BLUE, hover_color="#0066CC", height=35, corner_radius=10).pack(fill="x", padx=20, pady=10)

        # --- 功能選單 ---
        ctk.CTkLabel(self.sidebar, text="動作", font=("Arial", 12), text_color=TEXT_GRAY).pack(pady=(20, 5), padx=20, anchor="w")

        def sidebar_btn(text, cmd, color="transparent", text_color=TEXT_WHITE, font=(15)):
            return ctk.CTkButton(self.sidebar, text=text, command=cmd, fg_color=color, hover_color="#3A3A3C", anchor="w", text_color=text_color, height=40, corner_radius=8)

        sidebar_btn("新增客戶", lambda: self.open_add_edit_window()).pack(fill="x", padx=10, pady=2)
        sidebar_btn("清除搜尋", self.run_reset).pack(fill="x", padx=10, pady=2)
        
        # 分隔線
        ctk.CTkLabel(self.sidebar, text="檔案編輯", font=("Arial", 12), text_color=TEXT_GRAY).pack(pady=(20, 5), padx=20, anchor="w")
        sidebar_btn("儲存至檔案", self.run_save, text_color=GREEN).pack(fill="x", padx=10, pady=2)
        sidebar_btn("刪除選取", self.run_delete, text_color=RED).pack(fill="x", padx=10, pady=2)

        # 分隔線
        ctk.CTkLabel(self.sidebar, text="其它...", font=("Arial", 12), text_color=TEXT_GRAY).pack(pady=(20, 5), padx=20, anchor="w")
        sidebar_btn("如何使用", lambda: webbrowser.open("how2use.html")).pack(fill="x", padx=10, pady=2)

        # 底部資訊
        self.count_label = ctk.CTkLabel(self.sidebar, text="載入中...", text_color=TEXT_GRAY, font=("Arial", 13))
        self.count_label.pack(side="bottom", pady=20)

    def create_main_area(self):
        """右側主要內容區"""
        # 一個Frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # 頂部標題與狀態
        self.status_label = ctk.CTkLabel(self.main_frame, text="All Clients", font=("Microsoft JhengHei UI", 24, "bold"), text_color=TEXT_WHITE)
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # --- 表格區域 ---
        style = ttk.Style()
        style.theme_use("default")
        
        # Treeview 樣式
        style.configure("Treeview", 
                        background=CARD_BG, 
                        foreground=TEXT_WHITE, 
                        fieldbackground=CARD_BG,
                        borderwidth=0,
                        rowheight=40,  
                        font=FONT_MAIN)
        
        # 選中時的顏色
        style.map('Treeview', background=[('selected', BLUE)], foreground=[('selected', 'white')])

        # 表頭樣式
        style.configure("Treeview.Heading", 
                        background=BG_COLOR, 
                        foreground=TEXT_GRAY, 
                        relief="flat",
                        font=("Microsoft JhengHei UI", 12, "bold"))
        style.map("Treeview.Heading", background=[('active', BG_COLOR)])

        # 建立表格容器 (For圓角)
        table_container = ctk.CTkFrame(self.main_frame, fg_color=CARD_BG, corner_radius=15)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)

        # 滾動條 (TCK)
        self.yscroll = ctk.CTkScrollbar(table_container, button_color="#555555")
        self.yscroll.grid(row=0, column=1, sticky="ns", padx=(0, 5), pady=5)

        # Treeview 本體
        self.tree = ttk.Treeview(table_container, show="headings", yscrollcommand=self.yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.yscroll.configure(command=self.tree.yview)
        
        # 綁定雙擊
        self.tree.bind("<Double-1>", self.open_edit_window)

    def load_data_to_treeview(self, df):
        columns = [c for c in self.db.display_cols if c in df.columns]
        self.tree["columns"] = columns
        self.tree.delete(*self.tree.get_children())

        for col in columns:
            self.tree.heading(col, text=col.upper()) # 表頭大寫
            if col in ["備註", "地址"]:
                self.tree.column(col, width=300, anchor="w")
            else:
                self.tree.column(col, width=120, anchor="center")

        # 斑馬紋
        self.tree.tag_configure('odd', background=CARD_BG)
        self.tree.tag_configure('even', background="#333336")

        for index, row in df.iterrows():
            values = [row[col] for col in columns]
            tag = 'even' if index % 2 == 0 else 'odd'
            self.tree.insert("", "end", iid=index, values=values, tags=(tag,))
        
        self.count_label.configure(text=f"Total: {len(df)} 筆資料")

    # --- 邏輯區 ---
    def run_search(self):
        query = self.search_entry.get().strip()
        q_words = query.split()
        try:
            results = self.db.search(q_words)
            self.load_data_to_treeview(results)
            self.status_label.configure(text=f"Search: '{query}'")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_reset(self):
        self.search_entry.delete(0, "end")
        self.load_data_to_treeview(self.db.df)
        self.status_label.configure(text="All Clients")

    def run_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請先選擇要刪除的資料")
            return
        if not messagebox.askyesno("Delete", f"確定刪除選取的 {len(selected)} 筆資料？"): return
        try:
            indices = [int(item) for item in selected]
            self.db.delete_rows(indices)
            self.run_search()
        except Exception as e: messagebox.showerror("Error", str(e))

    def run_save(self):
        try:
            self.db.save()
            messagebox.showinfo("Saved", "儲存成功！")
        except Exception as e: messagebox.showerror("Error", str(e))

    def open_add_edit_window(self, edit_index=None):
        is_edit = edit_index is not None
        win = ctk.CTkToplevel(self)
        win.title("Edit" if is_edit else "New Client")
        win.geometry("500x600")
        win.configure(fg_color=BG_COLOR)
        win.attributes("-topmost", True)

        # 標題
        ctk.CTkLabel(win, text="客戶資料", font=FONT_TITLE, text_color=TEXT_WHITE).pack(pady=20)

        form = ctk.CTkFrame(win, fg_color=CARD_BG, corner_radius=15)
        form.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        initial_data = self.db.df.loc[edit_index].to_dict() if is_edit else {}
        entry_vars = {}

        for i, col in enumerate(self.db.display_cols):
            row_frame = ctk.CTkFrame(form, fg_color="transparent")
            row_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(row_frame, text=col, font=FONT_BOLD, text_color=TEXT_GRAY, width=80, anchor="w").pack(side="left")
            
            var = tk.StringVar(value=str(initial_data.get(col, "")))
            entry = ctk.CTkEntry(row_frame, textvariable=var, height=35, border_width=0, fg_color="#3A3A3C", text_color="white")
            entry.pack(side="right", fill="x", expand=True)
            
            entry_vars[col] = var
            if is_edit and col == self.db.colmap.get("客戶編號"): 
                entry.configure(state="disabled", text_color="gray")

        def save():
            data = {k: v.get() for k, v in entry_vars.items()}
            try:
                if is_edit: self.db.edit_row(edit_index, data)
                else: self.db.add_row(data)
                self.run_search()
                win.destroy()
            except Exception as e: messagebox.showerror("Error", str(e))

        ctk.CTkButton(win, text="儲存資料", command=save, fg_color=BLUE, height=45, font=FONT_BOLD).pack(pady=20, padx=20, fill="x")

    def open_edit_window(self, event):
        sel = self.tree.selection()
        if len(sel) == 1: self.open_add_edit_window(int(sel[0]))

#-----------------------------------------------------------------

if __name__ == "__main__":
    startapp()