import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QSpinBox, QTextEdit,
    QGroupBox, QFrame, QSplitter, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput


# Dữ liệu món ăn: định lượng cho 1 người
# (tên nguyên liệu, số lượng, đơn vị)
RECIPES = {
    "Món khô": {
        "Cơm chiên": [
            ("Gạo", 120, "g"),
            ("Trứng gà", 1, "quả"),
            ("Dầu ăn", 10, "ml"),
            ("Cà rốt", 30, "g"),
            ("Đậu Hà Lan", 30, "g"),
            ("Nước mắm", 5, "ml"),
        ],
        "Thịt kho": [
            ("Thịt ba chỉ", 150, "g"),
            ("Nước dừa", 100, "ml"),
            ("Trứng cút", 2, "quả"),
            ("Đường", 5, "g"),
            ("Nước mắm", 7, "ml"),
        ],
        "Rau xào": [
            ("Rau cải", 200, "g"),
            ("Tỏi", 5, "g"),
            ("Dầu ăn", 8, "ml"),
            ("Muối", 2, "g"),
        ],
    },
    "Món nước": {
        "Canh rau": [
            ("Rau ngót", 100, "g"),
            ("Thịt băm", 50, "g"),
            ("Nước", 300, "ml"),
            ("Hành lá", 5, "g"),
            ("Muối", 2, "g"),
        ],
        "Phở bò": [
            ("Bánh phở", 120, "g"),
            ("Thịt bò", 120, "g"),
            ("Nước dùng", 400, "ml"),
            ("Hành tây", 30, "g"),
            ("Hành lá", 5, "g"),
        ],
    },
    "Tráng miệng": {
        "Chè đậu xanh": [
            ("Đậu xanh", 60, "g"),
            ("Đường", 30, "g"),
            ("Nước", 200, "ml"),
            ("Nước cốt dừa", 30, "ml"),
        ],
        "Sữa chua trái cây": [
            ("Sữa chua", 1, "hộp"),
            ("Chuối", 0.5, "quả"),
            ("Dâu tây", 50, "g"),
            ("Mật ong", 10, "ml"),
        ],
        "Hoa quả dĩa": [
            ("Dưa hấu", 150, "g"),
            ("Táo", 0.5, "quả"),
            ("Nho", 80, "g"),
        ],
    },
}

# Các bước chế biến (có thể có bước có thời gian). seconds = số giây đếm ngược
# Nếu món không có trong đây, sẽ dùng hướng dẫn cơ bản mặc định.
STEPS = {
    "Cơm chiên": [
        {"text": "Vo gạo, nấu cơm để nguội (cơm khô hạt).", "seconds": None},
        {"text": "Sơ chế rau củ.", "seconds": 300},  # 5 phút
        {"text": "Phi thơm tỏi, chiên trứng, cho cơm vào đảo.", "seconds": 420},  # 7 phút
        {"text": "Nêm nếm và đảo đều tay.", "seconds": 120},  # 2 phút
    ],
    "Thịt kho": [
        {"text": "Ướp thịt với gia vị.", "seconds": 600},  # 10 phút
        {"text": "Thắng đường, cho thịt đảo săn.", "seconds": 300},  # 5 phút
        {"text": "Đổ nước dừa, kho lửa nhỏ.", "seconds": 1800},  # 30 phút
    ],
    "Rau xào": [
        {"text": "Rửa rau, để ráo.", "seconds": 300},
        {"text": "Phi tỏi với dầu, cho rau vào xào.", "seconds": 240},
        {"text": "Nêm nếm, đảo nhanh tay.", "seconds": 60},
    ],
    "Canh rau": [
        {"text": "Nấu nước sôi, cho thịt băm vào.", "seconds": 300},
        {"text": "Cho rau vào, nêm nếm.", "seconds": 240},
    ],
    "Phở bò": [
        {"text": "Chần bánh phở.", "seconds": 60},
        {"text": "Trụng thịt bò tái.", "seconds": 45},
        {"text": "Chan nước dùng nóng, thêm hành.", "seconds": None},
    ],
    "Chè đậu xanh": [
        {"text": "Ngâm đậu xanh.", "seconds": 1200},  # 20 phút
        {"text": "Nấu đậu, thêm đường.", "seconds": 900},
        {"text": "Cho nước cốt dừa vào sau cùng.", "seconds": None},
    ],
}


def format_number_vi(n: float) -> str:
    if float(n).is_integer():
        return str(int(round(n)))
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def format_quantity(amount: float, unit: str) -> str:
    if unit == "g" and amount >= 1000:
        kg = amount / 1000.0
        return f"{format_number_vi(kg)} Kg"
    if unit == "ml" and amount >= 1000:
        liters = amount / 1000.0
        return f"{format_number_vi(liters)} L"
    return f"{format_number_vi(amount)} {unit}"


def format_seconds(sec: int) -> str:
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


class SoundManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.click = self._load_effect("sounds/click.wav")
        self.alarm = self._load_effect("sounds/alarm.wav")

        self.audio_out = QAudioOutput()
        self.bgm_player = QMediaPlayer()
        self.bgm_player.setAudioOutput(self.audio_out)
        bgm_path = self._abs("sounds/bgm.mp3")
        if os.path.exists(bgm_path):
            self.bgm_player.setSource(QUrl.fromLocalFile(bgm_path))
            try:
                # Qt 6.4+: loop vô hạn
                self.bgm_player.setLoops(QMediaPlayer.Loops.Infinite)  # type: ignore[attr-defined]
            except Exception:
                self.bgm_player.mediaStatusChanged.connect(self._replay_bgm_if_finished)
            self.audio_out.setVolume(0.15)
            self.bgm_player.play()

    def _replay_bgm_if_finished(self, status):
        # Fallback khi không có setLoops
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.bgm_player.play()

    def _abs(self, rel: str) -> str:
        return os.path.join(self.base_dir, rel)

    def _load_effect(self, rel: str) -> QSoundEffect | None:
        path = self._abs(rel)
        if os.path.exists(path):
            eff = QSoundEffect()
            eff.setSource(QUrl.fromLocalFile(path))
            eff.setVolume(0.8)
            return eff
        return None

    def play_click(self):
        if self.click:
            self.click.play()

    def play_alarm(self):
        if self.alarm:
            self.alarm.play()
        else:
            QApplication.beep()


class StepRow(QFrame):
    def __init__(self, text: str, seconds: int | None, sound_mgr: SoundManager, parent=None):
        super().__init__(parent)
        self.sound_mgr = sound_mgr
        self.seconds_total = seconds
        self.seconds_left = seconds if seconds is not None else 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.lbl = QLabel(text)
        self.lbl.setWordWrap(True)
        layout.addWidget(self.lbl, 1)

        self.countdown = QLabel("")
        self.countdown.setObjectName("CountdownLabel")
        layout.addWidget(self.countdown)

        self.btn = None
        self.timer = None

        if seconds is not None:
            self.btn = QPushButton(f"Bắt đầu ({format_seconds(self.seconds_left)})")
            self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(self.btn)
            self.timer = QTimer(self)
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self._tick)
            self.btn.clicked.connect(self._start_or_stop)
            self._update_countdown_label()

    def _start_or_stop(self):
        self.sound_mgr.play_click()
        if not self.timer:
            return
        if not self.timer.isActive():
            # bắt đầu
            if self.seconds_left <= 0:
                self.seconds_left = self.seconds_total or 0
            self.timer.start()
            self.btn.setText("Đang đếm...")
            self.setProperty("active", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            # dừng
            self.timer.stop()
            self.btn.setText(f"Tiếp tục ({format_seconds(self.seconds_left)})")
            self.setProperty("active", False)
            self.style().unpolish(self)
            self.style().polish(self)

    def _tick(self):
        if self.seconds_left <= 0:
            if self.timer:
                self.timer.stop()
            self.countdown.setText("Hết giờ!")
            if self.btn:
                self.btn.setText("Bắt đầu lại")
            self.sound_mgr.play_alarm()
            QMessageBox.information(self, "Báo giờ", "Đã hết thời gian cho bước này!")
            self.setProperty("active", False)
            self.style().unpolish(self)
            self.style().polish(self)
            return
        self.seconds_left -= 1
        self._update_countdown_label()

    def _update_countdown_label(self):
        if self.seconds_total is None:
            self.countdown.setText("")
        else:
            self.countdown.setText(format_seconds(self.seconds_left))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hôm nay ăn gì?")
        self.resize(980, 620)

        self.sound_mgr = SoundManager(os.path.dirname(os.path.abspath(__file__)))

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel("Hôm nay ăn gì?")
        subtitle = QLabel("Gợi ý món ăn và hẹn giờ cho các bước chế biến")
        title.setObjectName("AppTitle")
        subtitle.setObjectName("AppSubtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header)

        group_categories = QGroupBox("Gợi ý món ăn")
        cat_layout = QHBoxLayout(group_categories)
        cat_layout.setContentsMargins(12, 10, 12, 12)
        cat_layout.setSpacing(10)

        self.btn_dry = QPushButton("Món khô")
        self.btn_soup = QPushButton("Món nước")
        self.btn_dessert = QPushButton("Tráng miệng")

        for b in (self.btn_dry, self.btn_soup, self.btn_dessert):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setMinimumHeight(36)
            b.setProperty("category", True)
            b.clicked.connect(self.sound_mgr.play_click)

        cat_layout.addWidget(self.btn_dry)
        cat_layout.addWidget(self.btn_soup)
        cat_layout.addWidget(self.btn_dessert)
        main_layout.addWidget(group_categories)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Panel trái: danh sách món
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        self.lbl_category = QLabel("Danh sách món")
        self.lbl_category.setObjectName("SectionTitle")
        self.list_dishes = QListWidget()
        self.list_dishes.setObjectName("DishList")
        self.list_dishes.setAlternatingRowColors(True)

        left_layout.addWidget(self.lbl_category)
        left_layout.addWidget(self.list_dishes, 1)

        # Panel phải: nguyên liệu + bước
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        controls = QFrame()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.lbl_people = QLabel("Số người:")
        self.spin_people = QSpinBox()
        self.spin_people.setMinimum(1)
        self.spin_people.setMaximum(50)
        self.spin_people.setValue(2)
        self.spin_people.setToolTip("Chọn số người ăn để tính định lượng nguyên liệu")

        self.btn_show = QPushButton("Xem công thức")
        self.btn_show.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show.clicked.connect(self.sound_mgr.play_click)

        controls_layout.addWidget(self.lbl_people)
        controls_layout.addWidget(self.spin_people)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.btn_show)

        self.text_recipe = QTextEdit()
        self.text_recipe.setReadOnly(True)
        self.text_recipe.setPlaceholderText("Nguyên liệu sẽ hiển thị ở đây...")

        steps_group = QGroupBox("Các bước chế biến")
        steps_group_layout = QVBoxLayout(steps_group)
        steps_group_layout.setContentsMargins(10, 10, 10, 10)
        steps_group_layout.setSpacing(6)

        # Scroll cho bước chế biến
        self.steps_scroll = QScrollArea()
        self.steps_scroll.setWidgetResizable(True)
        self.steps_host = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_host)
        self.steps_layout.setContentsMargins(4, 4, 4, 4)
        self.steps_layout.setSpacing(6)
        self.steps_scroll.setWidget(self.steps_host)
        steps_group_layout.addWidget(self.steps_scroll)

        right_layout.addWidget(controls)
        right_layout.addWidget(self.text_recipe, 1)
        right_layout.addWidget(steps_group, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([340, 640])

        # Sự kiện load
        self.btn_dry.clicked.connect(lambda: self.load_category("Món khô"))
        self.btn_soup.clicked.connect(lambda: self.load_category("Món nước"))
        self.btn_dessert.clicked.connect(lambda: self.load_category("Tráng miệng"))
        self.btn_show.clicked.connect(self.show_recipe)

        # Mặc định hiển thị
        self.load_category("Món khô")

        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { font-size: 14px; }
            #AppTitle { font-size: 24px; font-weight: 700; }
            #AppSubtitle { color: #666; }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #e6e6e6;
                border-radius: 8px;
                padding-top: 10px;
                background: #fafafa;
            }
            QPushButton[category="true"] {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 6px 14px;
            }
            QPushButton[category="true"]:hover {
                background: #f2f7ff;
                border-color: #a9c7ff;
            }
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background: #1e4fd6; }
            QPushButton:disabled { background: #a3b4ec; }
            #SectionTitle { font-weight: 700; margin-bottom: 4px; }
            #DishList {
                border: 1px solid #e6e6e6;
                border-radius: 8px;
                background: #ffffff;
            }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background: #e8f0ff; color: #1e3a8a; }
            QTextEdit {
                border: 1px solid #e6e6e6;
                border-radius: 8px;
                background: #ffffff;
                padding: 8px;
            }
            StepRow[active="true"] {
                background: #fff9e6;
                border: 1px solid #ffe8a3;
                border-radius: 8px;
            }
            #CountdownLabel { color: #555; min-width: 56px; qproperty-alignment: 'AlignRight|AlignVCenter'; }
        """)

    def clear_steps(self):
        while self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def load_steps(self, dish_name: str):
        self.clear_steps()
        steps = STEPS.get(dish_name)
        if not steps:
            steps = [
                {"text": "Sơ chế nguyên liệu.", "seconds": None},
                {"text": "Nấu/chế biến theo món.", "seconds": None},
                {"text": "Nêm nếm vừa ăn và trình bày.", "seconds": None},
            ]
        for s in steps:
            row = StepRow(s["text"], s["seconds"], self.sound_mgr, self.steps_host)
            self.steps_layout.addWidget(row)
        self.steps_layout.addStretch(1)

    def load_category(self, category_name: str) -> None:
        self.lbl_category.setText(f"Danh sách món: {category_name}")
        self.list_dishes.clear()
        dishes = RECIPES.get(category_name, {})
        for dish_name in dishes.keys():
            self.list_dishes.addItem(dish_name)
        if self.list_dishes.count() > 0:
            self.list_dishes.setCurrentRow(0)

    def show_recipe(self) -> None:
        current_category = self.lbl_category.text().replace("Danh sách món: ", "")
        current_item = self.list_dishes.currentItem()
        if not current_item:
            self.text_recipe.setPlainText("Vui lòng chọn một món.")
            self.clear_steps()
            return

        dish_name = current_item.text()
        base_ingredients = RECIPES.get(current_category, {}).get(dish_name, [])
        people = self.spin_people.value()

        lines = [
            f"Món: {dish_name}",
            f"Số người: {people}",
            "-" * 30,
            "Nguyên liệu:"
        ]
        for ingredient_name, base_amount, unit in base_ingredients:
            total_amount = base_amount * people
            lines.append(f"- {ingredient_name}: {format_quantity(total_amount, unit)}")

        self.text_recipe.setPlainText("\n".join(lines))
        self.load_steps(dish_name)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()