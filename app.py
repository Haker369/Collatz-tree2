import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QComboBox, QSpinBox, 
                             QLabel, QFrame, QScrollArea, QFileDialog)
from PyQt6.QtCore import Qt

# ==========================================
# ОПТИМИЗИРОВАННЫЙ ДИНАМИЧЕСКИЙ КЭШ
# ==========================================
np.random.seed(42)
STATIC_START_NUMBERS = np.random.randint(1, 1000000, size=10000)
COLLATZ_CACHE = {}

def get_collatz_sequence(idx):
    """ Ленивый расчет: вычисляет траекторию только при первом обращении """
    global COLLATZ_CACHE
    if idx not in COLLATZ_CACHE:
        n = int(STATIC_START_NUMBERS[idx])
        seq = [n]
        append = seq.append
        while n != 1:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            append(n)
        COLLATZ_CACHE[idx] = np.array(seq[::-1], dtype=float)
    return COLLATZ_CACHE[idx]


class HybridControl(QWidget):
    """ Кастомный виджет, полностью заменяющий гибридные слайдеры ipywidgets """
    def __init__(self, label_text, default_val, min_val, max_val, callback):
        super().__init__()
        self.callback = callback
        self.min_val = min_val
        self.max_val = max_val
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        
        # Светодиод-индикатор состояния
        self.indicator = QLabel()
        self.indicator.setFixedSize(10, 10)
        layout.addWidget(self.indicator)
        
        # Метка параметра
        lbl = QLabel(label_text)
        lbl.setFixedWidth(130)
        lbl.setStyleSheet("color: #8189a2; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl)
        
        # Ползунок (в PyQt SpinBox выступает основным контроллером значения)
        self.slider = QSpinBox()
        self.slider.setRange(int(min_val), int(max_val))
        self.slider.setValue(int(default_val))
        self.slider.setStyleSheet("background-color: #02040a; border: 1px solid #4b598c; color: white;")
        self.slider.setFixedWidth(160)
        self.slider.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.slider)
        
        # Стрелка назад
        self.btn_minus = QPushButton("◀")
        self.btn_minus.setFixedSize(26, 26)
        self.btn_minus.setStyleSheet("background-color: #1e2640; color: #8fa3cc; border-radius: 4px; font-weight: bold;")
        self.btn_minus.clicked.connect(lambda: self.slider.setValue(self.slider.value() - 1))
        layout.addWidget(self.btn_minus)
        
        # Текстовое поле ввода
        self.num_field = QSpinBox()
        self.num_field.setRange(int(min_val), int(max_val))
        self.num_field.setValue(int(default_val))
        self.num_field.setStyleSheet("background-color: #02040a; border: 1px solid #4b598c; color: white;")
        self.num_field.setFixedWidth(60)
        self.num_field.valueChanged.connect(self.slider.setValue)
        layout.addWidget(self.num_field)
        
        # Стрелка вперед
        self.btn_plus = QPushButton("▶")
        self.btn_plus.setFixedSize(26, 26)
        self.btn_plus.setStyleSheet("background-color: #1e2640; color: #8fa3cc; border-radius: 4px; font-weight: bold;")
        self.btn_plus.clicked.connect(lambda: self.slider.setValue(self.slider.value() + 1))
        layout.addWidget(self.btn_plus)
        
        self.update_indicator(default_val)
        
    def on_value_changed(self, val):
        self.num_field.setValue(val)
        self.update_indicator(val)
        self.callback()
        
    def update_indicator(self, val):
        if abs(val - self.min_val) < 0.01:
            self.indicator.setStyleSheet("background-color: #dc3545; border-radius: 5px;")
        elif abs(val - self.max_val) < 0.01:
            self.indicator.setStyleSheet("background-color: #28a745; border-radius: 5px;")
        else:
            self.indicator.setStyleSheet("background-color: #ffc107; border-radius: 5px;")

    def value(self):
        return self.slider.value()

    def set_value(self, val):
        self.slider.setValue(int(val))


class CollatzFractalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Collatz Fractal Generator 4K (Offline)")
        self.setStyleSheet("background-color: #02040a; color: #8fa3cc; font-family: sans-serif;")
        
        self.is_updating_preset = False
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        h_layout = QHBoxLayout(main_widget)
        
        # Боковая интерактивная панель управления
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(530)
        scroll.setStyleSheet("border: none; background-color: #060919;")
        
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #060919; border-right: 1px solid #1e2640;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        
        sidebar_layout.addWidget(QLabel("Пресет фрактала:"))
        self.preset_dropdown = QComboBox()
        self.preset_dropdown.addItems(['Стандарт', 'Радуга', 'Киберпанк', 'Огонь'])
        self.preset_dropdown.setStyleSheet("background-color: #02040a; color: white; padding: 4px; border: 1px solid #1e2640;")
        self.preset_dropdown.currentTextChanged.connect(self.apply_preset)
        sidebar_layout.addWidget(self.preset_dropdown)
        
        sidebar_layout.addWidget(QLabel("Разрешение холста:"))
        self.res_dropdown = QComboBox()
        self.res_dropdown.addItems(['FullHD (1080x1920)', '2K (1440x2560)', '4K (2160x3840)'])
        self.res_dropdown.setStyleSheet("background-color: #02040a; color: white; padding: 4px; border: 1px solid #1e2640;")
        self.res_dropdown.currentTextChanged.connect(self.update_fractal)
        sidebar_layout.addWidget(self.res_dropdown)
        
        # Генерация гибридной группы параметров
        self.w_n = HybridControl("Число нитей (N)", 12, 1, 1000, self.update_fractal)
        self.w_s = HybridControl("Смещение спектра (S)", 0, -500, 500, self.update_fractal)
        self.w_r = HybridControl("Радиус цвета (R)", 100, -500, 500, self.update_fractal)
        self.w_h = HybridControl("Интенсивность (H)", 100, -500, 500, self.update_fractal)
        self.w_g = HybridControl("Спад градиента (G)", 100, 1, 500, self.update_fractal)
        self.w_o = HybridControl("Прозрачность (O)", 100, 0, 100, self.update_fractal)
        self.w_e = HybridControl("Масштаб нитей (E)", 0, -200, 200, self.update_fractal)
        self.w_a = HybridControl("Угол поворота (A)", 15, -360, 360, self.update_fractal)
        self.w_f = HybridControl("Множитель фазы (F)", 100, -500, 500, self.update_fractal)
        self.w_lw = HybridControl("Толщина линий (LW)", 50, 1, 500, self.update_fractal)
        
        for widget in [self.w_n, self.w_s, self.w_r, self.w_h, self.w_g, self.w_o, self.w_e, self.w_a, self.w_f, self.w_lw]:
            sidebar_layout.addWidget(widget)
            
        # Информационный блок
        self.stats_label = QLabel("Линий на экране: 0")
        self.stats_label.setStyleSheet("background-color: #12162d; border: 1px solid #3c445c; padding: 8px; border-radius: 6px; font-weight: bold; color: #28a745; margin: 10px 0;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.stats_label)
        
        sidebar_layout.addWidget(QLabel("Формат сохранения:"))
        self.format_dropdown = QComboBox()
        self.format_dropdown.addItems(['PNG', 'JPEG', 'PDF'])
        self.format_dropdown.setStyleSheet("background-color: #02040a; color: white; padding: 4px; border: 1px solid #1e2640;")
        sidebar_layout.addWidget(self.format_dropdown)
        
        self.btn_save = QPushButton("💾 Сохранить изображение обоев")
        self.btn_save.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px; border-radius: 6px; margin-top: 5px;")
        self.btn_save.clicked.connect(self.save_image_action)
        sidebar_layout.addWidget(self.btn_save)
        
        scroll.setWidget(sidebar)
        h_layout.addWidget(scroll)
        
        # Правая часть: холст Matplotlib для рендеринга фрактала
        self.fig, self.ax = plt.subplots(figsize=(10.8, 19.2), dpi=70, facecolor='none')
        self.ax.set_facecolor('none')
        self.lc = LineCollection([], linewidths=0.5)
        self.ax.add_collection(self.lc)
        
        self.canvas = FigureCanvas(self.fig)
        h_layout.addWidget(self.canvas, 1)
        
        self.update_fractal()

    def update_fractal(self):
        if self.is_updating_preset: return

        s = self.w_s.value() / 100.0
        r = self.w_r.value() / 100.0
        h = self.w_h.value() / 100.0
        g = self.w_g.value() / 100.0
        o = self.w_o.value() / 100.0
        e = self.w_e.value() / 100.0
        a = self.w_a.value() / 100.0
        f = self.w_f.value() / 100.0
        lw = self.w_lw.value() / 100.0
        n = int(self.w_n.value())
        
        res_mode = self.res_dropdown.currentText()
        if 'FullHD' in res_mode: self.fig.set_size_inches(10.8, 19.2)
        elif '2K' in res_mode: self.fig.set_size_inches(14.4, 25.6)
        elif '4K' in res_mode: self.fig.set_size_inches(21.6, 38.4)

        all_segments = []
        all_colors = []
        xmin, xmax = float('inf'), float('-inf')
        ymin, ymax = float('inf'), float('-inf')
        total_lines = 0

        for idx in range(n):
            seq = get_collatz_sequence(idx)
            steps = seq / (1.0 + np.power(seq, e))
            angles = a * (f - 2.0 * (seq % 2))
            cum_angles = np.cumsum(angles)
            
            dx = steps * np.cos(cum_angles)
            dy = steps * np.sin(cum_angles)
            
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
            self.ax.axis('off')
            self.fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
            
            self.stats_label.setText(f"Линий на экране: {total_lines:,}")
            self.canvas.draw()

    def apply_preset(self, name):
        self.is_updating_preset = True
        if name == 'Стандарт':
            self.w_s.set_value(0); self.w_r.set_value(100); self.w_h.set_value(100); self.w_g.set_value(100)
        elif name == 'Радуга':
            self.w_s.set_value(150); self.w_r.set_value(320); self.w_h.set_value(250); self.w_g.set_value(80)
        elif name == 'Киберпанк':
            self.w_s.set_value(-200); self.w_r.set_value(450); self.w_h.set_value(120); self.w_g.set_value(150)
        elif name == 'Огонь':
            self.w_s.set_value(50); self.w_r.set_value(-150); self.w_h.set_value(400); self.w_g.set_value(60)
        self.is_updating_preset = False
        self.update_fractal()

    def save_image_action(self):
        fmt = self.format_dropdown.currentText().lower()
        
        # Нативный Windows-диалог выбора пути сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить фрактал", f"collatz_fractal_4k.{fmt}", f"Files (*.{fmt})"
        )
        if not file_path: return
        
        self.lc.set_antialiaseds(True)
        current_lw = self.w_lw.value() / 100.0
        
        if fmt == 'pdf':
            self.lc.set_linewidths(current_lw * 0.8)
            self.fig.savefig(file_path, facecolor='none', transparent=True, pad_inches=0)
        else:
            self.lc.set_linewidths(current_lw * 1.5)
            bg_color = 'none' if fmt != 'jpeg' else '#000000'
            self.fig.savefig(file_path, dpi=300, facecolor=bg_color, transparent=(fmt != 'jpeg'), pad_inches=0)
            
        self.lc.set_linewidths(current_lw)
        self.update_fractal()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CollatzFractalApp()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
