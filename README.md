# Chess Bot README

### Educational Purpose Only !!

## Deskripsi Proyek
Proyek ini adalah sebuah aplikasi catur otomatis berbasis GUI menggunakan Tkinter yang mengintegrasikan engine Stockfish dan PyAutoGUI. Chess Bot ini memungkinkan pengguna untuk bermain catur dengan bantuan AI, memulai permainan dari posisi FEN yang ditentukan, dan menerima langkah terbaik dari Stockfish untuk kedua pemain secara otomatis.

### Struktur Proyek
Proyek ini terdiri dari tiga script utama:
1. **`catur.py`**: Skrip utama untuk menjalankan dan mengontrol interaksi dengan engine Stockfish, serta mengelola alur permainan catur di GUI.
2. **`click.py`**: Skrip yang digunakan untuk berinteraksi dengan layar menggunakan PyAutoGUI untuk mensimulasikan klik dan pergerakan otomatis berdasarkan koordinat papan catur.
3. **`grid.py`**: Skrip ini menyediakan pengaturan untuk grid papan catur dan konversi notasi catur ke koordinat yang digunakan oleh PyAutoGUI.

## Persyaratan
Sebelum menjalankan proyek ini, pastikan Anda memiliki persyaratan berikut:
- **Python 3.x** (direkomendasikan versi 3.6 ke atas)
- **Stockfish**: Engine catur Stockfish diunduh dan dikonfigurasi.
- **PyAutoGUI**: Untuk kontrol otomatis klik pada layar.
- **Tkinter**: Digunakan untuk membuat GUI aplikasi.
- **Chess**: Modul Python untuk menangani aturan catur.

### Instalasi
1. Install dependensi yang diperlukan:
   ```bash
   pip install pyautogui chess
   ```

2. **Stockfish**:
   - Unduh Stockfish dari [situs resmi Stockfish](https://stockfishchess.org/download/).
   - Ekstrak dan simpan file eksekutabel Stockfish pada lokasi yang sesuai di sistem Anda.

### Menjalankan Proyek
1. Jalankan `catur.py` untuk memulai aplikasi GUI catur.
2. Pilih posisi awal FEN (format posisi catur standar) dan klik "Mulai dari FEN".
3. Skript akan automatisasi analisis siapakah yang jalan, dan menganalisis best move untuk kamu
4. Skrip akan membuat file `fen.txt` dan `best.txt`
5. Happy Playing!

### Penjelasan Skrip

#### 1. **`catur.py`**
   - **Tujuan**: Skrip ini mengelola interaksi dengan engine Stockfish, membaca input dari pengguna, dan memperbarui status papan catur pada GUI.
   - **Fungsi Utama**:
     - **`StockfishProcess`**: Kelas untuk mengelola proses Stockfish, mengirim perintah, dan menerima hasil analisis untuk mendapatkan langkah terbaik.
     - **`start_from_fen()`**: Fungsi untuk memulai permainan dari posisi FEN yang diberikan oleh pengguna.
     - **`add_white_move()`**: Fungsi untuk menangani langkah pemain putih dan menganalisis langkah terbaik dari pemain hitam.
     - **`update_fen_display()`**: Memperbarui tampilan FEN pada GUI.
   - **GUI**: Menggunakan Tkinter untuk menangani input langkah, menampilkan FEN saat ini, dan output analisis.

#### 2. **`click.py`**
   - **Tujuan**: Skrip ini menggunakan PyAutoGUI untuk mengontrol klik pada papan catur berdasarkan koordinat.
   - **Fungsi Utama**:
     - **`get_turn_from_fen()`**: Fungsi untuk membaca file `fen.txt` dan menentukan giliran pemain (Putih atau Hitam) berdasarkan FEN yang ada.
     - **Konfigurasi Grid**: Menyusun koordinat dan ukuran grid papan catur untuk menghubungkan notasi catur dengan posisi di layar.
   
#### 3. **`grid.py`**
   - **Tujuan**: Menyediakan pengaturan koordinat dan konversi dari notasi catur (seperti 'e2' atau 'g1') ke koordinat layar yang digunakan oleh PyAutoGUI untuk klik otomatis.
   - **Fungsi Utama**:
     - **Mapping Notasi**: Memetakan kolom papan catur (a-h) ke angka (1-8) dan sebaliknya.
     - **Menghitung ukuran sel**: Menghitung ukuran setiap sel pada papan berdasarkan ukuran layar yang ditentukan.

### Fitur
- **GUI Interaktif**: Pengguna dapat memasukkan posisi FEN dan mendapatkan langkah terbaik dari Stockfish.
- **Pengenalan Giliran**: Secara otomatis mendeteksi giliran putih atau hitam berdasarkan FEN.
- **Langkah Otomatis**: Setelah langkah pemain putih dimasukkan, AI akan memberikan langkah terbaik.
- **Simpan dan Baca FEN**: FEN dapat disimpan dan dibaca dari file untuk melanjutkan permainan.
  
### Catatan
- Pastikan untuk menyesuaikan path Stockfish pada variabel `stockfish_path` di `catur.py`.
- `fen.txt` digunakan untuk menyimpan FEN terakhir yang dimasukkan, dan `best.txt` untuk menyimpan langkah terbaik yang dipilih oleh Stockfish.

### Screenshot
**`catur.py`**
![image](https://github.com/user-attachments/assets/5a03d4b9-e1f9-4d54-b1a1-e3c1e23533af)
###
**`click.py`**
![image](https://github.com/user-attachments/assets/0ee2311e-eec2-4f44-9a75-27b9036e9a63)
###
**`grid.py`**
![selected_area_grid_labeled](https://github.com/user-attachments/assets/bb7646d6-774f-4c38-803e-5dcb46f4a48d)



### Troubleshooting
- **Stockfish Tidak Menanggapi**: Pastikan bahwa path ke Stockfish benar dan Stockfish dijalankan tanpa kesalahan.
- **Koordinat Klik Tidak Akurat**: Jika Anda mengalami masalah dengan koordinat klik yang tidak sesuai, pastikan layar Anda memiliki resolusi yang sesuai dan sesuaikan nilai pada `GRID_START_X`, `GRID_START_Y`, `GRID_END_X`, dan `GRID_END_Y` di `click.py`.

### Kontribusi
Jika Anda ingin berkontribusi pada proyek ini:
1. Fork repositori ini.
2. Buat perubahan yang Anda inginkan.
3. Kirim pull request dengan deskripsi perubahan yang dilakukan.
