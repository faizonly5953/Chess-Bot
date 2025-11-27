"""
Chess Bot - Main Application
Integrated GUI, Stockfish Engine, and Auto-Clicker

How to use:
1. Run: python main.py
2. Click "Calibrate Grid" if first time (or coordinates changed)
3. Enter FEN and click "Start from FEN"
4. Bot will automatically analyze and click best moves
"""

import tkinter as tk
from tkinter import messagebox, ttk
import chess
import threading
import time
import os
from pathlib import Path

from engine import StockfishEngine
from autoclicker import AutoClicker
from calibration import GridCalibrator

DEFAULT_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

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
        self.api_mode_active = False  # True jika sedang menerima moves dari API
        
        # GUI
        self.root = None
        self.setup_gui()
        
    def setup_gui(self):
        """Setup main GUI window with tabs"""
        self.root = tk.Tk()
        self.root.title("Chess Bot")
        self.root.geometry("650x650")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.attributes('-topmost', True)
        
        # Header
        header = tk.Label(self.root, text="Chess Bot", 
                         font=('Arial', 18, 'bold'))
        header.pack(pady=10)
        
        # Create Tab Control
        self.tab_control = ttk.Notebook(self.root)
        
        # Create Tabs
        self.tab_focus = ttk.Frame(self.tab_control)
        self.tab_config = ttk.Frame(self.tab_control)
        self.tab_api = ttk.Frame(self.tab_control)
        self.tab_output = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_focus, text='Focus Mode')
        self.tab_control.add(self.tab_config, text='Configuration')
        self.tab_control.add(self.tab_api, text='API Server')
        self.tab_control.add(self.tab_output, text='Output Log')
        
        self.tab_control.pack(expand=1, fill='both', padx=10, pady=5)
        
        # Setup each tab
        self.setup_focus_tab()
        self.setup_config_tab()
        self.setup_api_tab()
        self.setup_output_tab()
        
        # Initialize engine
        self.log("Initializing Stockfish engine...")
        try:
            self.engine = StockfishEngine(self.stockfish_path, self.syzygy_path)
            self.log("✓ Stockfish engine ready")
        except Exception as e:
            self.log(f"✗ Error initializing Stockfish: {e}")
            messagebox.showerror("Error", f"Failed to initialize Stockfish:\n{e}")
        
        # Try to load existing grid config
        self.load_grid_config()
    
    def setup_focus_tab(self):
        """Setup minimalist Focus Mode tab"""
        # Board Orientation
        orient_frame = tk.Frame(self.tab_focus)
        orient_frame.pack(pady=10)
        
        tk.Label(orient_frame, text="Board Perspective:", 
                font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=5)
        
        self.board_flip_var = tk.BooleanVar(value=False)
        tk.Radiobutton(orient_frame, text="Normal (White bottom)", 
                      variable=self.board_flip_var, value=False,
                      command=self.update_board_orientation).grid(row=1, column=0, padx=10)
        tk.Radiobutton(orient_frame, text="Flipped (Black bottom)", 
                      variable=self.board_flip_var, value=True,
                      command=self.update_board_orientation).grid(row=1, column=1, padx=10)
        
        # FEN Input
        fen_frame = tk.LabelFrame(self.tab_focus, text="Position", 
                                  font=('Arial', 10, 'bold'), padx=10, pady=10)
        fen_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.fen_entry_focus = tk.Entry(fen_frame, width=55, font=('Arial', 10))
        self.fen_entry_focus.pack(pady=5)
        
        btn_frame = tk.Frame(fen_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Start Default", 
                 command=self.start_default_fen,
                 font=('Arial', 10, 'bold'),
                 bg='#2196F3', fg='white', width=12).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Start from FEN", 
                 command=self.start_from_fen_focus,
                 font=('Arial', 10, 'bold'),
                 bg='#4CAF50', fg='white', width=12).pack(side=tk.LEFT, padx=5)
        
        # Current FEN Display
        self.fen_display_focus = tk.Label(self.tab_focus, text="Current FEN: -", 
                                         font=('Arial', 8), wraplength=580, fg='gray')
        self.fen_display_focus.pack(pady=5)
        
        # Move Input
        self.move_frame = tk.LabelFrame(self.tab_focus, text="Your Move (SAN) - Manual Mode", 
                                   font=('Arial', 10, 'bold'), padx=10, pady=10)
        self.move_frame.pack(pady=10, padx=20, fill=tk.X)
        
        input_frame = tk.Frame(self.move_frame)
        input_frame.pack(pady=5)
        
        self.move_entry_focus = tk.Entry(input_frame, width=20, 
                                         font=('Arial', 14, 'bold'),
                                         justify='center')
        self.move_entry_focus.pack(side=tk.LEFT, padx=5)
        self.move_entry_focus.bind("<Return>", self.add_move_focus)
        self.move_entry_focus.focus()
        
        self.move_button = tk.Button(input_frame, text="→", 
                 command=self.add_move_focus,
                 font=('Arial', 14, 'bold'),
                 width=3, bg='#FF9800')
        self.move_button.pack(side=tk.LEFT, padx=5)
        
        # Move Display
        display_frame = tk.Frame(self.tab_focus)
        display_frame.pack(pady=10)
        
        tk.Label(display_frame, text="Opponent Move:", 
                font=('Arial', 9)).grid(row=0, column=0, sticky='e', padx=5)
        self.opponent_move_label = tk.Label(display_frame, text="-", 
                                       font=('Arial', 12, 'bold'),
                                       fg='#FF5722')
        self.opponent_move_label.grid(row=0, column=1, sticky='w')
        
        tk.Label(display_frame, text="Our Move:", 
                font=('Arial', 9)).grid(row=1, column=0, sticky='e', padx=5)
        self.our_move_label = tk.Label(display_frame, text="-", 
                                             font=('Arial', 14, 'bold'),
                                             fg='#4CAF50')
        self.our_move_label.grid(row=1, column=1, sticky='w')
        
        # API Mode indicator
        self.api_mode_label = tk.Label(self.tab_focus, text="", 
                                       font=('Arial', 8, 'italic'), fg='blue')
        self.api_mode_label.pack(pady=2)
        
        # Auto-clicker controls
        clicker_frame = tk.Frame(self.tab_focus)
        clicker_frame.pack(pady=10)
        
        self.auto_click_var = tk.BooleanVar(value=False)
        tk.Checkbutton(clicker_frame, text="Auto-Clicker Enabled", 
                      variable=self.auto_click_var,
                      command=self.toggle_auto_clicker,
                      font=('Arial', 9, 'bold'),
                      fg='#FF5722').pack(side=tk.LEFT, padx=5)
        
        self.stop_clicker_btn = tk.Button(clicker_frame, text="⏹ Stop Auto-Clicker",
                                         command=self.stop_auto_clicker,
                                         font=('Arial', 9, 'bold'),
                                         bg='#F44336', fg='white',
                                         state=tk.DISABLED)
        self.stop_clicker_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_config_tab(self):
        """Setup Configuration tab"""
        # Calibration Section
        calib_frame = tk.LabelFrame(self.tab_config, text="Grid Calibration", 
                                    font=('Arial', 11, 'bold'), padx=15, pady=10)
        calib_frame.pack(pady=10, padx=20, fill=tk.X)
        
        btn_frame = tk.Frame(calib_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Calibrate New Grid", 
                 command=self.calibrate_grid, 
                 font=('Arial', 10), width=18).pack(side=tk.LEFT, padx=5)
                 
        tk.Button(btn_frame, text="Load Config", 
                 command=self.load_grid_config, 
                 font=('Arial', 10), width=18).pack(side=tk.LEFT, padx=5)
        
        self.calib_status = tk.Label(calib_frame, text="Status: Not calibrated", 
                                     fg="red", font=('Arial', 9))
        self.calib_status.pack(pady=5)
        
        # Engine Settings
        engine_frame = tk.LabelFrame(self.tab_config, text="Engine Settings", 
                                     font=('Arial', 11, 'bold'), padx=15, pady=10)
        engine_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(engine_frame, text="Stockfish Path:", 
                font=('Arial', 9)).pack(anchor='w')
        path_label = tk.Label(engine_frame, text=self.stockfish_path, 
                             font=('Arial', 8), fg='gray', wraplength=550)
        path_label.pack(anchor='w', pady=2)
        
        # Elo Limiting
        tk.Label(engine_frame, text="", font=('Arial', 2)).pack()  # Spacer
        
        self.limit_strength_var = tk.BooleanVar(value=False)
        limit_cb = tk.Checkbutton(engine_frame, text="Enable UCI_LimitStrength (Human-like play)",
                                 variable=self.limit_strength_var, font=('Arial', 9, 'bold'))
        limit_cb.pack(anchor='w', pady=5)
        
        elo_frame = tk.Frame(engine_frame)
        elo_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(elo_frame, text="UCI_Elo:", font=('Arial', 9)).pack(side=tk.LEFT)
        
        self.elo_var = tk.IntVar(value=1500)
        elo_slider = tk.Scale(elo_frame, from_=800, to=3190, orient=tk.HORIZONTAL,
                             variable=self.elo_var, length=300, 
                             command=lambda v: self.elo_label.config(text=str(self.elo_var.get())))
        elo_slider.pack(side=tk.LEFT, padx=10)
        
        self.elo_label = tk.Label(elo_frame, text="1500", font=('Arial', 10, 'bold'), width=6)
        self.elo_label.pack(side=tk.LEFT, padx=5)
        
        # Apply button
        apply_btn = tk.Button(engine_frame, text="Apply Settings", 
                             command=self.apply_engine_settings,
                             font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white',
                             padx=20, pady=5)
        apply_btn.pack(pady=10)
        
        # Elo guide
        elo_guide = tk.Label(engine_frame, 
                            text="800-1200: Beginner | 1300-1500: Intermediate | 1600-1900: Club | 2000-2300: Expert | 2400+: Master",
                            font=('Arial', 7), fg='gray')
        elo_guide.pack(anchor='w')
        
        # Click Mode Settings
        click_frame = tk.LabelFrame(self.tab_config, text="Auto-Clicker Mode", 
                                    font=('Arial', 11, 'bold'), padx=15, pady=10)
        click_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(click_frame, text="Click Style:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=5)
        
        self.instant_click_var = tk.BooleanVar(value=False)
        tk.Radiobutton(click_frame, text="Simulate Human Click (with mouse movement & delays)",
                      variable=self.instant_click_var, value=False,
                      command=self.update_click_mode,
                      font=('Arial', 9)).pack(anchor='w', padx=20)
        tk.Radiobutton(click_frame, text="Instant Click (direct, no animation)",
                      variable=self.instant_click_var, value=True,
                      command=self.update_click_mode,
                      font=('Arial', 9)).pack(anchor='w', padx=20)
        
        # Instructions
        info_frame = tk.LabelFrame(self.tab_config, text="Quick Start Guide", 
                                   font=('Arial', 11, 'bold'), padx=15, pady=10)
        info_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        instructions = """1. Calibrate Grid: Click "Calibrate New Grid" and select chess board corners
2. Choose Perspective: Normal (White bottom) or Flipped (Black bottom)
3. Start Position: Use "Start Default" or enter custom FEN
4. Enable Auto-Clicker: Check the box to auto-click moves
5. Enter Moves: Use SAN notation (e4, Nf3, Bb5, O-O, etc.)
6. Switch to Focus Mode tab for minimal interface"""
        
        tk.Label(info_frame, text=instructions, 
                font=('Arial', 9), justify='left').pack(anchor='w')
    
    def setup_api_tab(self):
        """Setup API Server tab untuk auto-play dari external source"""
        tk.Label(self.tab_api, text="API Server Mode", 
                font=('Arial', 13, 'bold')).pack(pady=10)
        
        # Server Status
        status_frame = tk.LabelFrame(self.tab_api, text="Server Status", 
                                     font=('Arial', 11, 'bold'), padx=15, pady=10)
        status_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.api_server_running = False
        self.api_server_thread = None
        
        self.api_status_label = tk.Label(status_frame, text="● Stopped", 
                                        font=('Arial', 12, 'bold'), fg='red')
        self.api_status_label.pack(pady=5)
        
        # Server Configuration
        config_frame = tk.LabelFrame(self.tab_api, text="Server Configuration", 
                                     font=('Arial', 11, 'bold'), padx=15, pady=10)
        config_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Host
        host_frame = tk.Frame(config_frame)
        host_frame.pack(fill=tk.X, pady=5)
        tk.Label(host_frame, text="Host:", font=('Arial', 9), width=8).pack(side=tk.LEFT)
        self.api_host_var = tk.StringVar(value='0.0.0.0')
        tk.Entry(host_frame, textvariable=self.api_host_var, 
                font=('Arial', 10), width=20).pack(side=tk.LEFT, padx=5)
        tk.Label(host_frame, text="(0.0.0.0 = all interfaces)", 
                font=('Arial', 8), fg='gray').pack(side=tk.LEFT)
        
        # Port
        port_frame = tk.Frame(config_frame)
        port_frame.pack(fill=tk.X, pady=5)
        tk.Label(port_frame, text="Port:", font=('Arial', 9), width=8).pack(side=tk.LEFT)
        self.api_port_var = tk.IntVar(value=5000)
        tk.Spinbox(port_frame, from_=1024, to=65535, textvariable=self.api_port_var,
                  font=('Arial', 10), width=18).pack(side=tk.LEFT, padx=5)
        
        # Control Buttons
        btn_frame = tk.Frame(self.tab_api)
        btn_frame.pack(pady=15)
        
        self.start_api_btn = tk.Button(btn_frame, text="▶ Start Server", 
                                      command=self.start_api_server,
                                      font=('Arial', 11, 'bold'),
                                      bg='#4CAF50', fg='white', width=15)
        self.start_api_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_api_btn = tk.Button(btn_frame, text="■ Stop Server", 
                                     command=self.stop_api_server,
                                     font=('Arial', 11, 'bold'),
                                     bg='#F44336', fg='white', width=15,
                                     state=tk.DISABLED)
        self.stop_api_btn.pack(side=tk.LEFT, padx=5)
        
        # Reset Manual Mode Button
        reset_frame = tk.Frame(self.tab_api)
        reset_frame.pack(pady=5)
        
        tk.Button(reset_frame, text="🔄 Reset to Manual Mode",
                 command=self.reset_manual_mode,
                 font=('Arial', 10, 'bold'),
                 bg='#FF9800', fg='white', width=25).pack()
        
        tk.Label(reset_frame, text="Use this to re-enable manual move input",
                font=('Arial', 8), fg='gray').pack(pady=2)
        
        # API Info
        info_frame = tk.LabelFrame(self.tab_api, text="API Endpoints", 
                                   font=('Arial', 11, 'bold'), padx=15, pady=10)
        info_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.api_url_text = tk.Text(info_frame, height=12, font=('Consolas', 9), wrap=tk.WORD)
        self.api_url_text.pack(fill=tk.BOTH, expand=True)
        
        api_info = """Kirim POST request dari browser/script ke:

POST /api/receive-moves
Body (JSON):
{
  "moves": [
    {"no": 1, "white_move": "e4", "black_move": "e5"},
    {"no": 2, "white_move": "Nf3", "black_move": null}
  ]
}

Server akan:
1. Update posisi board di aplikasi
2. Analisis dengan Stockfish
3. Tampilkan best move
4. Auto-click jika enabled

GET /api/health - Check server status
"""
        self.api_url_text.insert('1.0', api_info)
        self.api_url_text.config(state=tk.DISABLED)
    
    def setup_output_tab(self):
        """Setup Output Log tab"""
        tk.Label(self.tab_output, text="System Log", 
                font=('Arial', 11, 'bold')).pack(pady=10)
        
        output_frame = tk.Frame(self.tab_output)
        output_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(output_frame, 
                                   yscrollcommand=scrollbar.set,
                                   font=('Consolas', 9), wrap=tk.WORD)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output_text.yview)
        
        # Clear button
        tk.Button(self.tab_output, text="Clear Log", 
                 command=self.clear_log,
                 font=('Arial', 9)).pack(pady=5)
    
    def clear_log(self):
        """Clear output log"""
        self.output_text.delete("1.0", tk.END)
        self.log("Log cleared")
    
    def start_default_fen(self):
        """Start from default starting position"""
        self.fen_entry_focus.delete(0, tk.END)
        self.fen_entry_focus.insert(0, DEFAULT_FEN)
        self.start_from_fen_focus()
    
    def start_from_fen_focus(self):
        """Start from FEN in focus mode"""
        fen = self.fen_entry_focus.get().strip()
        if not fen:
            self.log("✗ FEN cannot be empty")
            return
        
        try:
            self.board.set_fen(fen)
            self.save_fen_to_file(fen)
            
            if self.engine:
                self.engine.set_position(fen)
            
            # Auto-enable auto-clicker in Focus Mode if calibrated
            if self.auto_clicker and not self.auto_click_var.get():
                self.auto_click_var.set(True)
                self.auto_clicker.start()
                self.log("✓ Auto-clicker enabled (Focus Mode)")
            
            self.update_fen_display_focus()
            self.process_initial_move_focus(fen)
            self.move_entry_focus.focus()
            
        except Exception as e:
            self.log(f"✗ Error: {e}")
            messagebox.showerror("Error", str(e))
    
    def process_initial_move_focus(self, fen):
        """Process initial move in focus mode"""
        if not self.engine:
            return
            
        best_move_uci = self.engine.get_best_move(fen)
        if not best_move_uci:
            self.log("✗ Cannot get best move")
            return
            
        self.save_best_move_to_file(best_move_uci)
        
        move = chess.Move.from_uci(best_move_uci)
        best_move_san = self.board.san(move)
        self.board.push(move)
        
        if self.engine:
            self.engine.set_position(self.board.fen())
        
        self.our_move_label.config(text=best_move_san)
        self.opponent_move_label.config(text="-")
        self.update_fen_display_focus()
        self.log(f"✓ Best move: {best_move_san} ({best_move_uci})")
    
    def add_move_focus(self, event=None):
        """Add move in focus mode"""
        move_san = self.move_entry_focus.get().strip()
        if not move_san:
            return
            
        try:
            move = self.board.parse_san(move_san)
            assert self.board.is_legal(move), f"Illegal move '{move_san}'"
            
            self.board.push(move)
            if self.engine:
                self.engine.set_position(self.board.fen())
            
            self.opponent_move_label.config(text=move_san)
            self.log(f"→ Your move (manual): {move_san}")
            
            # Get our bot's response
            if self.engine:
                our_move_uci = self.engine.get_best_move(self.board.fen())
                if our_move_uci:
                    self.save_best_move_to_file(our_move_uci)
                    
                    our_move = chess.Move.from_uci(our_move_uci)
                    our_san = self.board.san(our_move)
                    
                    self.board.push(our_move)
                    self.engine.set_position(self.board.fen())
                    
                    self.our_move_label.config(text=our_san)
                    self.log(f"← Our response: {our_san} ({our_move_uci})")
                    self.update_fen_display_focus()
            
            self.move_entry_focus.delete(0, tk.END)
            self.move_entry_focus.focus()
            
        except (ValueError, AssertionError) as e:
            self.log(f"✗ Error: {e}")
            self.move_entry_focus.delete(0, tk.END)
    
    def update_fen_display_focus(self):
        """Update FEN display in focus mode"""
        current_fen = self.board.fen()
        self.fen_display_focus.config(text=f"Current FEN: {current_fen}")
        self.save_fen_to_file(current_fen)
        
    def calibrate_grid(self):
        """Calibrate chess board grid"""
        self.log("Starting grid calibration...")
        coords = self.calibrator.select_area()
        if coords:
            # Save with current Elo settings
            elo_limit = self.limit_strength_var.get()
            elo_value = self.elo_var.get()
            self.calibrator.save_config(elo_limit, elo_value)
            
            self.setup_auto_clicker()
            self.calib_status.config(text=f"Status: Saved ({coords['x1']},{coords['y1']}) to ({coords['x2']},{coords['y2']})", 
                                    fg="green")
            self.log(f"✓ Grid calibrated: {coords}")
        else:
            self.log("✗ Calibration cancelled")
            
    def load_grid_config(self):
        """Load grid configuration from file"""
        coords = self.calibrator.load_config()
        if coords:
            # Apply loaded Elo settings
            if 'elo_limit' in coords:
                self.limit_strength_var.set(coords['elo_limit'])
            if 'elo_value' in coords:
                self.elo_var.set(coords['elo_value'])
                self.elo_label.config(text=str(coords['elo_value']))
            
            # Update engine with loaded settings
            self.apply_engine_settings()
            
            self.setup_auto_clicker()
            self.calib_status.config(text=f"Status: Loaded ({coords['x1']},{coords['y1']}) to ({coords['x2']},{coords['y2']})", 
                                    fg="green")
            self.log(f"✓ Grid config loaded: {coords}")
        else:
            self.log("Grid config not found. Please calibrate.")
            
    def update_board_orientation(self):
        """Update board orientation and auto-clicker"""
        self.board_flipped = self.board_flip_var.get()
        if self.auto_clicker:
            self.auto_clicker.set_board_flipped(self.board_flipped)
        
        orientation = "Flipped (Black bottom)" if self.board_flipped else "Normal (White bottom)"
        self.log(f"✓ Board perspective: {orientation}")
    
    def apply_engine_settings(self):
        """Apply engine Elo settings and reset engine"""
        if not self.engine:
            self.log("✗ Engine not initialized")
            return
            
        limit_enabled = self.limit_strength_var.get()
        elo_value = self.elo_var.get()
        
        # Update label
        self.elo_label.config(text=str(elo_value))
        
        # Send UCI commands in correct order
        self.engine.send_command(f"setoption name UCI_LimitStrength value {str(limit_enabled).lower()}")
        self.engine.send_command(f"setoption name UCI_Elo value {elo_value}")
        self.engine.send_command("isready")
        self.engine.wait_for_response("readyok")
        
        # Reset engine state with ucinewgame
        self.engine.send_command("ucinewgame")
        self.engine.send_command("isready")
        self.engine.wait_for_response("readyok")
        
        if limit_enabled:
            self.log(f"✓ Engine strength set to Elo {elo_value} (applied & reset)")
        else:
            self.log("✓ Engine strength: Full power (unlimited, applied & reset)")
    
    def setup_auto_clicker(self):
        """Setup auto-clicker with calibrated coordinates"""
        if not self.calibrator.coordinates:
            return
            
        coords = self.calibrator.coordinates
        instant_mode = self.instant_click_var.get()
        self.auto_clicker = AutoClicker(
            coords['x1'], coords['y1'], 
            coords['x2'], coords['y2'],
            instant_mode=instant_mode
        )
        self.auto_clicker.set_board_flipped(self.board_flipped)
        mode_str = "Instant" if instant_mode else "Human Simulation"
        self.log(f"✓ Auto-clicker ready (Mode: {mode_str})")
    
    def update_click_mode(self):
        """Update auto-clicker mode when radio button changes"""
        if self.auto_clicker:
            instant_mode = self.instant_click_var.get()
            self.auto_clicker.set_instant_mode(instant_mode)
            mode_str = "Instant" if instant_mode else "Human Simulation"
            self.log(f"✓ Click mode changed to: {mode_str}")
        
    def toggle_auto_clicker(self):
        """Toggle auto-clicker on/off"""
        if self.auto_click_var.get():
            if not self.auto_clicker:
                messagebox.showwarning("Warning", 
                    "Please calibrate grid first!")
                self.auto_click_var.set(False)
                return
                
            self.auto_clicker.start()
            self.stop_clicker_btn.config(state=tk.NORMAL)
            self.log("✓ Auto-clicker enabled")
        else:
            if self.auto_clicker:
                self.auto_clicker.stop()
                self.stop_clicker_btn.config(state=tk.DISABLED)
                self.log("✓ Auto-clicker disabled")
    
    def stop_auto_clicker(self):
        """Stop auto-clicker immediately"""
        if self.auto_clicker:
            self.auto_clicker.stop()
            self.auto_click_var.set(False)
            self.stop_clicker_btn.config(state=tk.DISABLED)
            self.log("🛑 Auto-clicker stopped")
        else:
            self.log("⚠ Auto-clicker not running")
    
    def _toggle_manual_input(self, enable):
        """Enable/disable manual move input"""
        state = tk.NORMAL if enable else tk.DISABLED
        self.move_entry_focus.config(state=state)
        self.move_button.config(state=state)
        
        if enable:
            self.move_frame.config(text="Your Move (SAN) - Manual Mode")
            self.api_mode_label.config(text="")
        else:
            self.move_frame.config(text="Your Move (SAN) - API MODE ACTIVE")
            self.api_mode_label.config(text="🌐 Receiving moves from browser - Manual input disabled")
    
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
    
    def start_api_server(self):
        """Start API server di background thread"""
        if self.api_server_running:
            messagebox.showwarning("Warning", "Server sudah berjalan!")
            return
        
        try:
            host = self.api_host_var.get()
            port = self.api_port_var.get()
            
            assert host, "Host tidak boleh kosong"
            assert 1024 <= port <= 65535, "Port harus antara 1024-65535"
            
            # Import API server module
            import api_server
            
            # Set callback untuk auto-execute moves
            def move_callback(fen, last_move, last_move_color):
                """Callback dipanggil dari API ketika menerima moves dari browser"""
                self.root.after(0, self._execute_api_move, fen, last_move, last_move_color)
            
            api_server.set_move_callback(move_callback)
            
            # Start server di background thread
            self.api_server_thread = threading.Thread(
                target=api_server.run_server,
                args=(host, port, False),
                daemon=True
            )
            self.api_server_thread.start()
            
            self.api_server_running = True
            self.api_status_label.config(text="● Running", fg='green')
            self.start_api_btn.config(state=tk.DISABLED)
            self.stop_api_btn.config(state=tk.NORMAL)
            
            url = f"http://{host}:{port}"
            self.log(f"✓ API Server started at {url}")
            
            # Update URL di text box
            self.api_url_text.config(state=tk.NORMAL)
            current_text = self.api_url_text.get('1.0', tk.END)
            updated_text = f"Server URL: {url}\n\n" + current_text
            self.api_url_text.delete('1.0', tk.END)
            self.api_url_text.insert('1.0', updated_text)
            self.api_url_text.config(state=tk.DISABLED)
            
        except AssertionError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Gagal start server: {e}")
            self.log(f"✗ Error starting API server: {e}")
    
    def stop_api_server(self):
        """Stop API server"""
        if not self.api_server_running:
            messagebox.showwarning("Warning", "Server tidak berjalan!")
            return
        
        # Note: Flask tidak bisa di-stop dengan mudah dari thread
        # Alternatif: restart aplikasi atau gunakan werkzeug shutdown
        messagebox.showinfo("Info", 
                           "Server berjalan di background thread.\n"
                           "Untuk stop server, restart aplikasi.")
        self.log("⚠ API Server masih running (restart aplikasi untuk stop)")
    
    def reset_manual_mode(self):
        """Reset ke manual mode dan enable input"""
        self.api_mode_active = False
        self._toggle_manual_input(True)
        self.opponent_move_label.config(text="-")
        self.our_move_label.config(text="-")
        self.log("🔄 Reset to Manual Mode - You can now input moves manually")
    
    def _execute_api_move(self, fen, last_move, last_move_color):
        """Execute posisi yang diterima dari API (dipanggil via callback)"""
        try:
            # Aktifkan API mode dan disable manual input
            if not self.api_mode_active:
                self.api_mode_active = True
                self._toggle_manual_input(False)
            
            self.log(f"📡 API: Received position from browser")
            
            # Update board state
            self.board = chess.Board(fen)
            
            # Update GUI displays
            self.fen_display_focus.config(text=f"Current FEN: {fen}")
            
            # Determine siapa yang baru jalan (opponent) berdasarkan last_move_color
            current_turn = self.board.turn  # chess.WHITE atau chess.BLACK (giliran selanjutnya)
            
            # Tentukan siapa kita berdasarkan board perspective
            # Jika flipped (Black bottom), kita main sebagai Black
            # Jika normal (White bottom), kita main sebagai White
            we_are_white = not self.board_flipped
            we_are_color = "white" if we_are_white else "black"
            
            opponent_just_moved = last_move is not None and last_move_color is not None
            
            if opponent_just_moved:
                # Cek apakah last move adalah dari opponent
                is_opponent_move = (last_move_color != we_are_color)
                
                if is_opponent_move:
                    self.opponent_move_label.config(text=last_move)
                    self.log(f"📡 API: Opponent ({last_move_color}) played = {last_move}")
                    self.api_mode_label.config(text=f"🌐 Receiving moves from browser (We are {we_are_color})...")
                else:
                    # Ini move kita sendiri yang di-echo kembali dari browser
                    self.log(f"📡 API: Echo of our move = {last_move}")
                    return  # Skip processing, ini bukan opponent move
            
            # Save FEN to file
            with open("fen.txt", "w") as f:
                f.write(fen + "\n")
            
            # Cek apakah giliran kita untuk respond
            its_our_turn = (we_are_white and current_turn == chess.WHITE) or \
                          (not we_are_white and current_turn == chess.BLACK)
            
            if its_our_turn and self.engine and opponent_just_moved:
                self.log(f"🤖 Our turn! Calculating best move...")
                
                # Analisis posisi dengan Stockfish
                best_move_uci = self.engine.get_best_move(fen)
                if best_move_uci:
                    # Convert UCI to SAN
                    move_obj = chess.Move.from_uci(best_move_uci)
                    best_move_san = self.board.san(move_obj)
                    
                    # Apply move to board untuk update state
                    self.board.push(move_obj)
                    
                    self.our_move_label.config(text=best_move_san)
                    self.log(f"✓ Our move: {best_move_san} (UCI: {best_move_uci})")
                    
                    # Save to file untuk auto-clicker
                    with open("best.txt", "w") as f:
                        f.write(best_move_uci + "\n")
                    
                    # Update FEN after our move
                    new_fen = self.board.fen()
                    self.fen_display_focus.config(text=f"Current FEN: {new_fen}")
                    
                    with open("fen.txt", "w") as f:
                        f.write(new_fen + "\n")
                    
                    # Auto-clicker akan execute jika enabled
                    if self.auto_click_var.get():
                        self.log(f"🖱️ Auto-clicker akan execute {best_move_san}...")
                    else:
                        self.log(f"⚠ Auto-clicker disabled. Enable untuk auto-click.")
            else:
                if not its_our_turn:
                    turn_color = "White" if current_turn == chess.WHITE else "Black"
                    self.log(f"⏳ Waiting for opponent... (Turn: {turn_color})")
            
            self.log(f"✓ Position updated via API")
            
        except Exception as e:
            self.log(f"✗ Error executing API position: {e}")
            import traceback
            self.log(traceback.format_exc())
    
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
        if self.api_server_running:
            self.log("⚠ API Server masih running di background")
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
