import tkinter as tk
import chess
import subprocess
import threading
import queue
import time

class StockfishProcess:
    def __init__(self, path):
        print("Inisialisasi Stockfish...")
        self.process = subprocess.Popen(
            path,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=1
        )
        # Initialize engine with default parameters
        self.send_command("uci")
        self.send_command("setoption name Threads value 4")
        self.send_command("setoption name Skill Level value 20")
        self.send_command("setoption name Move Overhead value 10")
        self.send_command("setoption name MultiPV value 1")
        self.send_command(f"setoption name SyzygyPath value D:\\3-4-5")
        self.send_command("isready")
        self.wait_for_response("readyok")
        
    def send_command(self, cmd):
        print(f"Sending command: {cmd}")  # Debugging output
        self.process.stdin.write(f"{cmd}\n")
        self.process.stdin.flush()
        
    def get_best_move(self, fen, depth=20):
        print(f"Mengambil best move untuk FEN: {fen} dengan kedalaman {depth}")  # Debugging output
        self.send_command(f"position fen {fen}")
        self.send_command(f"go depth {depth}")
        
        while True:
            response = self.process.stdout.readline().strip()
            print(f"Response dari Stockfish: {response}")  # Debugging output
            if response.startswith("bestmove"):
                best_move = response.split()[1]
                self.save_best_move_to_file(best_move)  # Save best move to file
                return best_move
                
    def wait_for_response(self, expected):
        print(f"Menunggu response untuk: {expected}")  # Debugging output
        while True:
            response = self.process.stdout.readline().strip()
            print(response)  # Debugging output
            if response == expected:
                return
                
    def set_position(self, fen):
        print(f"Set posisi ke FEN: {fen}")  # Debugging output
        self.send_command(f"position fen {fen}")
        
    def make_moves_from_position(self, moves):
        moves_str = " ".join(moves)
        print(f"Memainkan langkah: {moves_str}")  # Debugging output
        self.send_command(f"position fen {self.current_fen} moves {moves_str}")
        
    def quit(self):
        print("Menghentikan Stockfish...")  # Debugging output
        self.send_command("quit")
        self.process.terminate()

    def save_best_move_to_file(self, best_move):
        print(f"Menyimpan best move ke file: {best_move}")  # Debugging output
        with open("best.txt", "a") as file:  # Open file in append mode
            file.write(best_move + "\n")  # Write best move followed by a newline

def save_fen_to_file(fen):
    """
    Menyimpan FEN yang diinput user ke dalam file fen.txt
    """
    print(f"Menyimpan FEN ke file: {fen}")  # Debugging output
    with open("fen.txt", "a") as file:  # Open file in append mode
        file.write(fen + "\n")  # Write FEN followed by a newline
        
# Inisialisasi Stockfish dan Board
stockfish_path = "C:\\Users\\LENOVO\\Documents\\Developing\\python\\stockfish\\stockfish-windows-x86-64-avx2.exe"
print("Memulai proses Stockfish...")
stockfish = StockfishProcess(stockfish_path)
board = chess.Board()

def start_from_fen():
    try:
        fen = fen_entry.get().strip()
        print(f"Memulai dari FEN: {fen}")  # Debugging output
        
        # Validasi FEN sebelum menyimpan
        board.set_fen(fen)  # This will raise an exception if FEN is invalid
        
        # Simpan FEN yang valid ke file
        save_fen_to_file(fen)
        
        stockfish.set_position(fen)
        update_fen_display()

        if board.turn == chess.WHITE:
            white_best_move = stockfish.get_best_move(fen)
            if white_best_move:
                board.push_uci(white_best_move)
                stockfish.set_position(board.fen())
                white_move_label.config(text=f"Langkah Pertama: {white_best_move}")
                update_fen_display()
                black_move_label.config(text="Masukkan Langkah Selanjutnya")
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, "Silakan masukkan Langkah Selanjutnya.\n")
        else:
            black_best_move = stockfish.get_best_move(fen)
            if black_best_move:
                board.push_uci(black_best_move)
                stockfish.set_position(board.fen())
                black_move_label.config(text=f"Langkah Black: {black_best_move}")
                update_fen_display()
                white_move_label.config(text="Giliran Putih, silakan masukkan langkah Putih.")
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, "Silakan masukkan langkah Putih.\n")
    except Exception as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"Error: {str(e)}\n")
        print(f"Error: {str(e)}")  # Debugging output

def add_white_move(event=None):
    try:
        white_move_san = white_move_entry.get().strip()
        print(f"Menambahkan langkah Putih: {white_move_san}")  # Debugging output
        white_move = board.parse_san(white_move_san)
        if not board.is_legal(white_move):
            raise ValueError(f"Langkah '{white_move_san}' tidak sah di papan ini.")
        
        board.push(white_move)
        stockfish.set_position(board.fen())

        black_best_move = stockfish.get_best_move(board.fen())
        if black_best_move:
            board.push_uci(black_best_move)
            stockfish.set_position(board.fen())
            black_move_label.config(text=f"Langkah Black: {black_best_move}")
            update_fen_display()

        white_move_entry.delete(0, tk.END)
    except ValueError as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"Error: {str(e)}\n")
        print(f"ValueError: {str(e)}")  # Debugging output
    except Exception as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"Unexpected error: {str(e)}\n")
        print(f"Unexpected error: {str(e)}")  # Debugging output

def update_fen_display():
    current_fen = board.fen()
    print(f"Memperbarui FEN: {current_fen}")  # Debugging output
    fen_display.config(text=f"FEN saat ini: {current_fen}")

def on_closing():
    print("Menutup aplikasi...")  # Debugging output
    stockfish.quit()
    root.destroy()

# Membuat window utama GUI
root = tk.Tk()
root.title("Chess FEN Analyzer")
root.geometry("500x500")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Menambahkan opsi untuk menampilkan window di atas
root.attributes('-topmost', True)

# Input untuk posisi awal FEN
fen_label = tk.Label(root, text="Masukkan FEN:")
fen_label.pack(pady=5)
fen_entry = tk.Entry(root, width=50)
fen_entry.pack(pady=5)

# Tombol untuk memulai dari FEN yang dimasukkan
start_button = tk.Button(root, text="Mulai dari FEN", command=start_from_fen)
start_button.pack(pady=10)

# Display untuk FEN saat ini
fen_display = tk.Label(root, text="FEN saat ini: ")
fen_display.pack(pady=5)

# Entry untuk langkah Putih
white_move_label = tk.Label(root, text="Masukkan langkah Putih (SAN):")
white_move_label.pack(pady=5)
white_move_entry = tk.Entry(root, width=10)
white_move_entry.pack(pady=5)

# Bind tombol Enter ke fungsi add_white_move
white_move_entry.bind("<Return>", add_white_move)

# Tombol untuk menambahkan langkah Putih dan memicu langkah Hitam otomatis
white_move_button = tk.Button(root, text="Tambah Langkah Putih", command=add_white_move)
white_move_button.pack(pady=10)

# Display untuk langkah Hitam
black_move_label = tk.Label(root, text="Best Move: ")
black_move_label.pack(pady=5)

# Text widget untuk output hasil analisis
output_text = tk.Text(root, height=5, width=50)
output_text.pack(pady=10)

# Menjalankan loop utama tkinter
root.mainloop()