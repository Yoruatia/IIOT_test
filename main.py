"""
main.py

Mode 1: Direct Manual Control
Menerima argumen: --manual <col> <row>
Contoh: python main.py --manual 1 1
"""

import sys
import argparse
from serial.tools import list_ports
from pydobotplus import Dobot, CustomPosition
# Mengimpor CoordinateSystem dan fungsi sequence terintegrasi dari utility2
from utility2 import CoordinateSystem, execute_full_sequence

def init_dobot():
    """Inisialisasi koneksi Dobot Magician melalui port serial otomatis"""
    try:
        available_ports = list_ports.comports()
        if not available_ports:
            print("[ERROR] Tidak ada port serial ditemukan.")
            return None
        
        # Memilih port yang tersedia (prioritas port kedua jika ada, jika tidak port pertama)
        port = available_ports[1].device if len(available_ports) > 1 else available_ports[0].device
        print(f"[INFO] Mencoba connect ke Dobot di port: {port}")
        
        device = Dobot(port=port)
        print("[INFO] Dobot connected successfully")
        return device
    except Exception as e:
        print(f"[ERROR] Gagal connect Dobot: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Dobot Manual Control")
    parser.add_argument("--manual", nargs=2, type=int, metavar=("COL", "ROW"),
                        help="Manual control: kolom (1-4) dan row (1-4)")
    
    args = parser.parse_args()
    
    if not args.manual:
        print("[ERROR] Argumen --manual <col> <row> diperlukan")
        return False
    
    col, row = args.manual
    
    # Validasi input koordinat grid matriks
    if col < 1 or col > 4 or row < 1 or row > 4:
        print(f"[ERROR] Grid ({col},{row}) tidak valid. Gunakan col,row dalam range 1-4.")
        return False
    
    print(f"[INFO] Mode 1: Manual Control ke Grid ({col},{row})")
    
    # Inisialisasi perangkat keras lengan robot
    device = init_dobot()
    if device is None:
        return False
    
    # Inisialisasi pengelola sistem koordinat grid 4x4
    coord_sys = CoordinateSystem()
    coord_sys.print_system_info()
    
    # Kalibrasi awal sistem koordinat (asumsi posisi lengan saat ini adalah home awal)
    home_pos = CustomPosition(x=0, y=0, z=0, r=0)
    coord_sys.calibrate(home_pos)
    
    try:
        # Menjalankan urutan kerja penuh (Langkah 1 s.d. 6)
        success = execute_full_sequence(device, col, row, coord_sys)
        if success:
            print(f"\n[SUCCESS] Urutan Misi ke Grid ({col},{row}) selesai!")
            return True
        else:
            print(f"\n[FAILED] Urutan Misi gagal di tengah jalan.")
            return False
        
    except Exception as e:
        print(f"[ERROR] Gagal mengeksekusi sekuens gerakan robot: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Memastikan koneksi ke port komunikasi Dobot ditutup secara aman
        if device:
            try:
                device.close()
                print("[INFO] Dobot disconnected")
            except Exception as e:
                print(f"[WARNING] Gagal menutup port Dobot secara bersih: {e}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
