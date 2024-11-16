import pyautogui
import time
import random
import chess
from pathlib import Path

# Konfigurasi PyAutoGUI
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

# Konfigurasi papan catur berdasarkan koordinat yang diberikan
GRID_START_X = 295
GRID_START_Y = 147
GRID_END_X = 1088
GRID_END_Y = 938

# Hitung ukuran sel
GRID_WIDTH = GRID_END_X - GRID_START_X
GRID_HEIGHT = GRID_END_Y - GRID_START_Y
CELL_SIZE = min(GRID_WIDTH, GRID_HEIGHT) // 8

# Mapping untuk konversi notasi
COL_MAP = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
REV_COL_MAP = {v: k for k, v in COL_MAP.items()}

def get_turn_from_fen():
    """
    Membaca file fen.txt dan mengembalikan giliran siapa yang harus bergerak
    Returns:
        str: 'white' atau 'black'
    """
    try:
        with open('fen.txt', 'r') as file:
            lines = file.readlines()
            if lines:
                # Ambil FEN terakhir (paling bawah) di file
                fen = lines[-1].strip()  # Mengambil baris terakhir dan menghapus spasi ekstra
                board = chess.Board(fen)
                
                # Menampilkan FEN ke konsol untuk debugging
                print(f"FEN Terbaru: {fen}")
                
                # Mengembalikan giliran dari FEN (WHITE atau BLACK)
                return 'white' if board.turn == chess.WHITE else 'black'
    except Exception as e:
        print(f"Error membaca FEN: {str(e)}")
        return 'white'  # Default ke white jika ada error
    return 'white'  # Default ke white jika format FEN tidak valid

def print_mapping_info():
    print("\nMapping Koordinat: ")
    print("Kolom: ")
    for letter, number in COL_MAP.items():
        print(f"  {letter} -> {number}")
    print("\nBaris: ")
    for i in range(8, 0, -1):
        y_coord = GRID_START_Y + (8 - i) * CELL_SIZE + (CELL_SIZE // 2)
        print(f"  {i}     -> {y_coord}")

def san_to_coordinates(san_move):
    if len(san_move) != 4:
        raise ValueError("Format SAN tidak valid")
    
    start_col = COL_MAP.get(san_move[0].lower())
    start_row = int(san_move[1])
    end_col = COL_MAP.get(san_move[2].lower())
    end_row = int(san_move[3])
    
    # Dapatkan perspektif dari FEN
    current_turn = get_turn_from_fen()
    
    # Balik koordinat jika giliran hitam
    if current_turn == "black":
        start_row, end_row = 9 - start_row, 9 - end_row
        start_col, end_col = 9 - start_col, 9 - end_col
        print("Perspektif: Hitam (koordinat dibalik)")
    else:
        print("Perspektif: Putih (koordinat normal)")

    if not all([start_col, start_row, end_col, end_row]):
        raise ValueError("Koordinat tidak valid")
    
    print(f"\nDetail konversi {san_move}:")
    print(f"Awal: {san_move[0]}{san_move[1]} -> Kolom {start_col}, Baris {start_row}")
    print(f"Akhir: {san_move[2]}{san_move[3]} -> Kolom {end_col}, Baris {end_row}")
    
    return ((start_row, start_col), (end_row, end_col))

def get_grid_position(row, col):
    # Menghitung posisi klik di tengah sel
    x = GRID_START_X + (col - 1) * CELL_SIZE + (CELL_SIZE // 2)
    y = GRID_START_Y + (8 - row) * CELL_SIZE + (CELL_SIZE // 2)
    
    # Menghapus bagian randomisasi
    # x += random.uniform(-CELL_SIZE // 8, CELL_SIZE // 8)
    # y += random.uniform(-CELL_SIZE // 8, CELL_SIZE // 8)
    
    return (int(x), int(y))


def get_latest_move(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if lines:
                return lines[-1].strip()
    except Exception as e:
        print(f"Error membaca file: {str(e)}")
    return None

def perform_click(x, y, duration=0.2):
    pyautogui.moveTo(x, y, duration=duration)
    time.sleep(0.1)
    pyautogui.mouseDown(x, y)
    time.sleep(0.1)
    pyautogui.mouseUp(x, y)
    time.sleep(0.1)

def execute_move(start_pos, end_pos):
    perform_click(start_pos[0], start_pos[1])
    time.sleep(0.3)
    
    perform_click(end_pos[0], end_pos[1])
    time.sleep(0.3)
    
    time.sleep(0.2)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(0.2)

def monitor_and_execute():
    file_path = Path('best.txt')
    last_processed_move = None
    
    print("\nMonitoring best.txt untuk gerakan baru...")
    print(f"Menggunakan koordinat grid: ({GRID_START_X}, {GRID_START_Y}) ke ({GRID_END_X}, {GRID_END_Y})")
    print(f"Ukuran sel: {CELL_SIZE} piksel")
    print("Perspektif akan otomatis disesuaikan berdasarkan FEN")
    
    while True:
        try:
            current_move = get_latest_move(file_path)
            
            if current_move:
                current_move = current_move[:4]
            
            if current_move and current_move != last_processed_move:
                print(f"\n{'='*50}")
                print(f"Gerakan baru terdeteksi: {current_move}")
                print(f"{'='*50}")
                
                try:
                    (start_row, start_col), (end_row, end_col) = san_to_coordinates(current_move)
                    start_pos = get_grid_position(start_row, start_col)
                    end_pos = get_grid_position(end_row, end_col)
                    
                    print("\nRingkasan gerakan: ")
                    print(f"Dari: {current_move[0:2]} -> ({start_pos[0]}, {start_pos[1]})")
                    print(f"Ke: {current_move[2:4]} -> ({end_pos[0]}, {end_pos[1]})")
                    
                    print("\nMelakukan gerakan dalam 0.5 detik...")
                    time.sleep(0.5)
                    
                    execute_move(start_pos, end_pos)
                    
                    print("Gerakan selesai dilakukan")
                    print(f"{'='*50}")
                    last_processed_move = current_move
                    
                except ValueError as ve:
                    print(f"Error dalam konversi notasi: {str(ve)}")
                except Exception as e:
                    print(f"Error dalam eksekusi gerakan: {str(e)}")
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\nProgram dihentikan oleh pengguna")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            time.sleep(1)

# Menampilkan informasi mapping koordinat
print_mapping_info()

# Mulai monitoring dan eksekusi gerakan
monitor_and_execute()
