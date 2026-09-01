import sys
from pathlib import Path

# Daftarkan folder aplikasi ke daftar pencarian module Python
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from shiny_app import app