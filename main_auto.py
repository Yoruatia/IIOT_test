"""
main_auto.py

Mode 2: Smart Auto-Sort
Menerima argumen: --image <path_to_image>
Contoh: python main_auto.py --image target.png
"""

import cv2
import numpy as np
import argparse
import sys
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


def load_target_image(image_path):
    """
    Load gambar target dan konversi ke grid 4x4
    
    Returns: dict {(col,row): color_value} atau None jika error
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"[ERROR] Tidak bisa membaca gambar: {image_path}")
            return None
        
        print(f"[INFO] Gambar loaded: {image_path}")
        print(f"[INFO] Ukuran: {img.shape}")
        
        # Resize ke 4x4 untuk simplicity
        resized = cv2.resize(img, (4, 4), interpolation=cv2.INTER_AREA)
        
        # Analisis warna setiap cell
        # Untuk sekarang: simpel dominance color detection
        grid_data = {}
        for row in range(4):
            for col in range(4):
                # Extract pixel warna
                pixel = resized[row, col]
                
                # Detect warna dominan (BGR format)
                b, g, r = pixel[0], pixel[1], pixel[2]
                
                # Determine color
                if r > 100 and g < 100 and b < 100:
                    color = "merah"
                elif r < 100 and g > 100 and b < 100:
                    color = "hijau"
                elif r < 100 and g < 100 and b > 100:
                    color = "biru"
                elif r > 100 and g > 100 and b < 100:
                    color = "kuning"
                else:
                    color = "unknown"
                
                grid_data[(col+1, row+1)] = color
                print(f"  Grid ({col+1},{row+1}): {color}")
        
        return grid_data
        
    except Exception as e:
        print(f"[ERROR] Gagal process gambar: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Dobot Auto-Sort")
    parser.add_argument("--image", type=str, required=True,
                       help="Path ke file gambar target 4x4")
    
    args = parser.parse_args()
    image_path = args.image
    
    print(f"[INFO] Mode 2: Auto-Sort dengan target: {image_path}")
    
    # Load target image
    grid_target = load_target_image(image_path)
    if not grid_target:
        return False
    
    # Inisialisasi hardware
    device = init_dobot()
    if device is None:
        return False
    
    # Inisialisasi coordinate system
    coord_sys = CoordinateSystem()
    coord_sys.print_system_info()
    
    # Calibrate
    home_pos = CustomPosition(x=0, y=0, z=0, r=0)
    coord_sys.calibrate(home_pos)
    
    try:
        print("\n[PROCESS] Mulai arrange grid sesuai target...")
        
        # Untuk setiap grid position, execute
        for (col, row), color in grid_target.items():
            print(f"\n  Menjalankan Grid ({col},{row}) - Target: {color}")
            execute_drop(device, col, row, coord_sys)
        
        print(f"\n[SUCCESS] Auto-Sort selesai!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Gagal execute auto-sort: {e}")
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

    # Mapping Tugas: Posisi -> Warna Target
    task_list = {
        "A": sys.argv[1],
        "B": sys.argv[2],
        "C": sys.argv[3],
        "D": sys.argv[4]
    }
    
    # Status: False = Belum Selesai, True = Selesai
    task_status = {"A": False, "B": False, "C": False, "D": False}

    print(f"=== MEMULAI MISI ===")
    for pos, color in task_list.items():
        print(f"Posisi {pos} -> Menunggu: {color}")
    print("====================")

    # 2. INISIALISASI HARDWARE
    device = init_dobot()
    if device is None:
        print("[ERROR] Dobot tidak ditemukan.")
        return

    # 3. INISIALISASI COORDINATE SYSTEM
    coord_sys = CoordinateSystem()
    coord_sys.print_system_info()
    
    # Calibrate ke home (0,0,0) - assuming arm sudah di-home
    from pydobotplus import CustomPosition
    home_pos = CustomPosition(x=0, y=0, z=0, r=0)
    coord_sys.calibrate(home_pos)
    
    # 4. VALIDASI GRID POSITION
    if grid_position not in coord_sys.grid_positions:
        print(f"[ERROR] Grid '{grid_position}' tidak valid!")
        print(f"[INFO] Grid yang tersedia: {list(coord_sys.grid_positions.keys())}")
        return
    
    print(f"\n[READY] Siap execute drop ke Grid {grid_position}")
    
    try:
        # Execute drop ke grid position
        execute_drop(device, grid_position, coord_sys)
        print(f"\n[SUCCESS] Drop ke Grid {grid_position} selesai!")
        
    except Exception as e:
        print(f"[ERROR] Gagal execute drop: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if device:
            device.close()
            print("[INFO] Dobot disconnected")

if __name__ == "__main__":
    main()
