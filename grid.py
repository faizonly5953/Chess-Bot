import tkinter as tk
import pyautogui
import time
from PIL import Image, ImageDraw, ImageFont

# Fungsi untuk memilih area dengan klik dan mencetak posisi pixel
def select_area():
    # Memberikan waktu 2 detik untuk persiapan sebelum klik pertama
    print("Pilih pojok kiri atas dan pojok kanan bawah dari area yang ingin diseleksi.")
    time.sleep(5)
    
    # Klik pertama di pojok kiri atas
    print("Klik pada pojok kiri atas area seleksi.")
    x1, y1 = pyautogui.position()  # Menyimpan posisi mouse saat klik pertama
    print(f"Pojok kiri atas: ({x1}, {y1})")
    
    # Memberikan waktu 1 detik sebelum klik kedua
    time.sleep(5)

    # Klik kedua di pojok kanan bawah
    print("Klik pada pojok kanan bawah area seleksi.")
    x2, y2 = pyautogui.position()  # Menyimpan posisi mouse saat klik kedua
    print(f"Pojok kanan bawah: ({x2}, {y2})")

    # Menghitung lebar dan tinggi area seleksi
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    # Mencetak informasi area yang dipilih
    print(f"Area yang dipilih memiliki ukuran {width}x{height} pixels.")
    
    # Validasi jika area terlalu kecil (misalnya, lebar atau tinggi kurang dari 10px)
    if width < 10 or height < 10:
        print("Area terlalu kecil, pastikan untuk memilih area yang lebih besar.")
        return

    # Mengambil screenshot dari area yang dipilih
    screenshot = pyautogui.screenshot(region=(x1, y1, width, height))

    # Menggambar grid 8x8 pada screenshot
    draw_grid(screenshot, width, height, x1, y1)

# Fungsi untuk menggambar grid 8x8
def draw_grid(image, width, height, x_offset, y_offset):
    # Membuat objek ImageDraw untuk menggambar pada gambar
    draw = ImageDraw.Draw(image)
    
    # Ukuran tiap sel dalam grid
    grid_size_x = width // 8
    grid_size_y = height // 8
    
    # Warna untuk garis grid
    grid_color = (255, 0, 0)  # Merah
    
    # Menambahkan font untuk label (pilih font yang sesuai)
    font = ImageFont.load_default()
    
    # Menggambar grid 8x8 dan menambahkan label (koordinat angka)
    for i in range(1, 8):
        # Garis vertikal
        draw.line([(i * grid_size_x, 0), (i * grid_size_x, height)], fill=grid_color, width=2)
        # Garis horizontal
        draw.line([(0, i * grid_size_y), (width, i * grid_size_y)], fill=grid_color, width=2)
    
    # Menambahkan label untuk setiap grid dengan koordinat angka
    for row in range(8):
        for col in range(8):
            # Membuat label dengan format (baris, kolom)
            label = f"({row+1},{col+1})"  # Format (1,1), (1,2), ..., (8,8)
            x_pos = col * grid_size_x + grid_size_x // 2  # Menempatkan label di tengah sel
            y_pos = row * grid_size_y + grid_size_y // 2
            draw.text((x_pos, y_pos), label, fill="black", font=font)
    
    # Menyimpan hasil gambar dengan grid
    image.save("selected_area_grid_labeled.png")
    print("Screenshot dan grid 8x8 dengan label telah disimpan sebagai 'selected_area_grid_labeled.png'.")

# Fungsi untuk membuat GUI dengan tkinter
def create_gui():
    # Membuat window tkinter
    window = tk.Tk()
    window.title("Select Area GUI")
    window.geometry("300x150")
    
    # Menjadikan window selalu berada di atas
    window.attributes('-topmost', True)
    
    # Label untuk instruksi
    label = tk.Label(window, text="Tekan tombol untuk pilih area!", font=('Arial', 12))
    label.pack(pady=20)
    
    # Tombol untuk memilih area
    select_button = tk.Button(window, text="Select Area", command=select_area, font=('Arial', 12))
    select_button.pack(pady=10)

    # Jalankan GUI
    window.mainloop()

if __name__ == "__main__":
    # Jalankan GUI
    create_gui()