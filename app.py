import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QComboBox, QSlider, QPushButton, 
                             QLabel, QLineEdit, QFileDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIntValidator

# ==========================================
# ТОЧНЫЙ И НАДЕЖНЫЙ КЭШ ЧИСЕЛ КОЛЛАТЦА
# ==========================================
np.random.seed(42)
STATIC_START_NUMBERS = np.random.randint(1, 1000000, size=10000)
COLLATZ_CACHE = []

for n in STATIC_START_NUMBERS:
    seq = [n]
    while n != 1:
        if n % 2 == 0: n //= 2
        else: n = 3 * n + 1
        seq.append(n)
    COLLATZ_CACHE.append(np.array(seq[::-1], dtype=float))

class HybridControl(QWidget):
    def __init__(self, label_text, val, min_v, max_v, callback):
        super().__init__()
        self.min_v = min_v
        self.max_v = max_v
        self.callback = callback
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        
        self.indicator = QLabel()
        self.indicator.setFixedSize(10, 10)
        
        lbl = QLabel(label_text)
        lbl.setFixedWidth(120)
        lbl.setStyleSheet("color: #8189a2; font-weight: bold; font-size: 11px;")
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(min_v), int(max_v))
        self.slider.setValue(int(val))
        self.slider.setFixedWidth(160)
        
        self.btn_minus = QPushButton("◀")
        self.btn_plus = QPushButton("▶")
        btn_style = "QPushButton { border-radius: 11px; min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px; background-color: #2b304c; color: white; } QPushButton:pressed { background-color: #3b4268; }"
        self.btn_minus.setStyleSheet(btn_style)
        self.btn_plus.setStyleSheet(btn_style)
        
        self.num_field = QLabel(str(int(val)))
        self.num_field.setFixedWidth(35)
        self.num_field.setAlignment(Qt.AlignCenter)
        self.num_field.setStyleSheet("color: white; background-color: #1a1d33; border-radius: 4px; padding: 2px;")
        
        layout.addWidget(self.indicator)
        layout.addWidget(lbl)
        layout.addWidget(self.slider)
        layout.addWidget(self.btn_minus)
        layout.addWidget(self.num_field)
        layout.addWidget(self.btn_plus)
        self.setLayout(layout)
        
        self.slider.valueChanged.connect(self.on_slider_change)
        self.btn_minus.clicked.connect(lambda: self.adjust(-1))
        self.btn_plus.clicked.connect(lambda: self.adjust(1))
        self.update_indicator(val)

    @property
    def value(self):
        return self.slider.value()

    @value.setter
    def value(self, val):
        self.slider.setValue(int(val))

    def on_slider_change(self, val):
        self.num_field.setText(str(val))
        self.update_indicator(val)
        self.callback()

    def adjust(self, direction):
        new_val = self.slider.value() + direction
        if self.min_v <= new_val <= self.max_v:
            self.slider.setValue(new_val)

    def update_indicator(self, val):
        if abs(val - self.min_v) < 0.1:
            color = "#dc3545" # Красный - Мин
        elif abs(val - self.max_v) < 0.1:
            color = "#28a745" # Зеленый - Макс
        else:
            color = "#ffc107" # Желтый - Середина
        self.indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")


class FractalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор дерева Коллатца")
        self.setStyleSheet("QMainWindow { background-color: #0b0d19; }")
        
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Левая панель управления
        control_panel = QVBoxLayout()
        control_panel.setSpacing(10)
        
        # Блок Цветов
        colors_box = QWidget()
        colors_box.setStyleSheet("background-color: #12162d; border: 1px solid #3c445c; border-radius: 6px; padding: 8px;")
        colors_layout = QVBoxLayout(colors_box)
        
        title_colors = QLabel("Цветовая палитра")
        title_colors.setStyleSheet("color: white; font-weight: bold; border-bottom: 1px solid #3c445c; padding-bottom: 3px;")
        colors_layout.addWidget(title_colors)
        
        preset_layout = QHBoxLayout()
        preset_lbl = QLabel("Готовый пресет:")
        preset_lbl.setStyleSheet("color: #8189a2; font-size: 11px; font-weight: bold;")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['Стандарт', 'Радуга', 'Киберпанк', 'Огонь'])
        self.preset_combo.setStyleSheet("background-color: #1b203e; color: white; border: 1px solid #3c445c;")
        preset_layout.addWidget(preset_lbl)
        preset_layout.addWidget(self.preset_combo)
        colors_layout.addLayout(preset_layout)
        
        self.controls = {}
        w = lambda lbl, val, mn, mx: HybridControl(lbl, val, mn, mx, self.trigger_update)
        
        colors_layout.addWidget(self.controls['s'] := w('Сдвиг спектра', 249, 0, 300))
        colors_layout.addWidget(self.controls['r'] := w('Вращение цвета', 76, 0, 500))
        colors_layout.addWidget(self.controls['h'] := w('Насыщенность', 181, 0, 300))
        colors_layout.addWidget(self.controls['g'] := w('Яркость / Гамма', 130, 10, 200))
        colors_layout.addWidget(self.controls['o'] := w('Прозрачность ветвей', 50, 5, 100))
        
        self.btn_rand_col = QPushButton("🎨 Мутировать цвет")
        self.btn_rand_col.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold; border-radius: 4px; padding: 4px;")
        colors_layout.addWidget(self.btn_rand_col)
        control_panel.addWidget(colors_box)
        
        # Блок Геометрии
        geo_box = QWidget()
        geo_box.setStyleSheet("background-color: #12162d; border: 1px solid #3c445c; border-radius: 6px; padding: 8px;")
        geo_layout = QVBoxLayout(geo_box)
        
        title_geo = QLabel("Геометрия дерева")
        title_geo.setStyleSheet("color: white; font-weight: bold; border-bottom: 1px solid #3c445c; padding-bottom: 3px;")
        geo_layout.addWidget(title_geo)
        
        geo_layout.addWidget(self.controls['e'] := w('Масштаб длины', 130, 10, 250))
        geo_layout.addWidget(self.controls['a'] := w('Угол ветвления', 19, 1, 100))
        geo_layout.addWidget(self.controls['f'] := w('Смещение кроны', 70, 0, 200))
        geo_layout.addWidget(self.controls['lw'] := w('Толщина линий', 40, 2, 300))
        
        rays_layout = QHBoxLayout()
        rays_lbl = QLabel("Количество лучей")
        rays_lbl.setStyleSheet("color: #8189a2; font-size: 11px; font-weight: bold; margin-left: 18px;")
        self.w_n = QLineEdit("1008")
        self.w_n.setValidator(QIntValidator(12, 10000))
        self.w_n.setFixedWidth(80)
        self.w_n.setStyleSheet("background-color: #1b203e; color: white; border: 1px solid #3c445c; border-radius: 4px; padding: 2px;")
        rays_layout.addWidget(rays_lbl)
        rays_layout.addWidget(self.w_n)
        geo_layout.addLayout(rays_layout)
        
        self.btn_rand_geo = QPushButton("🌀 Мутировать форму")
        self.btn_rand_geo.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold; border-radius: 4px; padding: 4px;")
        geo_layout.addWidget(self.btn_rand_geo)
        control_panel.addWidget(geo_box)
        
        # Блок Экспорта
        export_box = QWidget()
        export_box.setStyleSheet("background-color: #12162d; border: 1px solid #3c445c; border-radius: 6px; padding: 8px;")
        export_layout = QVBoxLayout(export_box)
        
        title_export = QLabel("Экспорт")
        title_export.setStyleSheet("color: white; font-weight: bold; border-bottom: 1px solid #3c445c; padding-bottom: 3px;")
        export_layout.addWidget(title_export)
        
        res_layout = QHBoxLayout()
        res_lbl = QLabel("Разрешение кадра:")
        res_lbl.setStyleSheet("color: #8189a2; font-size: 11px; font-weight: bold;")
        self.res_combo = QComboBox()
        self.res_combo.addItems(['FullHD (1080x1920)', '2K (1440x2560)', '4K (2160x3840)'])
        self.res_combo.setStyleSheet("background-color: #1b203e; color: white; border: 1px solid #3c445c;")
        res_layout.addWidget(res_lbl)
        res_layout.addWidget(self.res_combo)
        export_layout.addLayout(res_layout)
        
        fmt_layout = QHBoxLayout()
        fmt_lbl = QLabel("Формат:")
        fmt_lbl.setStyleSheet("color: #8189a2; font-size: 11px; font-weight: bold;")
        self.format_combo = QComboBox()
        self.format_combo.addItems(['PNG', 'JPEG', 'PDF'])
        self.format_combo.setStyleSheet("background-color: #1b203e; color: white; border: 1px solid #3c445c;")
        fmt_layout.addWidget(fmt_lbl)
        fmt_layout.addWidget(self.format_combo)
        export_layout.addLayout(fmt_layout)
        
        btn_action_layout = QHBoxLayout()
        self.btn_download = QPushButton("Скачать файл")
        self.btn_download.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px; border-radius: 4px;")
        self.btn_reset = QPushButton("Сброс")
        self.btn_reset.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_action_layout.addWidget(self.btn_download)
        btn_action_layout.addWidget(self.btn_reset)
        export_layout.addLayout(btn_action_layout)
        control_panel.addWidget(export_box)
        
        self.stats_label = QLabel("Линий на экране: 0")
        self.stats_label.setStyleSheet("color: #28a745; background-color: #12162d; border: 1px solid #3c445c; border-radius: 4px; padding: 6px; font-weight: bold; qproperty-alignment: AlignCenter;")
        control_panel.addWidget(self.stats_label)
        
        # Правая часть холста Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(5.4, 9.6), dpi=100, facecolor='none')
        self.ax.set_facecolor('none')
        self.lc = LineCollection([], linewidths=0.5)
        self.ax.add_collection(self.lc)
        self.ax.axis('off')
        self.fig.subplots_adjust(top=1, bottom=0, right=1, left=0)
        
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        main_layout.addLayout(control_panel, 1)
        main_layout.addWidget(self.canvas, 2)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Привязка событий
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        self.res_combo.currentTextChanged.connect(self.trigger_update)
        self.w_n.textChanged.connect(self.trigger_update)
        self.btn_rand_col.clicked.connect(self.mutate_colors)
        self.btn_rand_geo.clicked.connect(self.mutate_geometry)
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        self.btn_download.clicked.connect(self.save_image_file)
        
        self.trigger_update()

    def trigger_update(self):
        global is_updating_preset
        if is_updating_preset: return
        
        s = self.controls['s'].value / 100.0
        r = self.controls['r'].value / 100.0
        h = self.controls['h'].value / 100.0
        g = self.controls['g'].value / 100.0
        o = self.controls['o'].value / 100.0
        e = self.controls['e'].value / 100.0
        a = self.controls['a'].value / 100.0
        f = self.controls['f'].value / 100.0
        lw = self.controls['lw'].value / 100.0
        
        try:
            n = int(self.w_n.text())
        except ValueError:
            n = 12
        n = max(12, min(10000, n))
        
        res_mode = self.res_combo.currentText()
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
            
            self.stats_label.setText(f"Линий на экране: {total_lines:,}")
            self.canvas.draw()

    def on_preset_changed(self, preset):
        global is_updating_preset
        is_updating_preset = True
        if preset == 'Радуга':          self.controls['s'].value, self.controls['r'].value, self.controls['h'].value, self.controls['g'].value = 0, 300, 150, 100
        elif preset == 'Киберпанк':     self.controls['s'].value, self.controls['r'].value, self.controls['h'].value, self.controls['g'].value = 225, 290, 230, 110
        elif preset == 'Огонь':         self.controls['s'].value, self.controls['r'].value, self.controls['h'].value, self.controls['g'].value = 10, 45, 190, 130
        elif preset == 'Стандарт':      self.controls['s'].value, self.controls['r'].value, self.controls['h'].value, self.controls['g'].value = 249, 76, 181, 130
        is_updating_preset = False
        self.trigger_update()

    def mutate_geometry(self):
        self.controls['e'].value = int(np.random.uniform(90, 170))
        self.controls['a'].value = int(np.random.uniform(12, 28))
        self.controls['f'].value = int(np.random.uniform(30, 130))

    def mutate_colors(self):
        global is_updating_preset
        is_updating_preset = True
        self.controls['s'].value = int(np.random.uniform(0, 300))
        self.controls['r'].value = int(np.random.uniform(0, 400))
        self.controls['h'].value = int(np.random.uniform(50, 250))
        self.controls['g'].value = int(np.random.uniform(50, 170))
        is_updating_preset = False
        self.trigger_update()

    def reset_to_defaults(self):
        global is_updating_preset
        is_updating_preset = True
        self.controls['s'].value, self.controls['r'].value, self.controls['h'].value, self.controls['g'].value, self.controls['o'].value = 249, 76, 181, 130, 50
        self.controls['e'].value, self.controls['a'].value, self.controls['f'].value, self.controls['lw'].value = 130, 19, 70, 40
        self.w_n.setText("1008")
        self.preset_combo.setCurrentText('Стандарт')
        self.res_combo.setCurrentText('FullHD (1080x1920)')
        self.format_combo.setCurrentText('PNG')
        is_updating_preset = False
        self.trigger_update()

    def save_image_file(self):
        fmt = self.format_combo.currentText().lower()
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить обои", f"collatz_wallpaper.{fmt}", f"Files (*.{fmt})", options=options)
        if file_path:
            self.lc.set_antialiaseds(True)
            current_lw = self.controls['lw'].value / 100.0
            if fmt == 'pdf':
                self.lc.set_linewidths(current_lw * 0.8)
                self.fig.savefig(file_path, facecolor='none', transparent=True, pad_inches=0)
            else:
                self.lc.set_linewidths(current_lw * 1.5)
                bg_color = 'none' if fmt != 'jpeg' else '#000000'
                self.fig.savefig(file_path, dpi=200, facecolor=bg_color, transparent=(fmt != 'jpeg'), pad_inches=0)
            self.lc.set_linewidths(current_lw)
            self.trigger_update()

if __name__ == '__main__':
    is_updating_preset = False
    app = QApplication(sys.argv)
    window = FractalApp()
    window.resize(1000, 650)
    window.show()
    sys.exit(app.exec_())
