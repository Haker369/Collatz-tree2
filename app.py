import sys
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================
# ТОЧНЫЙ И НАДЕЖНЫЙ КЭШ ЧИСЕЛ КОЛЛАТЦА
# ==========================================
np.random.seed(42)
STATIC_START_NUMBERS = np.random.randint(1, 1000000, size=10000)
COLLATZ_CACHE = []

for n in STATIC_START_NUMBERS:
    seq = [n]
    steps_count = 0
    while n != 1 and steps_count < 5000:  # ИСПРАВЛЕНО: Лимит шагов предотвращает переполнение RAM (MemoryError)
        if n % 2 == 0: n //= 2
        else: n = 3 * n + 1
        seq.append(n)
        steps_count += 1
    COLLATZ_CACHE.append(np.array(seq[::-1], dtype=float))

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class HybridControl(ctk.CTkFrame):
    def __init__(self, master, label_text, val, min_v, max_v, callback):
        super().__init__(master, fg_color="transparent")
        self.min_v = min_v
        self.max_v = max_v
        self.callback = callback
        self.is_blocking = False

        # Круглый маркер-индикатор
        self.indicator = tk.Canvas(self, width=12, height=12, bg="#12162d", highlightthickness=0)
        self.indicator_circle = self.indicator.create_oval(2, 2, 10, 10, fill="#ffc107")
        self.indicator.pack(side=tk.LEFT, padx=(0, 6))

        lbl = ctk.CTkLabel(self, text=label_text, font=("Arial", 11, "bold"), text_color="#8189a2", width=130, anchor="w")
        lbl.pack(side=tk.LEFT)

        self.slider = ctk.CTkSlider(self, from_=min_v, to=max_v, number_of_steps=int(max_v - min_v), width=160, command=self.on_slider_move)
        self.slider.set(val)
        self.slider.pack(side=tk.LEFT, padx=5)

        self.btn_minus = ctk.CTkButton(self, text="◀", width=24, height=24, corner_radius=12, fg_color="#2b304c", hover_color="#3b4268", command=lambda: self.adjust(-1))
        self.btn_minus.pack(side=tk.LEFT, padx=2)

        self.num_field = ctk.CTkLabel(self, text=str(int(val)), font=("Arial", 11), text_color="white", fg_color="#1a1d33", corner_radius=4, width=40, height=24)
        self.num_field.pack(side=tk.LEFT, padx=2)

        self.btn_plus = ctk.CTkButton(self, text="▶", width=24, height=24, corner_radius=12, fg_color="#2b304c", hover_color="#3b4268", command=lambda: self.adjust(1))
        self.btn_plus.pack(side=tk.LEFT, padx=2)

        self.update_indicator(val)

    def on_slider_move(self, val):
        if self.is_blocking: return
        self.num_field.configure(text=str(int(val)))
        self.update_indicator(val)
        self.callback()

    def adjust(self, direction):
        new_val = self.slider.get() + direction
        if self.min_v <= new_val <= self.max_v:
            self.slider.set(new_val)
            self.on_slider_move(new_val)

    def set_value_silent(self, val):
        self.is_blocking = True
        self.slider.set(val)
        self.num_field.configure(text=str(int(val)))
        self.update_indicator(val)
        self.is_blocking = False

    def get_value(self):
        return self.slider.get()

    def update_indicator(self, val):
        if abs(val - self.min_v) < 0.1: color = "#dc3545" # Красный
        elif abs(val - self.max_v) < 0.1: color = "#28a745" # Зеленый
        else: color = "#ffc107" # Желтый
        self.indicator.itemconfigure(self.indicator_circle, fill=color)


class FractalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Генератор дерева Коллатца")
        self.geometry("1100x700")
        self.configure(fg_color="#0b0d19")

        # Главный контейнер разметки
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.left_panel = ctk.CTkFrame(self.main_container, fg_color="transparent", width=460)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        self.is_updating_preset = False
        self.controls = {}

        # 1. Панель цветов
        colors_box = ctk.CTkFrame(self.left_panel, fg_color="#12162d", border_color="#3c445c", border_width=1, corner_radius=6)
        colors_box.pack(fill=tk.X, pady=(0, 10), ipady=8, ipadx=8)
        
        ctk.CTkLabel(colors_box, text="Цветовая палитра", font=("Arial", 12, "bold"), text_color="white").pack(anchor="w", padx=10, pady=4)
        
        p_frame = ctk.CTkFrame(colors_box, fg_color="transparent")
        p_frame.pack(fill=tk.X, padx=10, pady=4)
        ctk.CTkLabel(p_frame, text="Готовый пресет:", font=("Arial", 11, "bold"), text_color="#8189a2").pack(side=tk.LEFT)
        self.preset_combo = ctk.CTkComboBox(p_frame, values=['Стандарт', 'Радуга', 'Киберпанк', 'Огонь'], width=180, fg_color="#1b203e", border_color="#3c445c", command=self.on_preset_changed)
        self.preset_combo.pack(side=tk.RIGHT)

        def add_ctrl(master, key, label, val, mn, mx):
            ctrl = HybridControl(master, label, val, mn, mx, self.trigger_update)
            ctrl.pack(fill=tk.X, padx=10, pady=2)
            self.controls[key] = ctrl
        
        add_ctrl(colors_box, 's', 'Сдвиг спектра', 249, 0, 300)
        add_ctrl(colors_box, 'r', 'Вращение цвета', 76, 0, 500)
        add_ctrl(colors_box, 'h', 'Насыщенность', 181, 0, 300)
        add_ctrl(colors_box, 'g', 'Яркость / Гамма', 130, 10, 200)
        add_ctrl(colors_box, 'o', 'Прозрачность ветвей', 50, 5, 100)

        self.btn_rand_col = ctk.CTkButton(colors_box, text="🎨 Мутировать цвет", fg_color="#17a2b8", hover_color="#138496", font=("Arial", 11, "bold"), height=28, command=self.mutate_colors)
        self.btn_rand_col.pack(fill=tk.X, padx=10, pady=(6, 2))

        # 2. Панель геометрии
        geo_box = ctk.CTkFrame(self.left_panel, fg_color="#12162d", border_color="#3c445c", border_width=1, corner_radius=6)
        geo_box.pack(fill=tk.X, pady=(0, 10), ipady=8, ipadx=8)
        
        ctk.CTkLabel(geo_box, text="Геометрия дерева", font=("Arial", 12, "bold"), text_color="white").pack(anchor="w", padx=10, pady=4)
        add_ctrl(geo_box, 'e', 'Масштаб длины', 130, 10, 250)
        add_ctrl(geo_box, 'a', 'Угол ветвления', 19, 1, 100)
        add_ctrl(geo_box, 'f', 'Смещение кроны', 70, 0, 200)
        add_ctrl(geo_box, 'lw', 'Толщина линий', 40, 2, 300)

        rays_frame = ctk.CTkFrame(geo_box, fg_color="transparent")
        rays_frame.pack(fill=tk.X, padx=10, pady=4)
        ctk.CTkLabel(rays_frame, text="Количество лучей:", font=("Arial", 11, "bold"), text_color="#8189a2").pack(side=tk.LEFT, padx=(18, 0))
        self.w_n = ctk.CTkEntry(rays_frame, width=80, height=24, fg_color="#1b203e", border_color="#3c445c")
        self.w_n.insert(0, "1008")
        self.w_n.pack(side=tk.LEFT, padx=10)
        self.w_n.bind("<KeyRelease>", lambda e: self.trigger_update())

        self.btn_rand_geo = ctk.CTkButton(geo_box, text="🌀 Мутировать форму", fg_color="#ffc107", hover_color="#e0a800", text_color="black", font=("Arial", 11, "bold"), height=28, command=self.mutate_geometry)
        self.btn_rand_geo.pack(fill=tk.X, padx=10, pady=(6, 2))

        # 3. Экспорт
        export_box = ctk.CTkFrame(self.left_panel, fg_color="#12162d", border_color="#3c445c", border_width=1, corner_radius=6)
        export_box.pack(fill=tk.X, pady=(0, 10), ipady=8, ipadx=8)
        
        ctk.CTkLabel(export_box, text="Экспорт", font=("Arial", 12, "bold"), text_color="white").pack(anchor="w", padx=10, pady=4)
        
        res_frame = ctk.CTkFrame(export_box, fg_color="transparent")
        res_frame.pack(fill=tk.X, padx=10, pady=4)
        ctk.CTkLabel(res_frame, text="Разрешение кадра:", font=("Arial", 11, "bold"), text_color="#8189a2").pack(side=tk.LEFT)
        self.res_combo = ctk.CTkComboBox(res_frame, values=['FullHD (1080x1920)', '2K (1440x2560)', '4K (2160x3840)'], width=180, fg_color="#1b203e", border_color="#3c445c", command=lambda v: self.trigger_update())
        self.res_combo.pack(side=Qt.RIGHT)

        fmt_frame = ctk.CTkFrame(export_box, fg_color="transparent")
        fmt_frame.pack(fill=tk.X, padx=10, pady=4)
        ctk.CTkLabel(fmt_frame, text="Формат файла:", font=("Arial", 11, "bold"), text_color="#8189a2").pack(side=tk.LEFT)
        self.format_combo = ctk.CTkComboBox(fmt_frame, values=['PNG', 'JPEG', 'PDF'], width=180, fg_color="#1b203e", border_color="#3c445c")
        self.format_combo.pack(side=tk.RIGHT)

        actions_frame = ctk.CTkFrame(export_box, fg_color="transparent")
        actions_frame.pack(fill=tk.X, padx=10, pady=(10, 2))
        self.btn_download = ctk.CTkButton(actions_frame, text="Скачать файл", fg_color="#28a745", hover_color="#218838", font=("Arial", 11, "bold"), command=self.save_image_file)
        self.btn_download.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.btn_reset = ctk.CTkButton(actions_frame, text="Сброс", fg_color="#dc3545", hover_color="#c82333", font=("Arial", 11, "bold"), command=self.reset_to_defaults)
        self.btn_reset.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # Статистика
        self.stats_label = ctk.CTkLabel(self.left_panel, text="Линий на экране: 0", font=("Arial", 11, "bold"), text_color="#28a745", fg_color="#12162d", border_color="#3c445c", border_width=1, corner_radius=4, height=30)
        self.stats_label.pack(fill=tk.X)

        # График Matplotlib справа
        self.right_panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(5.4, 9.6), dpi=100, facecolor='none')
        self.ax.set_facecolor('none')
        self.lc = LineCollection([], linewidths=0.5)
        self.ax.add_collection(lc)
        self.ax.axis('off')
        self.fig.subplots_adjust(top=1, bottom=0, right=1, left=0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.get_tk_widget().configure(bg="#0b0d19", highlightthickness=0)

        self.trigger_update()

    def trigger_update(self):
        if self.is_updating_preset: return
        
        s = self.controls['s'].get_value() / 100.0
        r = self.controls['r'].get_value() / 100.0
        h = self.controls['h'].get_value() / 100.0
        g = self.controls['g'].get_value() / 100.0
        o = self.controls['o'].get_value() / 100.0
        e = self.controls['e'].get_value() / 100.0
        a = self.controls['a'].get_value() / 100.0
        f = self.controls['f'].get_value() / 100.0
        lw = self.controls['lw'].get_value() / 100.0
        
        try:
            n = int(self.w_n.get())
        except ValueError:
            n = 12
        n = max(12, min(10000, n))
        
        res_mode = self.res_combo.get()
        if res_mode == 'FullHD (1080x1920)': self.fig.set_size_inches(5.4, 9.6)
        elif res_mode == '2K (1440x2560)': self.fig.set_size_inches(7.2, 12.8)
        elif res_mode == '4K (2160x3840)': self.fig.set_size_inches(10.8, 19.2)

        all_segments, all_colors = [], []
        xmin, xmax, ymin, ymax = float('inf'), float('-inf'), float('inf'), float('-inf')
        total_lines = 0

        for idx in range(n):
            seq = COLLATZ_CACHE[idx]
            steps = seq / (1.0 + np.power(seq, e))
            angles = a * (f - 2.0 * (seq % 2))
            cum_angles = np.cumsum(angles)
            
            dx, dy = steps * np.cos(cum_angles), steps * np.sin(cum_angles)
            x = np.concatenate(([0.0], np.cumsum(dx)))
            y = np.concatenate(([0.0], np.cumsum(dy)))
            path = np.column_stack((x, y))
            
            num_points = len(path)
            if num_points < 2: continue
                
            xmin, xmax = min(xmin, np.min(path[:, 0])), max(xmax, np.max(path[:, 0]))
            ymin, ymax = min(ymin, np.min(path[:, 1])), max(ymax, np.max(path[:, 1]))

            seg = np.zeros((num_points - 1, 2, 2))
            seg[:, 0, :] = path[:-1]
            seg[:, 1, :] = path[1:]
            all_segments.append(seg)
            total_lines += (num_points - 1)
            
            lengths = np.linspace(0.0, 1.0, num_points - 1)
            psi = 2.0 * np.pi * (s / 3.0 + r * lengths)
            amp = h * np.power(lengths, g) * (1.0 - np.power(lengths, g)) / 2.0
            matrix = np.array([[-0.14861, 1.78277], [-0.29227, -0.90649], [1.97294, 0.0]])
            vec = np.vstack((np.cos(psi), np.sin(psi)))
            rgb = np.power(lengths, g)[:, np.newaxis] + amp[:, np.newaxis] * (matrix @ vec).T
            rgb = np.clip(rgb, 0.0, 1.0)
            
            rgba = np.zeros((rgb.shape[0], 4))
            rgba[:, :3] = rgb
            rgba[:, 3] = o
            all_colors.append(rgba)

        if all_segments:
            self.lc.set_segments(np.concatenate(all_segments, axis=0))
            self.lc.set_colors(np.concatenate(all_colors, axis=0))
            self.lc.set_linewidths(lw)
            
            padding_x = (xmax - xmin) * 0.05 if xmax > xmin else 1.0
            padding_y = (ymax - ymin) * 0.05 if ymax > ymin else 1.0
            self.ax.set_xlim(xmin - padding_x, xmax + padding_x)
            self.ax.set_ylim(ymin - padding_y, ymax + padding_y)
            self.ax.set_aspect('equal')
            
            self.stats_label.configure(text=f"Линий на экране: {total_lines:,}")
            self.canvas.draw()

    def on_preset_changed(self, preset):
        self.is_updating_preset = True
        if preset == 'Радуга':          p = (0, 300, 150, 100)
        elif preset == 'Киберпанк':     p = (225, 290, 230, 110)
        elif preset == 'Огонь':         p = (10, 45, 190, 130)
        elif preset == 'Стандарт':      p = (249, 76, 181, 130)
        
        self.controls['s'].set_value_silent(p[0])
        self.controls['r'].set_value_silent(p[1])
        self.controls['h'].set_value_silent(p[2])
        self.controls['g'].set_value_silent(p[3])
        self.is_updating_preset = False
        self.trigger_update()

    def mutate_geometry(self):
        self.controls['e'].set_value_silent(int(np.random.uniform(90, 170)))
        self.controls['a'].set_value_silent(int(np.random.uniform(12, 28)))
        self.controls['f'].set_value_silent(int(np.random.uniform(30, 130)))
        self.trigger_update()

    def mutate_colors(self):
        self.is_updating_preset = True
        self.controls['s'].set_value_silent(int(np.random.uniform(0, 300)))
        self.controls['r'].set_value_silent(int(np.random.uniform(0, 400)))
        self.controls['h'].set_value_silent(int(np.random.uniform(50, 250)))
        self.controls['g'].set_value_silent(int(np.random.uniform(50, 170)))
        self.is_updating_preset = False
        self.trigger_update()

    def reset_to_defaults(self):
        self.is_updating_preset = True
        self.controls['s'].set_value_silent(249)
        self.controls['r'].set_value_silent(76)
        self.controls['h'].set_value_silent(181)
        self.controls['g'].set_value_silent(130)
        self.controls['o'].set_value_silent(50)
        self.controls['e'].set_value_silent(130)
        self.controls['a'].set_value_silent(19)
        self.controls['f'].set_value_silent(70)
        self.controls['lw'].set_value_silent(40)
        self.w_n.delete(0, tk.END)
        self.w_n.insert(0, "1008")
        self.preset_combo.set('Стандарт')
        self.res_combo.set('FullHD (1080x1920)')
        self.format_combo.set('PNG')
        self.is_updating_preset = False
        self.trigger_update()

    def save_image_file(self):
        fmt = self.format_combo.get().lower()
        file_path = filedialog.asksaveasfilename(defaultextension=f".{fmt}", filetypes=[(f"{fmt.upper()} Files", f"*.{fmt}")])
        if file_path:
            self.lc.set_antialiaseds(True)
            current_lw = self.controls['lw'].get_value() / 100.0
            if fmt == 'pdf':
                self.lc.set_linewidths(current_lw * 0.8)
                self.fig.savefig(file_path, facecolor='none', transparent=True, pad_inches=0)
            else:
                self.lc.set_linewidths(current_lw * 1.5)
                bg_color = 'none' if fmt != 'jpeg' else '#000000'
                self.fig.savefig(file_path, dpi=200, facecolor=bg_color, transparent=(fmt != 'jpeg'), pad_inches=0)
            self.lc.set_linewidths(current_lw)
            self.trigger_update()
            messagebox.showinfo("Экспорт", "Обои успешно сохранены!")

if __name__ == '__main__':
    app = FractalApp()
    app.mainloop()
