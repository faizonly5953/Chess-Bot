"""
Chess Bot - Main Application
Menggabungkan GUI, Stockfish Engine, dan Auto-Clicker dalam satu aplikasi

Cara menggunakan:
1. Jalankan: python main.py
2. Klik "Kalibrasi Grid" jika pertama kali (atau koordinat berubah)
3. Masukkan FEN dan klik "Mulai dari FEN"
4. Bot akan otomatis menganalisis dan mengklik langkah terbaik
"""

import tkinter as tk
from tkinter import messagebox
import chess
import threading
import time
import os
from pathlib import Path

from engine import StockfishEngine
from autoclicker import AutoClicker
from calibration import GridCalibrator

class ChessBot:
    def __init__(self, stockfish_path, syzygy_path=""):
        self.stockfish_path = stockfish_path
        self.syzygy_path = syzygy_path
        
        # Components
        self.engine = None
        self.auto_clicker = None
        self.calibrator = GridCalibrator()
        self.board = chess.Board()
        
        # State
        self.auto_click_enabled = False
        self.auto_clicker_thread = None
        self.board_flipped = False  # True jika Anda main sebagai Black di bawah
        
        # GUI
        self.root = None
        self.setup_gui()
        
    def setup_gui(self):
        """Setup main GUI window"""
        self.root = tk.Tk()
        self.root.title("Chess Bot - Integrated")
        self.root.geometry("600x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.attributes('-topmost', True)
        
        # Header
        header = tk.Label(self.root, text="Chess Bot", 
                         font=('Arial', 18, 'bold'))
        header.pack(pady=10)
        
        # Calibration Section
        calib_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        calib_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(calib_frame, text="Kalibrasi Grid", 
                font=('Arial', 12, 'bold')).pack(pady=5)
        
        btn_frame = tk.Frame(calib_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Kalibrasi Grid Baru", 
                 command=self.calibrate_grid, 
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
                 
        tk.Button(btn_frame, text="Load Config", 
                 command=self.load_grid_config, 
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.calib_status = tk.Label(calib_frame, text="Status: Belum dikalibrasi", 
                                     fg="red")
        self.calib_status.pack(pady=5)
        
        # Board Orientation
        orient_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        orient_frame.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(orient_frame, text="Perspektif Papan:", 
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        self.board_flip_var = tk.BooleanVar(value=False)
        tk.Radiobutton(orient_frame, text="Normal (White di bawah)", 
                      variable=self.board_flip_var, value=False,
                      command=self.update_board_orientation,
                      font=('Arial', 9)).pack()
        tk.Radiobutton(orient_frame, text="Flipped (Black di bawah)", 
                      variable=self.board_flip_var, value=True,
                      command=self.update_board_orientation,
                      font=('Arial', 9)).pack()
        
        # Auto-Clicker Toggle
        auto_frame = tk.Frame(self.root)
        auto_frame.pack(pady=5)
        
        self.auto_click_var = tk.BooleanVar(value=False)
        tk.Checkbutton(auto_frame, text="Aktifkan Auto-Clicker", 
                      variable=self.auto_click_var,
                      command=self.toggle_auto_clicker,
                      font=('Arial', 10)).pack()
        
        # FEN Input Section
        fen_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        fen_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(fen_frame, text="Masukkan FEN:", 
                font=('Arial', 11, 'bold')).pack(pady=5)
        
        self.fen_entry = tk.Entry(fen_frame, width=60, font=('Arial', 10))
        self.fen_entry.pack(pady=5, padx=10)
        
        tk.Button(fen_frame, text="Mulai dari FEN", 
                 command=self.start_from_fen,
                 font=('Arial', 11, 'bold'),
                 bg='#4CAF50', fg='white').pack(pady=10)
        
        # Current FEN Display
        self.fen_display = tk.Label(self.root, text="FEN saat ini: -", 
                                   font=('Arial', 9), 
                                   wraplength=550)
        self.fen_display.pack(pady=5)
        
        # Move Input Section
        move_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        move_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(move_frame, text="Langkah Manual", 
                font=('Arial', 11, 'bold')).pack(pady=5)
        
        self.white_move_label = tk.Label(move_frame, 
                                         text="Masukkan langkah Putih (SAN):")
        self.white_move_label.pack(pady=2)
        
        entry_frame = tk.Frame(move_frame)
        entry_frame.pack(pady=5)
        
        self.white_move_entry = tk.Entry(entry_frame, width=15, 
                                         font=('Arial', 11))
        self.white_move_entry.pack(side=tk.LEFT, padx=5)
        self.white_move_entry.bind("<Return>", self.add_white_move)
        
        tk.Button(entry_frame, text="Tambah Langkah", 
                 command=self.add_white_move,
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        # Best Move Display
        self.black_move_label = tk.Label(move_frame, 
                                         text="Best Move: -", 
                                         font=('Arial', 10, 'bold'),
                                         fg='blue')
        self.black_move_label.pack(pady=5)
        
        # Output Console
        tk.Label(self.root, text="Output:", 
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        output_frame = tk.Frame(self.root)
        output_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(output_frame, height=8, width=65,
                                   yscrollcommand=scrollbar.set,
                                   font=('Consolas', 9))
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output_text.yview)
        
        # Initialize engine
        self.log("Menginisialisasi Stockfish engine...")
        try:
            self.engine = StockfishEngine(self.stockfish_path, self.syzygy_path)
            self.log("✓ Stockfish engine siap")
        except Exception as e:
            self.log(f"✗ Error inisialisasi Stockfish: {e}")
            messagebox.showerror("Error", f"Gagal menginisialisasi Stockfish:\n{e}")
        
        # Try to load existing grid config
        self.load_grid_config()
        
    def calibrate_grid(self):
        """Kalibrasi grid papan catur"""
        self.log("Memulai kalibrasi grid...")
        coords = self.calibrator.select_area()
        if coords:
            self.setup_auto_clicker()
            self.calib_status.config(text=f"Status: Tersimpan ({coords['x1']},{coords['y1']}) ke ({coords['x2']},{coords['y2']})", 
                                    fg="green")
            self.log(f"✓ Grid dikalibrasi: {coords}")
        else:
            self.log("✗ Kalibrasi dibatalkan")
            
    def load_grid_config(self):
        """Load konfigurasi grid dari file"""
        coords = self.calibrator.load_config()
        if coords:
            self.setup_auto_clicker()
            self.calib_status.config(text=f"Status: Dimuat ({coords['x1']},{coords['y1']}) ke ({coords['x2']},{coords['y2']})", 
                                    fg="green")
            self.log(f"✓ Grid config dimuat: {coords}")
        else:
            self.log("Config grid tidak ditemukan. Silakan kalibrasi.")
            
    def update_board_orientation(self):
        """Update orientasi board dan auto-clicker"""
        self.board_flipped = self.board_flip_var.get()
        if self.auto_clicker:
            self.auto_clicker.set_board_flipped(self.board_flipped)
        
        orientation = "Flipped (Black di bawah)" if self.board_flipped else "Normal (White di bawah)"
        self.log(f"✓ Perspektif papan: {orientation}")
    
    def setup_auto_clicker(self):
        """Setup auto-clicker dengan koordinat yang sudah dikalibrasi"""
        if not self.calibrator.coordinates:
            return
            
        coords = self.calibrator.coordinates
        self.auto_clicker = AutoClicker(
            coords['x1'], coords['y1'], 
            coords['x2'], coords['y2']
        )
        self.auto_clicker.set_board_flipped(self.board_flipped)
        self.log("✓ Auto-clicker siap")
        
    def toggle_auto_clicker(self):
        """Toggle auto-clicker on/off"""
        if self.auto_click_var.get():
            if not self.auto_clicker:
                messagebox.showwarning("Warning", 
                    "Silakan kalibrasi grid terlebih dahulu!")
                self.auto_click_var.set(False)
                return
                
            self.auto_clicker.start()
            self.log("✓ Auto-clicker diaktifkan")
        else:
            if self.auto_clicker:
                self.auto_clicker.stop()
                self.log("✓ Auto-clicker dinonaktifkan")
    
    def start_from_fen(self):
        """Mulai analisis dari posisi FEN"""
        fen = self.fen_entry.get().strip()
        if not fen:
            self.log("✗ FEN tidak boleh kosong")
            return
            
        try:
            self.board.set_fen(fen)
            self.save_fen_to_file(fen)
            
            if self.engine:
                self.engine.set_position(fen)
            
            self.update_fen_display()
            self.process_initial_move(fen)
            
        except Exception as e:
            self.log(f"✗ Error: {e}")
            messagebox.showerror("Error", str(e))
    
    def process_initial_move(self, fen):
        """Proses langkah pertama berdasarkan giliran"""
        if not self.engine:
            return
            
        best_move = self.engine.get_best_move(fen)
        if not best_move:
            self.log("✗ Tidak dapat mendapatkan best move")
            return
            
        self.save_best_move_to_file(best_move)
        
        # Cek giliran siapa yang harus main
        if self.board.turn == chess.WHITE:
            # Giliran White (bot mainkan sebagai White)
            self.board.push_uci(best_move)
            self.engine.set_position(self.board.fen())
            self.white_move_label.config(text=f"White Best Move: {best_move}")
            self.update_fen_display()
            self.black_move_label.config(text="Giliran Black - Masukkan langkah")
            self.log(f"✓ White best move: {best_move}")
        else:
            # Giliran Black (bot mainkan sebagai Black)
            self.board.push_uci(best_move)
            self.engine.set_position(self.board.fen())
            self.black_move_label.config(text=f"Black Best Move: {best_move}")
            self.update_fen_display()
            self.white_move_label.config(text="Giliran White - Masukkan langkah")
            self.log(f"✓ Black best move: {best_move}")
    
    def add_white_move(self, event=None):
        """Tambahkan langkah putih dan dapatkan respons hitam"""
        white_move_san = self.white_move_entry.get().strip()
        if not white_move_san:
            return
            
        try:
            white_move = self.board.parse_san(white_move_san)
            assert self.board.is_legal(white_move), f"Langkah '{white_move_san}' tidak sah"
            
            self.board.push(white_move)
            if self.engine:
                self.engine.set_position(self.board.fen())
            
            self.log(f"→ White move: {white_move_san}")
            
            # Get opponent's response (Black's move)
            if self.engine:
                black_best_move = self.engine.get_best_move(self.board.fen())
                if black_best_move:
                    self.save_best_move_to_file(black_best_move)
                    self.board.push_uci(black_best_move)
                    self.engine.set_position(self.board.fen())
                    self.black_move_label.config(text=f"Black Best Move: {black_best_move}")
                    self.log(f"← Black best move: {black_best_move}")
                    self.update_fen_display()
            
            self.white_move_entry.delete(0, tk.END)
            
        except (ValueError, AssertionError) as e:
            self.log(f"✗ Error: {e}")
            messagebox.showerror("Error", str(e))
    
    def update_fen_display(self):
        """Update tampilan FEN saat ini"""
        current_fen = self.board.fen()
        self.fen_display.config(text=f"FEN saat ini: {current_fen}")
        self.save_fen_to_file(current_fen)
    
    def save_fen_to_file(self, fen):
        """Simpan FEN ke file"""
        try:
            with open("fen.txt", "w") as file:
                file.write(fen + "\n")
        except IOError as e:
            self.log(f"✗ Error menulis FEN: {e}")
    
    def save_best_move_to_file(self, best_move):
        """Simpan best move ke file"""
        try:
            with open("best.txt", "w") as file:
                file.write(best_move + "\n")
        except IOError as e:
            self.log(f"✗ Error menulis best move: {e}")
    
    def log(self, message):
        """Tambahkan message ke output console"""
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
    
    def on_closing(self):
        """Cleanup saat aplikasi ditutup"""
        if self.auto_clicker:
            self.auto_clicker.stop()
        if self.engine:
            self.engine.quit()
        self.root.destroy()
    
    def run(self):
        """Jalankan aplikasi"""
        self.root.mainloop()


def main():
    """Entry point aplikasi"""
    # KONFIGURASI: Sesuaikan path Stockfish Anda di sini
    STOCKFISH_PATH = "stockfish\\stockfish-windows-x86-64-avx2.exe"
    SYZYGY_PATH = ""  # Opsional, kosongkan jika tidak ada
    
    # Validasi Stockfish path
    if not os.path.exists(STOCKFISH_PATH):
        print(f"ERROR: Stockfish tidak ditemukan di: {STOCKFISH_PATH}")
        print("Silakan update STOCKFISH_PATH di main.py")
        input("Press Enter to exit...")
        return
    
    print("="*60)
    print("Chess Bot - Integrated Application")
    print("="*60)
    print()
    
    # Jalankan aplikasi
    app = ChessBot(STOCKFISH_PATH, SYZYGY_PATH)
    app.run()


if __name__ == "__main__":
    main()
