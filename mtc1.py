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
import pandas as pd  # Đã thêm: Import thư viện pandas

# Dữ liệu món ăn: định lượng cho 1 người
# (tên nguyên liệu, số lượng, đơn vị)
# Dữ liệu này sẽ được TỰ ĐỘNG GHI ĐÈ khi nhấn nút Update.
# Khởi tạo rỗng để dữ liệu được tải từ file recipes.xlsx ngay khi chương trình khởi động
RECIPES = {}  # <--- ĐÃ BỎ HẾT DỮ LIỆU CỨNG Ở ĐÂY

# Các bước chế biến (có thể có bước có thời gian). seconds = số giây đếm ngược
# Dữ liệu này sẽ được TỰ ĐỘNG GHI ĐÈ khi nhấn nút Update.
# Khởi tạo rỗng để dữ liệu được tải từ file recipes.xlsx ngay khi chương trình khởi động
STEPS = {}  # <--- ĐÃ BỎ HẾT DỮ LIỆU CỨNG Ở ĐÂY


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

        # Thêm nút Update
        self.btn_update = QPushButton("Update")
        self.btn_update.setObjectName("btn_update")
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)

        controls_layout.addWidget(self.lbl_people)
        controls_layout.addWidget(self.spin_people)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.btn_update)
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

        # Kết nối nút Update
        self.btn_update.clicked.connect(self.read_data_from_excel)

        # Tải dữ liệu từ Excel ngay khi khởi động
        self.read_data_from_excel()  # <--- ĐÃ THÊM: Tải dữ liệu ngay khi khởi động

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

            /* Thêm Style cho nút Update */
            #btn_update { background: #059669; }
            #btn_update:hover { background: #047857; }
        """)

    # --- HÀM XỬ LÝ DỮ LIỆU EXCEL ---

    def _process_recipes_sheet(self, xls: pd.ExcelFile) -> dict:
        """Đọc và chuyển đổi sheet Recipes thành dictionary RECIPES."""
        new_recipes = {}
        sheet_name = "Recipes"  # Giả định sheet tên là "Recipes"
        if sheet_name not in xls.sheet_names:
            return {}

        df = xls.parse(sheet_name, header=0)
        # Ánh xạ tên cột từ file CSV bạn cung cấp
        df.columns = ['Category', 'DishName', 'Ingredient', 'BaseAmount', 'Unit']
        df = df.dropna(subset=['Category', 'DishName', 'Ingredient', 'BaseAmount', 'Unit'])

        for category_name, cat_group in df.groupby('Category'):
            category_dishes = {}
            for dish_name, dish_group in cat_group.groupby('DishName'):
                ingredients_list = []
                for index, row in dish_group.iterrows():
                    try:
                        amount = float(row['BaseAmount'])
                        ingredients_list.append((
                            str(row['Ingredient']).strip(),
                            amount,
                            str(row['Unit']).strip()
                        ))
                    except ValueError:
                        # Bỏ qua nếu Số lượng không phải là số
                        continue

                if ingredients_list:
                    category_dishes[str(dish_name).strip()] = ingredients_list

            if category_dishes:
                new_recipes[str(category_name).strip()] = category_dishes
        return new_recipes

    def _process_steps_sheet(self, xls: pd.ExcelFile) -> dict:
        """Đọc và chuyển đổi sheet Steps thành dictionary STEPS."""
        new_steps = {}
        sheet_name = "Steps"  # Giả định sheet tên là "Steps"
        if sheet_name not in xls.sheet_names:
            return {}

        df = xls.parse(sheet_name, header=0)
        # Ánh xạ tên cột từ file CSV bạn cung cấp
        df.columns = ['DishName', 'StepText', 'TimeMinutes', 'TimeSeconds']
        df = df.dropna(subset=['DishName', 'StepText'])

        # Điền các giá trị trống trong cột Tên món bằng giá trị trước đó (forward fill)
        # để gán các bước phụ cho món chính
        df['DishName'] = df['DishName'].ffill()

        for dish_name, dish_group in df.groupby('DishName'):
            steps_list = []
            for index, row in dish_group.iterrows():
                total_seconds = None

                # Tính toán thời gian: ưu tiên Thời gian (giây), nếu không có thì lấy Thời gian (phút) * 60
                seconds = row.get('TimeSeconds')
                minutes = row.get('TimeMinutes')

                try:
                    if pd.notna(seconds) and float(seconds) > 0:
                        total_seconds = int(float(seconds))
                    elif pd.notna(minutes) and float(minutes) > 0:
                        total_seconds = int(float(minutes) * 60)
                except ValueError:
                    pass

                steps_list.append({
                    "text": str(row['StepText']).strip(),
                    "seconds": total_seconds
                })

            if steps_list:
                new_steps[str(dish_name).strip()] = steps_list

        return new_steps

    def read_data_from_excel(self):
        """Đọc cả công thức (RECIPES) và bước chế biến (STEPS) từ file recipes.xlsx."""
        self.sound_mgr.play_click()
        # Giả định file recipes.xlsx nằm cùng thư mục
        excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes.xlsx")

        if not os.path.exists(excel_path):
            QMessageBox.critical(self, "Lỗi", f"Không tìm thấy file recipes.xlsx tại đường dẫn: {excel_path}")
            return

        try:
            # Đọc file Excel
            xls = pd.ExcelFile(excel_path)

            # 1. XỬ LÝ DỮ LIỆU CÔNG THỨC (RECIPES)
            new_recipes = self._process_recipes_sheet(xls)

            # 2. XỬ LÝ DỮ LIỆU BƯỚC CHẾ BIẾN (STEPS)
            new_steps = self._process_steps_sheet(xls)

            # Cập nhật biến toàn cục
            global RECIPES
            global STEPS

            # Chỉ cập nhật nếu dữ liệu mới đọc được là hợp lệ
            if new_recipes:
                RECIPES = new_recipes
            if new_steps:
                STEPS = new_steps

            # Cập nhật lại giao diện
            # Lấy danh mục đầu tiên (nếu có) để tải lên UI
            first_category = next(iter(RECIPES.keys()), None)
            if first_category:
                self.load_category(first_category)

            QMessageBox.information(self, "Hoàn tất",
                                    "Đã cập nhật công thức và bước chế biến thành công từ file recipes.xlsx.")

        except FileNotFoundError:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy file recipes.xlsx.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Đọc File", f"Đã xảy ra lỗi khi đọc file Excel: {e}")

    # --- CÁC HÀM CÒN LẠI ---

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