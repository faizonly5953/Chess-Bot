"""
Module untuk mengelola Stockfish engine
"""
import subprocess
import chess

MAX_RESPONSE_LINES = 1000
MAX_MOVE_LENGTH = 10

class StockfishEngine:
    def __init__(self, path, syzygy_path=""):
        assert path, "Stockfish path harus diisi"
        self.path = path
        self.syzygy_path = syzygy_path
        self.process = None
        self._start_engine()
        
    def _start_engine(self):
        self.process = subprocess.Popen(
            self.path,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=1
        )
        assert self.process.stdin is not None, "STDIN harus tersedia"
        assert self.process.stdout is not None, "STDOUT harus tersedia"
        
        self.send_command("uci")
        self.send_command("setoption name Threads value 4")
        self.send_command("setoption name Skill Level value 20")
        self.send_command("setoption name Move Overhead value 10")
        self.send_command("setoption name MultiPV value 1")
        if self.syzygy_path:
            self.send_command(f"setoption name SyzygyPath value {self.syzygy_path}")
        self.send_command("isready")
        self.wait_for_response("readyok")
        
    def send_command(self, cmd):
        assert cmd, "Command tidak boleh kosong"
        assert len(cmd) < 500, "Command terlalu panjang"
        if self.process.stdin:
            self.process.stdin.write(f"{cmd}\n")
            self.process.stdin.flush()
        
    def get_best_move(self, fen, depth=20):
        assert fen, "FEN tidak boleh kosong"
        assert 1 <= depth <= 30, "Depth harus antara 1-30"
        
        self.send_command(f"position fen {fen}")
        self.send_command(f"go depth {depth}")
        
        max_iterations = MAX_RESPONSE_LINES
        for iteration in range(max_iterations):
            if not self.process.stdout:
                return None
            response = self.process.stdout.readline().strip()
            if response.startswith("bestmove"):
                parts = response.split()
                assert len(parts) >= 2, "Response bestmove tidak valid"
                best_move = parts[1]
                assert len(best_move) <= MAX_MOVE_LENGTH, "Move terlalu panjang"
                return best_move
        
        return None
                
    def wait_for_response(self, expected):
        assert expected, "Expected response tidak boleh kosong"
        
        max_iterations = MAX_RESPONSE_LINES
        for iteration in range(max_iterations):
            if not self.process.stdout:
                return
            response = self.process.stdout.readline().strip()
            if response == expected:
                return
                
    def set_position(self, fen):
        assert fen, "FEN tidak boleh kosong"
        self.send_command(f"position fen {fen}")
        
    def quit(self):
        if self.process:
            self.send_command("quit")
            self.process.terminate()
            self.process = None
