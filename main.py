import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import numpy as np

# Добавляем импорт pyperclip с обработкой ошибок
try:
    import pyperclip

    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False


class ImageToBitmapConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("ArduBMP / Image to Adafruit BMP converter")

        # Переменные для хранения пути и параметров
        self.image_path = tk.StringVar()
        self.threshold = tk.IntVar(value=128)
        self.output_text = tk.Text(root, height=15, width=70)

        # Создание элементов интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Кнопка загрузки изображения
        tk.Button(self.root, text="Choose image", command=self.load_image).grid(row=0, column=0, padx=5, pady=5)

        # Поле пути файла
        tk.Entry(self.root, textvariable=self.image_path, width=50).grid(row=0, column=1, padx=5, pady=5)

        # Порог бинаризации
        tk.Label(self.root, text="Binarization threshold:").grid(row=1, column=0, padx=5, pady=5)
        tk.Scale(self.root, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.threshold).grid(row=1, column=1,
                                                                                                 padx=5, pady=5)

        # Кнопка конвертации
        tk.Button(self.root, text="Convert", command=self.convert_image).grid(row=2, column=0, columnspan=2,
                                                                                      padx=5, pady=5)

        # Текстовое поле для вывода
        self.output_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # Фрейм для кнопок
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # Кнопка сохранения
        tk.Button(button_frame, text="Save", command=self.save_to_file).pack(side=tk.LEFT, padx=5)

        # Кнопка копирования в буфер обмена
        self.copy_button = tk.Button(button_frame, text="Copy", command=self.copy_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        # Показываем статус доступности pyperclip
        if not PYPERCLIP_AVAILABLE:
            self.copy_button.config(state=tk.DISABLED)
            tk.Label(button_frame, text="pyperclip not installed / data could not copy", fg="red").pack(side=tk.LEFT, padx=5)

    def load_image(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if filename:
            self.image_path.set(filename)

    def convert_image(self):
        if not self.image_path.get():
            messagebox.showerror("Error", "Choose image to convert.")
            return

        try:
            # Открываем и обрабатываем изображение
            img = Image.open(self.image_path.get()).convert('L').resize((128, 64)) if (
                        Image.open(self.image_path.get()).convert('L').width > 128 and Image.open(
                    self.image_path.get()).convert('L').height > 64) else Image.open(self.image_path.get()).convert('L')
            img_array = np.array(img)

            # Бинаризация
            binary_array = (img_array > self.threshold.get()).astype(np.uint8)

            # Генерация bitmap данных
            height, width = binary_array.shape
            bitmap_data = []

            for y in range(height):
                for x in range(0, width, 8):
                    byte = 0
                    for bit in range(8):
                        if x + bit < width:
                            byte |= (binary_array[y, x + bit] << (7 - bit))
                    bitmap_data.append(f"0x{byte:02X}")

            # Форматирование вывода
            output = f"// Size: {width}x{height}\n"
            output += f"static const unsigned char PROGMEM bitmap[{len(bitmap_data)}] = {{\n"
            for i in range(0, len(bitmap_data), 16):
                output += "  " + ", ".join(bitmap_data[i:i + 16]) + ",\n"
            output += "};"

            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, output)

            # Автоматическое копирование после конвертации
            self.copy_to_clipboard()

        except Exception as e:
            messagebox.showerror("Error", f"Image could not be converted to bitmap.\n{str(e)}")

    def save_to_file(self):
        data = self.output_text.get(1.0, tk.END).strip()
        if not data or data.startswith("Error"):
            messagebox.showerror("Error", "No data/bitmap to copy.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".h",
            filetypes=[("Header files", "*.h"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(data)
            messagebox.showinfo("OK", "File saved.")

    def copy_to_clipboard(self):
        if not PYPERCLIP_AVAILABLE:
            messagebox.showerror("Unknown Error", "Sorry, bitmap will not be copied to clipboard.")
            return

        data = self.output_text.get(1.0, tk.END).strip()
        if not data or data.startswith("Error"):
            messagebox.showerror("Error", "No data/bitmap to copy.")
            return

        try:
            pyperclip.copy(data)
            messagebox.showinfo("OK", "Data copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Sorry, bitmap will not be copied to clipboard.\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageToBitmapConverter(root)
    root.mainloop()
