import pandas as pd
import re
import os
from typing import List, Dict, Optional

# ---- 欄位 ----
COLUMN_ALIASES: Dict[str, List[str]] = {
    "客戶編號": ["客戶編號", "編號", "ID", "Id", "id", "cust_id", "customer_id", "客編"],
    "名字": ["名字", "姓名", "客戶姓名", "name", "Name"],
    "電話": ["電話", "連絡電話", "手機", "phone", "Phone", "mobile", "Mobile"],
    "地址": ["地址", "住址", "address", "Address"],
    "備註": ["備註", "備考", "備註欄", "note", "Note", "remark", "Remark", "memo", "Memo", "comments"],
}

def normalize_phone(s: str) -> str:
    """將非數字移除，用於電話比對"""
    if pd.isna(s):
        return ""
    return re.sub(r"\D+", "", str(s))

def build_column_map(df: pd.DataFrame) -> Dict[str, str]:
    """建立標準欄位名到實際欄位名的映射"""
    mapping = {}
    cols = [c.strip() for c in df.columns]
    for std, aliases in COLUMN_ALIASES.items():
        for c in cols:
            if c in aliases:
                mapping[std] = c
                break
    return mapping

def read_any(path: str) -> pd.DataFrame:
    """讀取 XLSX 或 CSV 檔案，並處理 CSV 編碼問題"""
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path, dtype=str).fillna("")
    elif ext == ".csv":
        # 嘗試常見編碼
        for enc in ["utf-8-sig", "cp950", "utf-8"]:
            try:
                return pd.read_csv(path, encoding=enc, dtype=str).fillna("")
            except Exception:
                pass
        raise ValueError("CSV 無法用常見編碼讀取（UTF-8/Big5），請改存 UTF-8 再試。")
    else:
        raise ValueError("只支援 .xlsx/.xls/.csv 檔案。")

class ClientDB:
    def __init__(self, path: str):
        self.path = path
        self.df = read_any(path)
        self.colmap = build_column_map(self.df)
        
        # 建議的顯示欄位順序
        self.display_cols: List[str] = []
        for std in ["客戶編號", "名字", "電話", "地址", "備註"]:
            if std in self.colmap:
                self.display_cols.append(self.colmap[std])
        if not self.display_cols:
            self.display_cols = list(self.df.columns)

    #模糊搜尋
    def search(self, q_words: List[str], columns: Optional[List[str]]=None, use_or:bool=False) -> pd.DataFrame:
        if not q_words or self.df.empty:
            return self.df.copy()

        columns = columns or list(self.df.columns)
        phone_col = self.colmap.get("電話")
        
        combined_mask = pd.Series([not use_or] * len(self.df))

        for w in q_words:
            w = w.strip().lower()
            if not w: continue
                
            word_mask = pd.Series([False] * len(self.df))

            # 1. 搜尋
            for col in columns:
                if col in self.df.columns:
                    word_mask = word_mask | self.df[col].astype(str).str.lower().str.contains(w, na=False)

            # 2. 電話數字比對
            if phone_col and w.isdigit() and phone_col in columns:
                phone_digits = self.df[phone_col].apply(normalize_phone)
                phone_mask = phone_digits.str.contains(w, na=False)
                word_mask = word_mask | phone_mask

            if use_or:
                combined_mask = combined_mask | word_mask
            else:
                combined_mask = combined_mask & word_mask
                
        if not any(w.strip() for w in q_words):
             return self.df.copy()

        return self.df[combined_mask].copy()

    #用索引更新整列資料
    def edit_row(self, index: int, data: Dict[str, str]) -> bool:
        if index in self.df.index:
            for k, v in data.items():
                if k in self.df.columns:
                    self.df.loc[index, k] = v
            return True
        return False
        
    def add_row(self, data: Dict[str, str]):
        """新增一列資料"""
        new_row = pd.Series({c: data.get(c, '') for c in self.df.columns}, index=self.df.columns)
        self.df.loc[len(self.df)] = new_row
        self.df = self.df.reset_index(drop=True)

    def delete_rows(self, indices: List[int]) -> int:
        """刪除指定的索引列"""
        before = len(self.df)
        self.df = self.df.drop(index=indices, errors='ignore').reset_index(drop=True)
        return before - len(self.df)

    def save(self, path: Optional[str]=None) -> str:
        """儲存 DataFrame 到指定路徑 (預設覆寫原檔)"""
        path = path or self.path
        ext = os.path.splitext(path)[1].lower()
        if ext == ".xlsx" or ext == ".xls":
            self.df.to_excel(path, index=False)
        else:
            self.df.to_csv(path, index=False, encoding="utf-8-sig")
        return path