"""
Module untuk kalibrasi grid papan catur
"""
import tkinter as tk
import pyautogui
import time
from PIL import Image, ImageDraw, ImageFont

MIN_AREA_SIZE = 10
MAX_COORDINATE = 5000
GRID_SIZE = 8
WAIT_TIME_FIRST = 5
WAIT_TIME_SECOND = 5

class GridCalibrator:
    def __init__(self):
        self.window = None
        self.coordinates = None
        
    def validate_coordinates(self, x1, y1, x2, y2):
        assert 0 <= x1 <= MAX_COORDINATE, "X1 di luar batas"
        assert 0 <= y1 <= MAX_COORDINATE, "Y1 di luar batas"
        assert 0 <= x2 <= MAX_COORDINATE, "X2 di luar batas"
        assert 0 <= y2 <= MAX_COORDINATE, "Y2 di luar batas"
        
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        assert width >= MIN_AREA_SIZE, "Area terlalu kecil (width)"
        assert height >= MIN_AREA_SIZE, "Area terlalu kecil (height)"
        
        return width, height

    def select_area(self):
        print("Pilih pojok kiri atas dan pojok kanan bawah.")
        time.sleep(WAIT_TIME_FIRST)
        
        print("Klik pada pojok kiri atas.")
        x1, y1 = pyautogui.position()
        print(f"Pojok kiri atas: ({x1}, {y1})")
        
        time.sleep(WAIT_TIME_SECOND)

        print("Klik pada pojok kanan bawah.")
        x2, y2 = pyautogui.position()
        print(f"Pojok kanan bawah: ({x2}, {y2})")

        try:
            width, height = self.validate_coordinates(x1, y1, x2, y2)
            print(f"Area: {width}x{height} pixels.")
            
            # Simpan koordinat
            self.coordinates = {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'width': width,
                'height': height
            }
            
            screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
            self.draw_grid(screenshot, width, height, x1, y1)
            
            # Simpan ke config file
            self.save_config()
            
            return self.coordinates
        except AssertionError as e:
            print(f"Error: {e}")
            return None

    def draw_grid(self, image, width, height, x_offset, y_offset):
        assert image, "Image tidak boleh None"
        assert width > 0, "Width harus positif"
        assert height > 0, "Height harus positif"
        
        draw = ImageDraw.Draw(image)
        grid_size_x = width // GRID_SIZE
        grid_size_y = height // GRID_SIZE
        
        assert grid_size_x > 0, "Grid size X terlalu kecil"
        assert grid_size_y > 0, "Grid size Y terlalu kecil"
        
        self.draw_grid_lines(draw, width, height, grid_size_x, grid_size_y)
        self.draw_grid_labels(draw, grid_size_x, grid_size_y)
        self.save_image(image)

    def draw_grid_lines(self, draw, width, height, grid_size_x, grid_size_y):
        grid_color = (255, 0, 0)
        
        max_iterations = GRID_SIZE
        for i in range(1, max_iterations):
            draw.line([(i * grid_size_x, 0), (i * grid_size_x, height)], 
                     fill=grid_color, width=2)
            draw.line([(0, i * grid_size_y), (width, i * grid_size_y)], 
                     fill=grid_color, width=2)

    def draw_grid_labels(self, draw, grid_size_x, grid_size_y):
        font = ImageFont.load_default()
        
        max_row = GRID_SIZE
        max_col = GRID_SIZE
        for row in range(max_row):
            for col in range(max_col):
                label = f"({row+1},{col+1})"
                x_pos = col * grid_size_x + grid_size_x // 2
                y_pos = row * grid_size_y + grid_size_y // 2
                draw.text((x_pos, y_pos), label, fill="black", font=font)

    def save_image(self, image):
        assert image, "Image tidak boleh None"
        filename = "selected_area_grid_labeled.png"
        try:
            image.save(filename)
            print(f"Screenshot disimpan: {filename}")
        except IOError as e:
            print(f"Error menyimpan gambar: {e}")
            
    def save_config(self, elo_limit=False, elo_value=1500):
        """Simpan koordinat dan Elo settings ke config.txt"""
        if not self.coordinates:
            return
            
        try:
            with open('grid_config.txt', 'w') as f:
                f.write(f"{self.coordinates['x1']}\n")
                f.write(f"{self.coordinates['y1']}\n")
                f.write(f"{self.coordinates['x2']}\n")
                f.write(f"{self.coordinates['y2']}\n")
                f.write(f"{int(elo_limit)}\n")
                f.write(f"{elo_value}\n")
            print("Koordinat dan Elo settings disimpan ke grid_config.txt")
        except IOError as e:
            print(f"Error menyimpan config: {e}")
            
    def load_config(self):
        """Load koordinat dan Elo settings dari config.txt"""
        try:
            with open('grid_config.txt', 'r') as f:
                lines = f.readlines()
                if len(lines) >= 4:
                    x1 = int(lines[0].strip())
                    y1 = int(lines[1].strip())
                    x2 = int(lines[2].strip())
                    y2 = int(lines[3].strip())
                    
                    # Load Elo settings if available (backward compatible)
                    elo_limit = bool(int(lines[4].strip())) if len(lines) > 4 else False
                    elo_value = int(lines[5].strip()) if len(lines) > 5 else 1500
                    
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    
                    self.coordinates = {
                        'x1': x1,
                        'y1': y1,
                        'x2': x2,
                        'y2': y2,
                        'width': width,
                        'height': height,
                        'elo_limit': elo_limit,
                        'elo_value': elo_value
                    }
                    print(f"Koordinat dimuat: ({x1}, {y1}) ke ({x2}, {y2})")
                    print(f"Elo settings: Limit={elo_limit}, Elo={elo_value}")
                    return self.coordinates
        except (IOError, ValueError) as e:
            print(f"Config tidak ditemukan atau invalid: {e}")
        return None

    def show_gui(self):
        """Tampilkan GUI untuk kalibrasi"""
        self.window = tk.Tk()
        self.window.title("Grid Calibration")
        self.window.geometry("300x150")
        self.window.attributes('-topmost', True)
        
        label = tk.Label(self.window, text="Tekan tombol untuk pilih area!", 
                         font=('Arial', 12))
        label.pack(pady=20)
        
        select_button = tk.Button(self.window, text="Select Area", 
                                 command=self._on_select, font=('Arial', 12))
        select_button.pack(pady=10)

        self.window.mainloop()
        
    def _on_select(self):
        """Handler untuk tombol select"""
        self.select_area()
        if self.coordinates:
            self.window.destroy()
