"""
API Server Event Listener untuk menerima moves chess dari browser/external source
Hanya menerima JSON array moves dan AUTO-EXECUTE di aplikasi (tanpa analisis Stockfish)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import threading

app = Flask(__name__)
CORS(app)  # Enable CORS untuk semua origins

# Constants untuk Power of 10 compliance
MAX_MOVES_ARRAY = 500
MAX_MOVE_LENGTH = 10
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 5000

# Callback untuk auto-execute move di aplikasi
move_callback = None
callback_lock = threading.Lock()



def set_move_callback(callback_func):
    """
    Set callback function yang akan dipanggil ketika API menerima move
    
    Args:
        callback_func: Function dengan signature callback_func(san_move, fen) -> None
    """
    global move_callback
    with callback_lock:
        move_callback = callback_func
        assert move_callback is not None, "Callback tidak boleh None"


def validate_moves_json(moves_data):
    """
    Validasi struktur JSON moves
    
    Args:
        moves_data: List of move objects
        
    Returns:
        tuple: (is_valid, error_message)
    """
    assert isinstance(moves_data, list), "Moves harus berupa array"
    assert len(moves_data) <= MAX_MOVES_ARRAY, f"Terlalu banyak moves (max: {MAX_MOVES_ARRAY})"
    
    iteration_count = 0
    for move_obj in moves_data:
        iteration_count += 1
        assert iteration_count <= MAX_MOVES_ARRAY, "Loop validation melebihi batas"
        
        assert isinstance(move_obj, dict), f"Move #{iteration_count} harus berupa object"
        assert 'no' in move_obj, f"Move #{iteration_count} harus punya field 'no'"
        assert 'white_move' in move_obj, f"Move #{iteration_count} harus punya field 'white_move'"
        assert 'black_move' in move_obj, f"Move #{iteration_count} harus punya field 'black_move'"
        
        # Validate move lengths if not None
        if move_obj['white_move'] is not None:
            assert len(move_obj['white_move']) <= MAX_MOVE_LENGTH, \
                f"White move #{iteration_count} terlalu panjang"
        if move_obj['black_move'] is not None:
            assert len(move_obj['black_move']) <= MAX_MOVE_LENGTH, \
                f"Black move #{iteration_count} terlalu panjang"
    
    return True, None


def convert_json_to_fen(moves_data):
    """
    Konversi JSON array moves ke FEN notation
    
    Args:
        moves_data: List of move objects [{"no": 1, "white_move": "e4", "black_move": "e5"}, ...]
        
    Returns:
        str: FEN string dari posisi terakhir
    """
    assert isinstance(moves_data, list), "Moves data harus list"
    
    board = chess.Board()
    move_count = 0
    
    for move_obj in moves_data:
        move_count += 1
        assert move_count <= MAX_MOVES_ARRAY, "Terlalu banyak moves dalam loop"
        
        # Apply white move
        if move_obj['white_move'] is not None:
            white_move_san = move_obj['white_move']
            assert white_move_san, "White move tidak boleh kosong"
            
            try:
                move = board.parse_san(white_move_san)
                assert move in board.legal_moves, f"White move {white_move_san} tidak legal"
                board.push(move)
            except (ValueError, AssertionError) as e:
                raise ValueError(f"Invalid white move '{white_move_san}' at move {move_obj['no']}: {str(e)}")
        
        # Apply black move
        if move_obj['black_move'] is not None:
            black_move_san = move_obj['black_move']
            assert black_move_san, "Black move tidak boleh kosong"
            
            try:
                move = board.parse_san(black_move_san)
                assert move in board.legal_moves, f"Black move {black_move_san} tidak legal"
                board.push(move)
            except (ValueError, AssertionError) as e:
                raise ValueError(f"Invalid black move '{black_move_san}' at move {move_obj['no']}: {str(e)}")
    
    fen = board.fen()
    assert fen, "FEN tidak boleh kosong"
    return fen


@app.route('/api/receive-moves', methods=['POST'])
def receive_moves():
    """
    Endpoint EVENT LISTENER - hanya terima moves dari browser dan execute di aplikasi
    TIDAK melakukan analisis Stockfish
    
    Request Body:
    {
        "moves": [
            {"no": 1, "white_move": "e4", "black_move": "e5"},
            {"no": 2, "white_move": "Nf3", "black_move": null}
        ]
    }
    
    Response:
    {
        "success": true,
        "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
        "turn": "black",
        "executed": true,
        "message": "Moves received and executed"
    }
    """
    try:
        # Validate request
        assert request.is_json, "Request harus berupa JSON"
        data = request.get_json()
        assert data is not None, "Request body kosong"
        assert 'moves' in data, "Field 'moves' diperlukan"
        
        moves = data['moves']
        
        # Validate moves structure
        validate_moves_json(moves)
        
        # Convert to FEN
        fen = convert_json_to_fen(moves)
        
        # Determine whose turn
        board = chess.Board(fen)
        turn = "white" if board.turn == chess.WHITE else "black"
        
        # Get last move for display
        last_move_san = None
        last_move_color = None  # "white" or "black"
        
        if len(moves) > 0:
            last_entry = moves[-1]
            if last_entry['black_move'] is not None:
                last_move_san = last_entry['black_move']
                last_move_color = "black"
            elif last_entry['white_move'] is not None:
                last_move_san = last_entry['white_move']
                last_move_color = "white"
        
        # AUTO-EXECUTE via callback (update GUI dengan posisi baru)
        executed = False
        if move_callback is not None:
            try:
                with callback_lock:
                    # Call callback untuk update GUI dengan FEN baru
                    move_callback(fen, last_move_san, last_move_color)
                    executed = True
            except Exception as e:
                print(f"Warning: Callback execution failed: {e}")
        
        response = {
            "success": True,
            "fen": fen,
            "turn": turn,
            "last_move": last_move_san,
            "last_move_by": last_move_color,
            "executed": executed,
            "message": "Moves received and executed in application"
        }
        
        return jsonify(response), 200
        
    except AssertionError as e:
        return jsonify({
            "success": False,
            "error": f"Validation error: {str(e)}"
        }), 400
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid move: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    callback_status = "ready" if move_callback is not None else "not_configured"
    
    return jsonify({
        "status": "ok",
        "callback": callback_status,
        "endpoints": ["/api/receive-moves", "/api/health"]
    }), 200


def run_server(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=False):
    """
    Jalankan Flask server
    
    Args:
        host: Host address (default: 0.0.0.0 untuk accept semua koneksi)
        port: Port number (default: 5000)
        debug: Debug mode (default: False)
    """
    assert host, "Host tidak boleh kosong"
    assert 1024 <= port <= 65535, "Port harus antara 1024-65535"
    
    print(f"Starting Chess Bot API Event Listener...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"\nEndpoints:")
    print(f"  POST http://{host}:{port}/api/receive-moves - Receive moves from browser")
    print(f"  GET  http://{host}:{port}/api/health - Health check")
    print(f"\nWaiting for moves from browser/external source...")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Jalankan server dengan default settings
    run_server()
