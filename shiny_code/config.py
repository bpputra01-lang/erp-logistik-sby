import io
import json
import urllib.request
import pandas as pd
import uuid
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. KONFIGURASI UMUM APLIKASI
# ==============================================================================
APP_TITLE = "Logistic Dashboard"
APP_HOST = "127.0.0.1"
APP_PORT = 8000

# ==============================================================================
# 2. KONFIGURASI SUPABASE (2 KONEKSI: BARU & LAMA)
# ==============================================================================
# A. Supabase Baru (Ongkir & User Aktif)
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "sb_publishable_pKXe0FX4YxwNhuqD1saHaw_NORud8cJ"

# B. Supabase Lama (Dari Streamlit untuk 4 Menu Cloud)
SUPABASE_OLD_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_OLD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

# ==============================================================================
# 3. SUPABASE MINI CLIENT (REST API POSTGREST LENGKAP)
# ==============================================================================
class SimpleSupabaseTable:
    def __init__(self, base_url, key, table_name):
        self.url = f"{base_url}/rest/v1/{table_name}"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"  # <-- WAJIB INI AGAR TIDAK DIBLOKIR CLOUDFLARE
        }
        self.params = []
        self.method = "GET"
        self.body = None

    def select(self, columns="*"):
        self.params.append(f"select={columns}")
        return self

    def insert(self, payload):
        self.method = "POST"
        self.body = payload if isinstance(payload, list) else [payload]
        return self

    def update(self, payload):
        self.method = "PATCH"
        self.body = payload
        return self

    def delete(self):
        self.method = "DELETE"
        return self

    def eq(self, column, value):
        self.params.append(f"{column}=eq.{value}")
        return self

    def in_(self, column, values):
        val_str = ",".join(map(str, values))
        self.params.append(f"{column}=in.({val_str})")
        return self

    def order(self, column, desc=False):
        direction = "desc" if desc else "asc"
        self.params.append(f"order={column}.{direction}")
        return self

    def execute(self):
        full_url = self.url
        if self.params:
            full_url += "?" + "&".join(self.params)

        data_bytes = json.dumps(self.body).encode("utf-8") if self.body else None
        req = urllib.request.Request(full_url, data=data_bytes, headers=self.headers, method=self.method)

        # Bypass SSL verification untuk lingkungan Pyodide/Cloud
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                res_data = resp.read().decode("utf-8")
                parsed_data = json.loads(res_data) if res_data else []
                return type("Response", (), {"data": parsed_data})()
        except Exception as e:
            print(f"[Supabase REST Error ({self.method} {full_url})]: {e}")
            return type("Response", (), {"data": []})()
            
class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key

    def table(self, table_name):
        return SimpleSupabaseTable(self.url, self.key, table_name)

# Helper Instance Supabase
def get_supabase() -> SimpleSupabaseClient:
    return SimpleSupabaseClient(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_old() -> SimpleSupabaseClient:
    return SimpleSupabaseClient(SUPABASE_OLD_URL, SUPABASE_OLD_KEY)

# ==============================================================================
# 4. TRACKER USER AKTIF / ONLINE (HEARTBEAT SUPABASE)
# ==============================================================================
def ping_active_user(session_id: str, user_name: str = "Anonymous"):
    """Mengirim sinyal online ke Supabase"""
    try:
        sb = get_supabase()
        now_iso = datetime.now(timezone.utc).isoformat()
        sb.table("active_sessions").in_("session_id", [session_id]).delete().execute()
        sb.table("active_sessions").insert({
            "session_id": session_id,
            "user_name": user_name,
            "last_ping": now_iso
        }).execute()
    except Exception as e:
        print(f"Ping error: {e}")

def remove_active_user(session_id: str):
    """Menghapus session saat user menutup browser"""
    try:
        sb = get_supabase()
        sb.table("active_sessions").in_("session_id", [session_id]).delete().execute()
    except Exception:
        pass

def count_online_users() -> int:
    """Menghitung user yang masih aktif dalam 45 detik terakhir"""
    try:
        sb = get_supabase()
        res = sb.table("active_sessions").select("*").execute()
        data = res.data if hasattr(res, "data") else []
        
        now = datetime.now(timezone.utc)
        active_count = 0
        for row in data:
            ping_str = row.get("last_ping")
            if ping_str:
                ping_time = pd.to_datetime(ping_str).to_pydatetime()
                if ping_time.tzinfo is None:
                    ping_time = ping_time.replace(tzinfo=timezone.utc)
                if (now - ping_time).total_seconds() <= 45:
                    active_count += 1
        return max(1, active_count)
    except Exception:
        return 1

# ==============================================================================
# 5. HELPER UTILITY (PANDAS & PARSER)
# ==============================================================================
def safe_int(val, default=0) -> int:
    try:
        if pd.isna(val) or val is None:
            return default
        cleaned = str(val).replace("Rp", "").replace(".", "").replace(",", "").strip()
        return int(float(cleaned))
    except Exception:
        return default

def load_data_from_info(file_info) -> pd.DataFrame:
    """Membaca file upload dari input file Shiny (CSV atau Excel)"""
    if not file_info or len(file_info) == 0:
        return pd.DataFrame()
    
    path = file_info[0]["datapath"]
    name = str(file_info[0]["name"]).lower()
    
    try:
        if name.endswith('.csv'):
            df = pd.read_csv(path)
            return df if not df.empty else pd.DataFrame()
        else:
            return pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        print(f"Error loading {name}: {e}")
        return pd.DataFrame()

def format_datetime_wib(df: pd.DataFrame, kolom: str, format_tampilan: str = "%d-%m-%Y %H:%M") -> pd.DataFrame:
    """Mengubah format ISO Supabase (UTC) ke waktu Indonesia Barat (WIB)"""
    if df is not None and not df.empty and kolom in df.columns:
        try:
            df = df.copy()
            converted = pd.to_datetime(df[kolom], errors="coerce")
            
            if converted.dt.tz is not None:
                converted = converted.dt.tz_convert("Asia/Jakarta")
            else:
                converted = converted.dt.tz_localize("UTC").dt.tz_convert("Asia/Jakarta")
            
            df[kolom] = converted.dt.strftime(format_tampilan)
        except Exception as e:
            print(f"Error saat memformat tanggal kolom '{kolom}': {e}")
    return df