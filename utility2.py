"""
utility2.py

Dobot Magician Coordinate System Manager + Unified Sequence Functions
=====================================================================
Sistem koordinat Dobot Magician untuk Papan Catur 4x4 (Matriks 16 Titik)
- Sisi setiap box/grid: 20 mm (2 cm)
- Sumbu X: Jarak depan-belakang (Kolom 1 & 2 di X=51 mm, Kolom 3 & 4 di X=-16 mm)
- Sumbu Y: Jarak kiri-kanan dengan spacing presisi 20 mm sesuai ukuran box (-30, -10, +10, +30)
- Sumbu Z: Ketinggian vertikal
"""

from pydobotplus import Dobot, CustomPosition
from time import sleep
from enum import Enum

class PositionType(Enum):
    HOME = "home"
    STANDBY = "standby"
    GRID = "grid"

# ============================================================
# KONSTANTA SISTEM GLOBAL
# ============================================================
# Poin 1: Posisi IDLE Kustom saat mesin baru aktif atau setelah eksekusi perintah
# X = 173.8, Y = 0.0 (Relatif awal), Z = 47.4
POSISI_IDLE = CustomPosition(x=173.8, y=0.0, z=47.4, r=0.0)

# Posisi pengambilan benda (Pick Up) di atas Conveyor Belt
POSISI_PICK_CONVEYOR = CustomPosition(x=173.8, y=3.45, z=9.44, r=20.7)


class CoordinateSystem:
    """Manager hitungan sistem koordinat papan matriks 4x4"""
    
    def __init__(self):
        # Sumbu X (Tetap berdasarkan pembagian kelompok kolom)
        self.X_HOME = 0
        self.X_STANDBY = 171.8
        
        # Pemetaan Sumbu X berdasarkan nomor Kolom (1-indexed)
        self.X_BY_COL = {
            1: 51, 2: 51,
            3: -16, 4: -16
        }
        
        # Pemetaan Sumbu Y berdasarkan nomor Baris/Row (1-indexed) dengan Spacing 20mm (2cm)
        self.Y_BY_ROW = {
            1: -30,
            2: -10,
            3: 10,
            4: 30
        }
        
        # Generator Otomatis Matriks Koordinat Grid 4x4 (16 Titik)
        self.grid_positions = {}
        self._calculate_all_grids()
        
        self.home_position = None
        self.is_calibrated = False

    def _calculate_all_grids(self):
        """Menghitung dan memetakan koordinat X, Y untuk setiap kombinasi grid (col, row)"""
        for col in range(1, 5):
            for row in range(1, 5):
                grid_id = (col, row)
                self.grid_positions[grid_id] = {
                    "col": col,
                    "row": row,
                    "x": self.X_BY_COL[col],
                    "y": self.Y_BY_ROW[row],
                    "label": f"Grid ({col},{row})"
                }

    def calibrate(self, home_position):
        """Menandai bahwa sistem koordinat mekanis robot telah siap digunakan"""
        self.home_position = home_position
        self.is_calibrated = True
        print(f"[CALIBRATION] Dobot Calibrated. Home Reference: X={home_position.x}, Y={home_position.y}")
        return True

    def get_grid_position(self, col, row, z=-10, r=100):
        """Mengambil data koordinat spesifik hasil kalkulasi grid matriks"""
        if not self.is_calibrated:
            raise RuntimeError("Sistem belum dikalibrasi! Jalankan home terlebih dahulu.")
        
        grid_key = (col, row)
        if grid_key not in self.grid_positions:
            raise ValueError(f"Koordinat grid ({col},{row}) di luar jangkauan matriks 4x4!")
        
        pos = self.grid_positions[grid_key]
        print(f"[KONTROL] Ambil Target {pos['label']} -> X: {pos['x']} mm, Y: {pos['y']} mm")
        
        return CustomPosition(x=pos["x"], y=pos["y"], z=z, r=r)


# ============================================================
# FUNGSI PERGERAKAN MANDIRI (LOW LEVEL MOVEMENT)
# ============================================================

def ke_posisi_idle(device: Dobot):
    """Langkah 1 & 6: Mengembalikan arm robot ke titik aman/idle kustom secara software"""
    print(f"[ROBOT] Pindah ke Posisi Idle -> X: {POSISI_IDLE.x}, Y: {POSISI_IDLE.y}, Z: {POSISI_IDLE.z}")
    device.move_to(x=POSISI_IDLE.x, y=POSISI_IDLE.y, z=POSISI_IDLE.z, r=POSISI_IDLE.r, wait=True)


def pick_payload(device: Dobot, position: CustomPosition):
    """Langkah 4: Mekanisme turun, mengaktifkan gripper/suction, dan mengangkat benda"""
    print("[ROBOT] Memulai sekuens picking di conveyor...")
    # Menuju ke posisi bersiap di atas conveyor
    device.move_to(x=position.x, y=position.y, z=position.z, r=position.r, wait=True)
    sleep(1)
    
    # Arm turun mendekati box (Z dikompensasi 20mm ke bawah untuk menjangkau permukaan objek)
    device.move_to(x=position.x, y=position.y, z=position.z - 20, r=position.r, wait=True)
    sleep(1.5)
    
    # Menjepit/mencengkeram benda (Sesuaikan parameter pneumatik/gripper pada hardware Anda)
    print("[ROBOT] Gripper/Suction Cup AKTIF.")
    device.grip(enable=False) 
    sleep(2)
    
    # Mengangkat kembali arm ke ketinggian aman standby conveyor
    device.move_to(x=position.x, y=position.y, z=position.z, r=position.r, wait=True)


def place_payload(device: Dobot, position: CustomPosition):
    """Langkah 5: Membawa benda di atas titik drop, turun, melepaskan, dan naik kembali"""
    print("[ROBOT] Memulai sekuens placing ke area grid...")
    sleep(1)
    
    # Berada di atas koordinat grid sasaran (Z dinaikkan +90mm agar tidak menabrak susunan lain)
    device.move_to(x=position.x, y=position.y, z=position.z + 90, r=position.r, wait=True)
    sleep(1.5)
    
    # Lengan turun ke koordinat Z drop target asli
    device.move_to(x=position.x, y=position.y, z=position.z, r=position.r, wait=True)
    sleep(1)
    
    # Melepaskan cengkeraman benda
    print("[ROBOT] Gripper/Suction Cup NON-AKTIF (Benda diletakkan).")
    device.grip(enable=True)
    sleep(2)
    
    # Arm naik menjauh ke atas (+120mm) sebelum bergeser kembali ke idle
    device.move_to(x=position.x, y=position.y, z=position.z + 120, r=position.r, wait=True)


# ============================================================
# ALUR WORKFLOW UTAMA (HIGH LEVEL SEQUENCE 1-6)
# ============================================================

def kontrol_conveyor(device: Dobot, status="jalan"):
    """Langkah 2: Mengatur kondisi pergerakan hardware Conveyor Belt"""
    if status == "jalan":
        print("[CONVEYOR] Motor Aktif -> Mengalirkan box menuju area jangkauan...")
        # Integrasikan perintah IO/Conveyor pydobotplus Anda di sini seandainya ada, misal:
        # device.conveyor(speed=10000)
    else:
        print("[CONVEYOR] Motor Mati -> Box dikunci di titik deteksi.")
        # device.conveyor(speed=0)


def amati_kamera_placeholder():
    """Langkah 3: Tempat penampungan logika deteksi warna (Computer Vision)"""
    print("[VISION] Menunggu konfirmasi visual dari kamera...")
    sleep(2)  # Simulasi jeda waktu tunggu pemrosesan gambar
    
    # Sementara mengembalikan True otomatis agar sekuens dapat berlanjut ke tahap pengantaran
    return True


def execute_full_sequence(device: Dobot, col: int, row: int, coord_system: CoordinateSystem):
    """
    Eksekutor urutan kerja otomatis terintegrasi (Poin 1 hingga 6)
    """
    if not coord_system.is_calibrated:
        raise RuntimeError("Gagal menjalankan sekuens! Sistem koordinat belum siap.")

    print(f"\n========================================================")
    print(f"RUNNING SEQUENCE: TARGET MATCHING -> GRID CELL ({col}, {row})")
    print(f"========================================================")

    # 1. Menuju ke posisi Idle awal kustom secara software
    ke_posisi_idle(device)
    sleep(1)

    # 2. Conveyor belt bergerak mencari objek baru
    kontrol_conveyor(device, status="jalan")

    # 3. Kamera menganalisis warna box hingga objek valid berhenti tepat di depan sensor
    box_terkonfirmasi = amati_kamera_placeholder()

    if box_terkonfirmasi:
        # Hentikan aliran conveyor segera setelah kamera/sensor mendeteksi box masuk
        kontrol_conveyor(device, status="berhenti")
        sleep(0.5)

        # 4. Lengan robot bergerak mengambil box di atas conveyor belt
        pick_payload(device, POSISI_PICK_CONVEYOR)
        sleep(1)

        # 5. Mengangkat dan memindahkan benda ke titik dropdown matriks papan catur pilihan GUI
        drop_target_coordinates = coord_system.get_grid_position(col, row)
        place_payload(device, drop_target_coordinates)
        sleep(1)

        # 6. Naik kembali dan pulang mengunci posisi di koordinat Idle awal
        ke_posisi_idle(device)
        
        print(f"\n[SUKSES] Misi penataan Box pada Grid ({col}, {row}) Berhasil diselesaikan!")
        print(f"========================================================\n")
        return True
    else:
        print("[GAGAL] Kamera tidak menemukan box yang sesuai. Menghentikan conveyor demi keamanan.")
        kontrol_conveyor(device, status="berhenti")
        ke_posisi_idle(device)
        return False
