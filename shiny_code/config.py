import io
import json
import urllib.request
import pandas as pd

# ==============================================================================
# 1. KONFIGURASI UMUM APLIKASI
# ==============================================================================
APP_TITLE = "Logistic Dashboard"
APP_HOST = "127.0.0.1"
APP_PORT = 8000

# ==============================================================================
# 2. KONFIGURASI SUPABASE
# ==============================================================================
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "sb_publishable_pKXe0FX4YxwNhuqD1saHaw_NORud8cJ"

# ==============================================================================
# 3. SUPABASE MINI CLIENT (REST API POSTGREST)
# ==============================================================================
class SimpleSupabaseTable:
    def __init__(self, base_url, key, table_name):
        self.url = f"{base_url}/rest/v1/{table_name}"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
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

    def delete(self):
        self.method = "DELETE"
        return self

    def in_(self, column, values):
        # Format list value ke syntax postgREST: in.(val1,val2)
        val_str = ",".join(map(str, values))
        self.params.append(f"{column}=in.({val_str})")
        return self

    def execute(self):
        full_url = self.url
        if self.params:
            full_url += "?" + "&".join(self.params)

        data_bytes = json.dumps(self.body).encode("utf-8") if self.body else None
        req = urllib.request.Request(full_url, data=data_bytes, headers=self.headers, method=self.method)

        try:
            with urllib.request.urlopen(req) as resp:
                res_data = resp.read().decode("utf-8")
                return type("Response", (), {"data": json.loads(res_data) if res_data else []})()
        except Exception as e:
            print(f"[Supabase REST Error]: {e}")
            return type("Response", (), {"data": []})()

class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key

    def table(self, table_name):
        return SimpleSupabaseTable(self.url, self.key, table_name)

def get_supabase() -> SimpleSupabaseClient:
    return SimpleSupabaseClient(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# 4. HELPER UTILITY (PANDAS & PARSER)
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
    """
    Mengubah format ISO Supabase (UTC) ke waktu Indonesia Barat (WIB).
    Contoh output: 08-07-2026 02:38
    """
    if df is not None and not df.empty and kolom in df.columns:
        try:
            # Gunakan .copy() agar tidak terkena SettingWithCopyWarning
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