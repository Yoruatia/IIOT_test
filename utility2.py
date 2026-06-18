"""
Dobot Magician Coordinate System Manager + Movement Functions
=============================================================

Sistem koordinat Dobot Magician dengan karakteristik khusus:
- Sumbu X: TETAP (depan-belakang)
- Sumbu Y: RELATIF terhadap home calibration (kiri-kanan)
- Sumbu Z: Ketinggian (vertikal)

Drop Zone: Papan catur 4x2 (4 baris × 2 kolom = 8 titik)
- X: 2 posisi [51 (ujung A), -16 (ujung B)]
- Y: 4 posisi dengan spacing 20mm
"""

from pydobotplus import Dobot, CustomPosition
from time import sleep
from enum import Enum

class PositionType(Enum):
    """Tipe posisi dalam sistem"""
    HOME = "home"           # Posisi calibration (0,0,0)
    STANDBY = "standby"     # Posisi siaga sebelum pick
    GRID = "grid"           # Grid position di papan catur

class CoordinateSystem:
    """Manager untuk sistem koordinat arm Dobot Magician"""
    
    def __init__(self):
        """
        Inisialisasi coordinate system dengan grid 4x4:
        - Format: (col, row) dimana col=1-4, row=1-4
        - Total 16 titik
        - X: 2 posisi [51 (kolom 1,2), -16 (kolom 3,4)]
        - Y: 4 posisi dengan spacing 20mm
        """
        
        # ==========================================
        # KONSTANTA SISTEM KOORDINAT
        # ==========================================
        
        # Sumbu X (Depan-Belakang, TETAP)
        self.X_HOME = 0                    # Home/calibration point
        self.X_STANDBY = 171.8             # Posisi siaga pick up
        
        # Drop Zone X positions (berdasarkan kolom)
        # Kolom 1,2 -> X=51 (ujung A)
        # Kolom 3,4 -> X=-16 (ujung B)
        self.X_BY_COL = {
            1: 51, 2: 51,
            3: -16, 4: -16
        }
        
        # Sumbu Y (Kiri-Kanan, RELATIF terhadap HOME)
        self.Y_MAX_REACH = 310             # Jangkauan maksimal arm (mm)
        self.Y_CENTER = 0                  # Center adalah home reference
        
        # Drop Zone Y positions (berdasarkan row) - spacing 20mm
        # Row 1 -> Y=-30
        # Row 2 -> Y=-10
        # Row 3 -> Y=+10
        # Row 4 -> Y=+30
        self.Y_BY_ROW = {
            1: -30,
            2: -10,
            3: +10,
            4: +30
        }
        
        # ==========================================
        # GRID MAPPING (4x4 = 16 titik)
        # ==========================================
        """
        Grid layout (1-indexed, format: (col, row)):
        (1,1) (2,1) (3,1) (4,1)
        (1,2) (2,2) (3,2) (4,2)
        (1,3) (2,3) (3,3) (4,3)
        (1,4) (2,4) (3,4) (4,4)
        """
        self.grid_positions = {}
        for col in range(1, 5):
            for row in range(1, 5):
                grid_id = (col, row)
                self.grid_positions[grid_id] = {
                    "col": col,
                    "row": row,
                    "x": self.X_BY_COL[col],
                    "y": self.Y_BY_ROW[row],
                    "label": f"({col},{row})"
                }
        
        # Store home position setelah calibration
        self.home_position = None
        self.is_calibrated = False

    def calibrate(self, home_position):
        """
        Simpan home position setelah arm di-home.
        
        Args:
            home_position: CustomPosition dari arm setelah home (seharusnya 0,0,0)
        """
        self.home_position = home_position
        self.is_calibrated = True
        
        print(f"[CALIBRATION] Home position: X={home_position.x}, Y={home_position.y}, Z={home_position.z}")
        print(f"[CALIBRATION] Sistem koordinat siap digunakan.")
        return True

    def get_standby_position(self, z=9.44, r=20.7):
        """
        Dapatkan posisi standby (siap pick).
        
        Returns:
            CustomPosition untuk posisi siaga
        """
        if not self.is_calibrated:
            raise RuntimeError("System belum dikalibrasi! Jalankan home dulu.")
        
        return CustomPosition(
            x=self.X_STANDBY,
            y=self.Y_CENTER,  # Kembali ke center (home Y reference)
            z=z,
            r=r
        )

    def get_grid_position(self, col, row, z=-10, r=100):
        """
        Dapatkan posisi di grid papan catur.
        
        Args:
            col: Kolom (1-4)
            row: Baris (1-4)
            z: Ketinggian drop (default -10)
            r: Rotasi gripper (default 100)
            
        Returns:
            CustomPosition untuk grid tertentu
        """
        if not self.is_calibrated:
            raise RuntimeError("System belum dikalibrasi! Jalankan home dulu.")
        
        if col < 1 or col > 4 or row < 1 or row > 4:
            raise ValueError(f"Grid ({col}, {row}) tidak valid. Gunakan col,row dalam range 1-4.")
        
        grid_key = (col, row)
        if grid_key not in self.grid_positions:
            raise ValueError(f"Grid {grid_key} tidak ditemukan.")
        
        pos = self.grid_positions[grid_key]
        
        print(f"[DROP] Grid ({col},{row}): X={pos['x']}, Y={pos['y']}")
        
        return CustomPosition(
            x=pos["x"],
            y=pos["y"],
            z=z,
            r=r
        )

    def get_all_grid_positions(self):
        """Return semua posisi grid dalam format dict"""
        result = {}
        for grid_id in self.grid_positions.keys():
            result[grid_id] = self.get_grid_position(grid_id)
        return result

    def print_system_info(self):
        """Print informasi sistem koordinat untuk debug"""
        print("\n" + "="*60)
        print("DOBOT MAGICIAN COORDINATE SYSTEM INFO")
        print("="*60)
        print(f"\n📍 GRID 4x4 (1-indexed):")
        print(f"   Format: (col, row) dimana col=1-4, row=1-4")
        
        print(f"\n📍 SUMBU X (Depan-Belakang, TETAP):")
        print(f"   Home/Center:     X = {self.X_HOME} mm")
        print(f"   Posisi Standby:  X = {self.X_STANDBY} mm")
        print(f"   Kolom 1,2:       X = 51 mm")
        print(f"   Kolom 3,4:       X = -16 mm")
        
        print(f"\n📍 SUMBU Y (Kiri-Kanan, RELATIF ke HOME):")
        print(f"   Center (Home Ref): Y = {self.Y_CENTER} mm")
        print(f"   Max Reach:        Y = ±{self.Y_MAX_REACH} mm")
        print(f"   Row 1:            Y = -30 mm")
        print(f"   Row 2:            Y = -10 mm")
        print(f"   Row 3:            Y = +10 mm")
        print(f"   Row 4:            Y = +30 mm")
        
        print(f"\n📍 GRID POSITIONS (4x4 = 16 titik):")
        for row in range(1, 5):
            row_str = ""
            for col in range(1, 5):
                pos = self.grid_positions[(col, row)]
                row_str += f"({col},{row}):({pos['x']:3},{pos['y']:3})  "
            print(f"   Row {row}: {row_str}")
        
        print(f"\n✓ Status Kalibrasi: {'SIAP' if self.is_calibrated else 'BELUM - Jalankan home dulu!'}")
        print("="*60 + "\n")


# ==========================================
# ROBOT MOVEMENT FUNCTIONS (Unified)
# ==========================================

def ke_posisi_awal(device: Dobot):
    """Pindah ke posisi siaga (standby)"""
    print("move to preparation position..")
    posisi_awal = CustomPosition(173.8, 3.45, 9.44, 20.7)
    device.move_to(x=posisi_awal.x, y=posisi_awal.y, z=posisi_awal.z, r=posisi_awal.r, wait=True)


def pick_payload(device: Dobot, position: CustomPosition):
    """Pick payload dari posisi tertentu"""
    print("pick payload..")
    ke_posisi_awal(device)
    sleep(2)
    device.move_to(x=position.x, y=position.y, z=position.z-20, r=position.r, wait=True)
    sleep(3)
    device.grip(enable=False)
    sleep(3)
    ke_posisi_awal(device)


def place_payload(device: Dobot, position: CustomPosition):
    """Place payload ke posisi tertentu"""
    print("place payload..")
    sleep(2)
    device.move_to(x=position.x, y=position.y, z=position.z+90, r=position.r, wait=True)
    sleep(3)
    device.move_to(x=position.x, y=position.y, z=position.z, r=position.r, wait=True)
    device.grip(enable=True)
    sleep(3)
    device.move_to(x=position.x, y=position.y, z=position.z+120, r=position.r, wait=True)


def execute_drop(device: Dobot, col: int, row: int, coord_system: CoordinateSystem):
    """
    Unified function untuk drop di grid tertentu
    
    Args:
        device: Dobot device
        col: Kolom grid (1-4)
        row: Baris grid (1-4)
        coord_system: CoordinateSystem instance
    """
    if not coord_system.is_calibrated:
        raise RuntimeError("Coordinate system belum dikalibrasi!")
    
    print(f"\n[EXECUTE] Bergerak ke Grid ({col},{row})")
    
    drop_pos = coord_system.get_grid_position(col, row)
    pick_payload(device, CustomPosition(173.8, 3.45, 9.44, 20.7))
    sleep(2)
    place_payload(device, drop_pos)
    sleep(2)
    ke_posisi_awal(device)
    
    print(f"[EXECUTE] Grid ({col},{row}) selesai")


# Backward compatibility functions (deprecated tapi tetap ada untuk compatibility)
def posisiA(device):
    """Legacy function - gunakan execute_drop() untuk lebih fleksibel"""
    print("[DEPRECATED] posisiA() - gunakan execute_drop(device, 'A1', coord_system)")
    pick_payload(device, CustomPosition(173.8, 3.45, 9.44, 20.7))
    place_payload(device, CustomPosition(14.68, 24.7, -22.05, 100))
    ke_posisi_awal(device)

def posisiB(device):
    """Legacy function - gunakan execute_drop() untuk lebih fleksibel"""
    print("[DEPRECATED] posisiB() - gunakan execute_drop(device, 'B1', coord_system)")
    pick_payload(device, CustomPosition(173.8, 3.45, 9.44, 20.7))
    place_payload(device, CustomPosition(-29.064, 204.89, -18.74, 100))
    ke_posisi_awal(device)

def posisiC(device):
    """Legacy function - gunakan execute_drop() untuk lebih fleksibel"""
    print("[DEPRECATED] posisiC() - gunakan execute_drop(device, 'B2', coord_system)")
    pick_payload(device, CustomPosition(173.8, 3.45, 9.44, 20.7))
    place_payload(device, CustomPosition(-21.72, 253.6, -17.82, 100))
    ke_posisi_awal(device)

def posisiD(device):
    """Legacy function - gunakan execute_drop() untuk lebih fleksibel"""
    print("[DEPRECATED] posisiD() - gunakan execute_drop(device, 'B4', coord_system)")
    pick_payload(device, CustomPosition(173.8, 3.45, 9.44, 20.7))
    place_payload(device, CustomPosition(-22.95, 254.08, -17.25, 100))
    ke_posisi_awal(device)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def create_coordinate_system():
    """Factory function untuk create coordinate system"""
    return CoordinateSystem()
