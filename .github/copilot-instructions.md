# Chess Bot - AI Agent Instructions

## Architecture Overview

This is a **modular chess automation bot** that combines Stockfish chess engine analysis with GUI-based calibration and automated mouse clicking. The system uses file-based communication (`fen.txt`, `best.txt`) between components and event-driven monitoring via Watchdog.

**Core Components:**
- `main.py` - GUI orchestrator with tabbed interface (Focus/Config/Output)
- `engine.py` - Stockfish UCI protocol wrapper for chess analysis
- `autoclicker.py` - File-watching auto-clicker with coordinate transformation
- `calibration.py` - Interactive grid calibration tool with persistent config

**Data Flow:** User enters FEN → Stockfish analyzes → Best move written to `best.txt` → Watchdog triggers → Autoclicker transforms UCI notation to screen coordinates → Executes clicks on chess board

## Critical Code Conventions

### Defensive Programming (POWER OF 10 Rules)
**All code follows JPL's Power of 10 safety-critical guidelines** (see `code.instructions.md`):

1. **Mandatory assertions** - Every function validates inputs/outputs with assertions
   ```python
   assert fen, "FEN tidak boleh kosong"
   assert 1 <= depth <= 30, "Depth harus antara 1-30"
   ```

2. **Loop bounds** - All loops have fixed upper bounds with MAX constants
   ```python
   MAX_RESPONSE_LINES = 1000
   for iteration in range(MAX_RESPONSE_LINES):  # Never unbounded while loops
   ```

3. **No dynamic allocation** - No runtime `malloc`/object creation in critical paths
4. **Function length** - Max 60 lines per function (printable on one page)
5. **No recursion** - All algorithms use iteration instead
6. **Minimal pointers** - Single-level only (N/A in Python but avoid nested refs)
7. **Limited preprocessor** - No token pasting/varargs (N/A in Python)

### State Management Pattern
- GUI state stored in Tkinter variables (`self.board_flip_var`, `self.elo_var`)
- Board state in `chess.Board()` object, synchronized with engine via FEN
- Persistent state in plain text files (`grid_config.txt` format: `x1\ny1\nx2\ny2\nelo_limit\nelo_value`)

### Coordinate System Handling
**Critical:** Board perspective affects coordinate transformation in `autoclicker.py`:
```python
if self.board_flipped:  # Black plays from bottom
    start_row, end_row = 9 - start_row, 9 - end_row
    start_col, end_col = 9 - start_col, 9 - end_col
```
Always validate with both Normal (White bottom) and Flipped orientations.

## Development Workflows

### Running the Application
```powershell
# Single entry point - no multiple scripts needed
python main.py
```

**First-time setup:**
1. Update `STOCKFISH_PATH` in `main.py` (line ~565) to local Stockfish executable
2. Run application → Configuration tab → "Calibrate New Grid"
3. Click chess board corners when prompted (5 sec delay between clicks)
4. Config auto-saves to `grid_config.txt` for reuse

### Stockfish Integration
Engine communication uses UCI protocol via subprocess pipes:
```python
self.send_command("position fen {fen}")
self.send_command("go depth 20")
# Wait for: bestmove e2e4 ponder e7e5
```

**Elo Limiting:** Use `UCI_LimitStrength` + `UCI_Elo` for human-like play (800-3190 range). Always call `ucinewgame` after changing settings to reset engine state.

### Testing Auto-Clicker Without Chess
Set breakpoints in `autoclicker.py:execute_move()` to inspect coordinate calculations. Use `instant_mode=True` to disable mouse animations during debugging.

## Project-Specific Patterns

### Error Handling Philosophy
Prefer explicit assertions over try-catch for invalid states:
```python
# GOOD - Fails fast with clear message
assert len(best_move) <= MAX_MOVE_LENGTH, "Move terlalu panjang"

# AVOID - Silent failure or generic errors
if len(best_move) > MAX_MOVE_LENGTH: return None
```

### File I/O Protocol
All inter-component communication uses atomic file writes:
```python
with open("fen.txt", "w") as f:
    f.write(fen + "\n")  # Always newline-terminated
```

Watchdog monitors `best.txt` modifications → triggers `process_move_file()` → avoids duplicate processing via `last_processed_move` cache.

### GUI Threading
**Never** call Tkinter methods from background threads. Use `threading` for file watching (Watchdog), but update GUI only from main thread callbacks.

### Module Boundaries
- `engine.py` knows nothing about GUI or clicking - only UCI protocol
- `autoclicker.py` knows only grid geometry and file watching - no chess logic
- `calibration.py` is standalone - can be imported independently
- `main.py` orchestrates all modules - only file with application-level logic

## Integration Points

### Stockfish Binary
Expected at `stockfish/stockfish-windows-x86-64-avx2.exe`. On non-Windows, update path to compiled binary for target platform. Optional: Set `SYZYGY_PATH` for endgame tablebases.

### External Dependencies (requirements.txt)
- `chess>=1.9.4` - Board representation and SAN/UCI notation parsing
- `pyautogui>=0.9.53` - Cross-platform mouse automation (FAILSAFE enabled)
- `pillow>=9.0.0` - Screenshot capture for grid visualization
- `watchdog>=2.1.0` - File system event monitoring

### Platform-Specific Code
`pyautogui.hotkey('alt', 'tab')` in `autoclicker.py` - may need macOS adjustment (`cmd+tab`).

## Common Modifications

**Adding new Stockfish options:**
```python
# In engine.py:_start_engine()
self.send_command("setoption name {OptionName} value {value}")
```

**Changing click delays:**
Modify constants in `autoclicker.py`: `pyautogui.PAUSE = 0.5` (global) or `duration` parameter in `perform_click()`.

**Supporting different board sizes:**
Update `GRID_SIZE = 8` in `calibration.py` - affects grid subdivision logic.

## Legacy Migration Notes
Deprecated files (`caturf.py`, `clickf.py`, `grid.py`) are old 3-script architecture. **Do not modify** - kept for reference only. All new development goes in modular structure.

Config file format is backward-compatible (lines 5-6 for Elo are optional).
