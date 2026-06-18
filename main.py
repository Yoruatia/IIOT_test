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
from utility2 import CoordinateSystem, execute_drop

def init_dobot():
    """Inisialisasi koneksi Dobot"""
    try:
        available_ports = list_ports.comports()
        if not available_ports:
            print("[ERROR] Tidak ada port serial ditemukan.")
            return None
        
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
    
    # Validasi
    if col < 1 or col > 4 or row < 1 or row > 4:
        print(f"[ERROR] Grid ({col},{row}) tidak valid. Gunakan col,row dalam range 1-4.")
        return False
    
    print(f"[INFO] Mode 1: Manual Control ke Grid ({col},{row})")
    
    # Inisialisasi hardware
    device = init_dobot()
    if device is None:
        return False
    
    # Inisialisasi coordinate system
    coord_sys = CoordinateSystem()
    coord_sys.print_system_info()
    
    # Calibrate (assuming arm sudah di home)
    home_pos = CustomPosition(x=0, y=0, z=0, r=0)
    coord_sys.calibrate(home_pos)
    
    try:
        # Execute drop ke grid position
        execute_drop(device, col, row, coord_sys)
        print(f"\n[SUCCESS] Drop ke Grid ({col},{row}) selesai!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Gagal execute drop: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if device:
            device.close()
            print("[INFO] Dobot disconnected")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
