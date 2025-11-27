"""
Module untuk auto-clicker chess moves
"""
import pyautogui
import time
import chess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

MAX_MOVE_LENGTH = 10
COL_MAP = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}

class AutoClicker:
    def __init__(self, grid_start_x, grid_start_y, grid_end_x, grid_end_y, instant_mode=False):
        self.grid_start_x = grid_start_x
        self.grid_start_y = grid_start_y
        self.grid_end_x = grid_end_x
        self.grid_end_y = grid_end_y
        self.grid_width = grid_end_x - grid_start_x
        self.grid_height = grid_end_y - grid_start_y
        self.cell_size = min(self.grid_width, self.grid_height) // 8
        self.last_processed_move = None
        self.observer = None
        self.running = False
        self.board_flipped = False  # True jika Black di bawah
        self.instant_mode = instant_mode  # True untuk instant click tanpa simulasi
        
    def get_turn_from_fen(self):
        try:
            with open('fen.txt', 'r') as file:
                content = file.read().strip()
                assert content, "File FEN kosong"
                
                board = chess.Board(content)
                return 'white' if board.turn == chess.WHITE else 'black'
        except (IOError, ValueError, AssertionError):
            return 'white'

    def set_board_flipped(self, flipped):
        """Set apakah board diflip (Black di bawah)"""
        self.board_flipped = flipped
    
    def set_instant_mode(self, instant):
        """Set mode klik: instant (True) atau simulate human (False)"""
        self.instant_mode = instant

    def validate_move_format(self, san_move):
        assert san_move, "Move tidak boleh kosong"
        assert len(san_move) >= 4, "Format move tidak valid"
        assert san_move[0] in COL_MAP, "Kolom awal tidak valid"
        assert san_move[2] in COL_MAP, "Kolom akhir tidak valid"
        assert san_move[1].isdigit(), "Baris awal harus angka"
        assert san_move[3].isdigit(), "Baris akhir harus angka"
        return True

    def san_to_coordinates(self, san_move):
        self.validate_move_format(san_move)
        
        start_col = COL_MAP[san_move[0].lower()]
        start_row = int(san_move[1])
        end_col = COL_MAP[san_move[2].lower()]
        end_row = int(san_move[3])
        
        assert 1 <= start_row <= 8, "Baris awal harus 1-8"
        assert 1 <= end_row <= 8, "Baris akhir harus 1-8"
        
        # LOGIKA PERSPEKTIF:
        # - Normal (White di bawah): koordinat UCI langsung dipakai
        # - Flipped (Black di bawah): koordinat harus dibalik
        if self.board_flipped:
            # Flip koordinat untuk perspektif Black di bawah
            start_row, end_row = 9 - start_row, 9 - end_row
            start_col, end_col = 9 - start_col, 9 - end_col
        
        return ((start_row, start_col), (end_row, end_col))

    def get_grid_position(self, row, col):
        assert 1 <= row <= 8, "Row harus antara 1-8"
        assert 1 <= col <= 8, "Col harus antara 1-8"
        
        x = self.grid_start_x + (col - 1) * self.cell_size + (self.cell_size // 2)
        y = self.grid_start_y + (8 - row) * self.cell_size + (self.cell_size // 2)
        
        return (int(x), int(y))

    def get_latest_move(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read().strip()
                if content:
                    assert len(content) <= MAX_MOVE_LENGTH, "Move terlalu panjang"
                    return content
        except (IOError, AssertionError):
            pass
        return None

    def perform_click(self, x, y, duration=0.2):
        assert 0 <= x <= 3000, "X koordinat di luar batas"
        assert 0 <= y <= 3000, "Y koordinat di luar batas"
        
        if self.instant_mode:
            # Instant mode: langsung klik tanpa animasi
            pyautogui.click(x, y)
        else:
            # Human simulation mode: dengan gerakan mouse dan delay
            pyautogui.moveTo(x, y, duration=duration)
            time.sleep(0.1)
            pyautogui.mouseDown(x, y)
            time.sleep(0.1)
            pyautogui.mouseUp(x, y)
            time.sleep(0.1)

    def execute_move(self, start_pos, end_pos):
        assert start_pos, "Start position tidak boleh None"
        assert end_pos, "End position tidak boleh None"
        
        if self.instant_mode:
            # Instant mode: klik langsung tanpa delay
            self.perform_click(start_pos[0], start_pos[1])
            self.perform_click(end_pos[0], end_pos[1])
            pyautogui.hotkey('alt', 'tab')
        else:
            # Human simulation mode: dengan delay natural
            self.perform_click(start_pos[0], start_pos[1])
            time.sleep(0.3)
            self.perform_click(end_pos[0], end_pos[1])
            time.sleep(0.3)
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.2)

    def process_move_file(self):
        file_path = Path('best.txt')
        
        current_move = self.get_latest_move(file_path)
        if not current_move:
            return
            
        current_move = current_move[:4]
        
        if current_move == self.last_processed_move:
            return
            
        print(f"\n{'='*50}")
        print(f"Gerakan baru: {current_move}")
        print(f"{'='*50}")
        
        try:
            (start_row, start_col), (end_row, end_col) = self.san_to_coordinates(current_move)
            start_pos = self.get_grid_position(start_row, start_col)
            end_pos = self.get_grid_position(end_row, end_col)
            
            print(f"Dari: {current_move[0:2]} -> {start_pos}")
            print(f"Ke: {current_move[2:4]} -> {end_pos}")
            
            time.sleep(0.5)
            self.execute_move(start_pos, end_pos)
            
            print("Gerakan selesai")
            print(f"{'='*50}")
            self.last_processed_move = current_move
            
        except (ValueError, AssertionError) as e:
            print(f"Error: {e}")

    def start(self):
        """Start monitoring best.txt file"""
        class MoveFileHandler(FileSystemEventHandler):
            def __init__(self, auto_clicker):
                self.auto_clicker = auto_clicker
                
            def on_modified(self, event):
                if event.src_path.endswith('best.txt'):
                    time.sleep(0.1)
                    self.auto_clicker.process_move_file()
        
        print("\nAuto-clicker dimulai...")
        print(f"Grid: ({self.grid_start_x}, {self.grid_start_y}) ke ({self.grid_end_x}, {self.grid_end_y})")
        print(f"Cell size: {self.cell_size}px")
        
        event_handler = MoveFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, path='.', recursive=False)
        self.observer.start()
        self.running = True
        
    def stop(self):
        """Stop monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.running = False
            print("\nAuto-clicker dihentikan")
