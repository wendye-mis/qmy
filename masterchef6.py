# ============================================================================
# CHƯƠNG TRÌNH: "HÔM NAY ĂN GÌ?"
# ============================================================================
# Đây là ứng dụng gợi ý món ăn và hẹn giờ cho các bước chế biến
# Sử dụng PyQt6 để tạo giao diện đồ họa
# ============================================================================

import sys  # Dùng để thoát chương trình
import os  # Dùng để làm việc với đường dẫn file

# Nhập các thành phần cần thiết từ PyQt6
from PyQt6.QtWidgets import (
    QApplication,  # Lớp chính để chạy ứng dụng
    QMainWindow,  # Cửa sổ chính của ứng dụng
    QWidget,  # Widget cơ bản (container)
    QVBoxLayout,  # Bố cục theo chiều dọc (Vertical)
    QHBoxLayout,  # Bố cục theo chiều ngang (Horizontal)
    QPushButton,  # Nút bấm
    QListWidget,  # Danh sách có thể cuộn
    QLabel,  # Nhãn hiển thị text
    QSpinBox,  # Ô nhập số (spinner)
    QTextEdit,  # Ô hiển thị văn bản nhiều dòng
    QGroupBox,  # Nhóm có viền và tiêu đề
    QFrame,  # Khung chứa widget khác
    QSplitter,  # Chia màn hình thành các phần
    QMessageBox,  # Hộp thông báo
    QScrollArea  # Vùng có thể cuộn
)
from PyQt6.QtCore import Qt, QTimer, QUrl  # Core: các hằng số, timer, URL
from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput  # Phát âm thanh
from PyQt6.uic import loadUi  # Dùng để tải giao diện từ file .ui

# Import module đọc Excel
from excel_loader import load_data_from_excel

# ============================================================================
# DỮ LIỆU MÓN ĂN: Định lượng cho 1 người
# ============================================================================
# Cấu trúc: RECIPES = {
#   "Tên danh mục": {
#       "Tên món": [
#           ("Tên nguyên liệu", số lượng, "đơn vị"),
#           ...
#       ],
#       ...
#   },
#   ...
# }
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

# ============================================================================
# DỮ LIỆU CÁC BƯỚC CHẾ BIẾN
# ============================================================================
# Một số bước có thời gian đếm ngược (seconds = số giây)
# Nếu món không có trong đây, sẽ dùng hướng dẫn mặc định
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


# ============================================================================
# HÀM CHUYỂN ĐỔI SỐ THÀNH ĐỊNH DẠNG VIỆT NAM
# ============================================================================
def format_number_vi(n: float) -> str:
    """
    Chuyển số thành chuỗi theo định dạng Việt Nam
    Ví dụ: 1.5 -> "1,5", 2.0 -> "2"

    Tham số:
        n (float): Số cần chuyển đổi

    Trả về:
        str: Chuỗi số đã định dạng
    """
    # Nếu là số nguyên, bỏ phần thập phân
    if float(n).is_integer():
        return str(int(round(n)))

    # Format với 2 chữ số thập phân, bỏ số 0 thừa ở cuối
    s = f"{n:.2f}".rstrip("0").rstrip(".")

    # Thay dấu chấm (.) bằng dấu phẩy (,) theo kiểu Việt Nam
    return s.replace(".", ",")


# ============================================================================
# HÀM ĐỊNH DẠNG SỐ LƯỢNG NGUYÊN LIỆU
# ============================================================================
def format_quantity(amount: float, unit: str) -> str:
    """
    Định dạng số lượng nguyên liệu, tự động đổi đơn vị lớn hơn nếu cần
    Ví dụ: 1500g -> "1,5 Kg", 2000ml -> "2 L"

    Tham số:
        amount (float): Số lượng
        unit (str): Đơn vị hiện tại (g, ml, etc.)

    Trả về:
        str: Chuỗi đã định dạng với đơn vị phù hợp
    """
    # Nếu là gram và >= 1000, đổi sang Kg
    if unit == "g" and amount >= 1000:
        kg = amount / 1000.0
        return f"{format_number_vi(kg)} Kg"

    # Nếu là ml và >= 1000, đổi sang Lít
    if unit == "ml" and amount >= 1000:
        liters = amount / 1000.0
        return f"{format_number_vi(liters)} L"

    # Giữ nguyên đơn vị gốc
    return f"{format_number_vi(amount)} {unit}"


# ============================================================================
# HÀM ĐỊNH DẠNG THỜI GIAN (GIÂY -> MM:SS)
# ============================================================================
def format_seconds(sec: int) -> str:
    """
    Chuyển số giây thành định dạng MM:SS
    Ví dụ: 125 -> "02:05", 3600 -> "60:00"

    Tham số:
        sec (int): Số giây cần chuyển đổi

    Trả về:
        str: Chuỗi thời gian dạng MM:SS
    """
    m = sec // 60  # Số phút (chia nguyên)
    s = sec % 60  # Số giây còn lại (chia dư)
    return f"{m:02d}:{s:02d}"  # Format 2 chữ số, thêm số 0 ở đầu nếu cần


# ============================================================================
# LỚP QUẢN LÝ ÂM THANH
# ============================================================================
class SoundManager:
    """
    Quản lý tất cả các âm thanh trong ứng dụng:
    - Âm thanh click khi bấm nút
    - Âm thanh báo giờ khi hết thời gian
    - Nhạc nền (BGM) phát lặp lại
    """

    def __init__(self, base_dir: str):
        """
        Khởi tạo SoundManager

        Tham số:
            base_dir (str): Thư mục gốc của ứng dụng (để tìm file âm thanh)
        """
        self.base_dir = base_dir  # Lưu đường dẫn thư mục gốc

        # Tải các file âm thanh
        self.click = self._load_effect("sounds/click.wav")  # Âm thanh click
        self.alarm = self._load_effect("sounds/alarm.wav")  # Âm thanh báo giờ

        # Tạo audio output để phát nhạc nền
        self.audio_out = QAudioOutput()

        # Tạo media player cho nhạc nền
        self.bgm_player = QMediaPlayer()
        self.bgm_player.setAudioOutput(self.audio_out)

        # Tìm file nhạc nền
        bgm_path = self._abs("sounds/bgm.mp3")
        if os.path.exists(bgm_path):
            # Nếu tìm thấy, thiết lập nguồn phát
            self.bgm_player.setSource(QUrl.fromLocalFile(bgm_path))

            try:
                # Thử phát lặp lại vô hạn (Qt 6.4+)
                self.bgm_player.setLoops(QMediaPlayer.Loops.Infinite)  # type: ignore[attr-defined]
            except Exception:
                # Nếu không hỗ trợ, dùng cách khác: tự động phát lại khi hết
                self.bgm_player.mediaStatusChanged.connect(self._replay_bgm_if_finished)

            # Đặt âm lượng nhạc nền (15% để không quá to)
            self.audio_out.setVolume(0.15)

            # Bắt đầu phát nhạc
            self.bgm_player.play()

    def _replay_bgm_if_finished(self, status):
        """
        Hàm dự phòng: tự động phát lại nhạc nền khi hết
        (Dùng khi không hỗ trợ setLoops)

        Tham số:
            status: Trạng thái của media player
        """
        # Khi nhạc phát xong (EndOfMedia), phát lại từ đầu
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.bgm_player.play()

    def _abs(self, rel: str) -> str:
        """
        Chuyển đường dẫn tương đối thành tuyệt đối

        Tham số:
            rel (str): Đường dẫn tương đối (ví dụ: "sounds/click.wav")

        Trả về:
            str: Đường dẫn tuyệt đối
        """
        return os.path.join(self.base_dir, rel)

    def _load_effect(self, rel: str) -> QSoundEffect | None:
        """
        Tải file âm thanh hiệu ứng (WAV)

        Tham số:
            rel (str): Đường dẫn tương đối đến file âm thanh

        Trả về:
            QSoundEffect | None: Đối tượng âm thanh nếu tìm thấy file, None nếu không
        """
        path = self._abs(rel)

        # Kiểm tra file có tồn tại không
        if os.path.exists(path):
            eff = QSoundEffect()  # Tạo đối tượng âm thanh
            eff.setSource(QUrl.fromLocalFile(path))  # Đặt nguồn phát
            eff.setVolume(0.8)  # Đặt âm lượng 80%
            return eff

        return None  # Không tìm thấy file

    def play_click(self):
        """Phát âm thanh khi click nút"""
        if self.click:
            self.click.play()
        # Nếu không có file, không làm gì (im lặng)

    def play_alarm(self):
        """Phát âm thanh báo giờ khi hết thời gian"""
        if self.alarm:
            self.alarm.play()
        else:
            # Nếu không có file, dùng tiếng beep của hệ thống
            QApplication.beep()


# ============================================================================
# LỚP HIỂN THỊ MỘT BƯỚC CHẾ BIẾN (CÓ THỂ CÓ HẸN GIỜ)
# ============================================================================
class StepRow(QFrame):
    """
    Mỗi StepRow là một dòng hiển thị một bước chế biến
    - Hiển thị mô tả bước
    - Nếu có thời gian: có nút bắt đầu/dừng đếm ngược
    - Hiển thị thời gian còn lại
    """

    def __init__(self, text: str, seconds: int | None, sound_mgr: SoundManager, parent=None):
        """
        Khởi tạo một StepRow

        Tham số:
            text (str): Mô tả bước chế biến
            seconds (int | None): Số giây cần đếm ngược (None = không có hẹn giờ)
            sound_mgr (SoundManager): Quản lý âm thanh để phát khi click
            parent: Widget cha (tùy chọn)
        """
        super().__init__(parent)  # Gọi hàm khởi tạo của QFrame

        self.sound_mgr = sound_mgr  # Lưu tham chiếu đến SoundManager

        # Lưu thời gian
        self.seconds_total = seconds  # Tổng thời gian ban đầu
        self.seconds_left = seconds if seconds is not None else 0  # Thời gian còn lại

        # Tạo bố cục ngang cho dòng này
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)  # Khoảng cách trong khung
        layout.setSpacing(8)  # Khoảng cách giữa các widget

        # Nhãn mô tả bước (bên trái)
        self.lbl = QLabel(text)
        self.lbl.setWordWrap(True)  # Cho phép xuống dòng nếu text dài
        layout.addWidget(self.lbl, 1)  # Thêm vào layout, tỷ lệ 1 (chiếm nhiều chỗ)

        # Nhãn hiển thị thời gian đếm ngược (giữa)
        self.countdown = QLabel("")
        self.countdown.setObjectName("CountdownLabel")  # Đặt tên để CSS
        layout.addWidget(self.countdown)

        # Các biến cho nút và timer (khởi tạo sau)
        self.btn = None  # Nút bắt đầu/dừng
        self.timer = None  # Timer đếm ngược

        # Chỉ tạo nút và timer nếu bước này có hẹn giờ
        if seconds is not None:
            # Tạo nút với text hiển thị thời gian
            self.btn = QPushButton(f"Bắt đầu ({format_seconds(self.seconds_left)})")
            self.btn.setCursor(Qt.CursorShape.PointingHandCursor)  # Con trỏ tay khi hover
            layout.addWidget(self.btn)  # Thêm nút vào layout

            # Tạo timer: mỗi 1 giây (1000ms) sẽ gọi hàm _tick
            self.timer = QTimer(self)
            self.timer.setInterval(1000)  # 1000ms = 1 giây
            self.timer.timeout.connect(self._tick)  # Kết nối sự kiện

            # Khi click nút, gọi hàm _start_or_stop
            self.btn.clicked.connect(self._start_or_stop)

            # Cập nhật nhãn thời gian lần đầu
            self._update_countdown_label()

    def _start_or_stop(self):
        """
        Xử lý khi click nút: bắt đầu hoặc dừng đếm ngược
        """
        self.sound_mgr.play_click()  # Phát âm thanh click

        if not self.timer:
            return  # An toàn: nếu không có timer thì không làm gì

        if not self.timer.isActive():  # Nếu timer đang dừng
            # BẮT ĐẦU đếm ngược
            # Nếu thời gian đã hết, reset về thời gian ban đầu
            if self.seconds_left <= 0:
                self.seconds_left = self.seconds_total or 0

            self.timer.start()  # Bắt đầu đếm
            self.btn.setText("Đang đếm...")  # Đổi text nút

            # Đổi style để người dùng biết đang đếm (màu vàng)
            self.setProperty("active", True)
            self.style().unpolish(self)  # Xóa style cũ
            self.style().polish(self)  # Áp dụng style mới

        else:  # Nếu timer đang chạy
            # DỪNG đếm ngược
            self.timer.stop()  # Dừng đếm
            self.btn.setText(f"Tiếp tục ({format_seconds(self.seconds_left)})")  # Đổi text

            # Đổi style về bình thường
            self.setProperty("active", False)
            self.style().unpolish(self)
            self.style().polish(self)

    def _tick(self):
        """
        Hàm được gọi mỗi giây khi timer chạy: giảm thời gian còn lại
        """
        # Nếu hết thời gian
        if self.seconds_left <= 0:
            if self.timer:
                self.timer.stop()  # Dừng timer

            self.countdown.setText("Hết giờ!")  # Hiển thị "Hết giờ!"
            if self.btn:
                self.btn.setText("Bắt đầu lại")  # Đổi text nút

            # Phát âm thanh báo giờ
            self.sound_mgr.play_alarm()

            # Hiện hộp thông báo
            QMessageBox.information(self, "Báo giờ", "Đã hết thời gian cho bước này!")

            # Đổi style về bình thường
            self.setProperty("active", False)
            self.style().unpolish(self)
            self.style().polish(self)
            return  # Dừng hàm

        # Chưa hết giờ: giảm 1 giây
        self.seconds_left -= 1
        self._update_countdown_label()  # Cập nhật hiển thị

    def _update_countdown_label(self):
        """
        Cập nhật nhãn hiển thị thời gian còn lại
        """
        if self.seconds_total is None:
            # Nếu không có hẹn giờ, không hiển thị gì
            self.countdown.setText("")
        else:
            # Hiển thị thời gian dạng MM:SS
            self.countdown.setText(format_seconds(self.seconds_left))


# ============================================================================
# LỚP CỬA SỔ CHÍNH CỦA ỨNG DỤNG
# ============================================================================
class MainWindow(QMainWindow):
    """
    Cửa sổ chính của ứng dụng "Hôm nay ăn gì?"
    Quản lý toàn bộ giao diện và logic tương tác
    Giao diện được tải từ file main.ui
    """

    def __init__(self):
        """
        Khởi tạo cửa sổ chính
        """
        super().__init__()  # Gọi hàm khởi tạo của QMainWindow

        # Xác định thư mục gốc
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Đọc dữ liệu từ Excel (nếu có), nếu không thì dùng dữ liệu mặc định
        excel_recipes, excel_steps = load_data_from_excel(self.base_dir)

        # Sử dụng dữ liệu từ Excel nếu có, nếu không thì dùng dữ liệu mặc định
        global RECIPES, STEPS
        if excel_recipes:
            RECIPES = excel_recipes
        if excel_steps:
            STEPS = excel_steps

        # Load UI từ file .ui (giao diện đã thiết kế sẵn)
        # Tìm file main.ui ở nhiều vị trí có thể
        current_dir = self.base_dir
        parent_dir = os.path.dirname(current_dir)

        # Thử tìm file ở thư mục hiện tại trước
        ui_path = os.path.join(current_dir, "main.ui")
        if not os.path.exists(ui_path):
            # Nếu không có, thử ở thư mục cha
            ui_path = os.path.join(parent_dir, "main.ui")

        # Nếu vẫn không tìm thấy, báo lỗi
        if not os.path.exists(ui_path):
            raise FileNotFoundError(
                f"Không tìm thấy file main.ui ở:\n- {os.path.join(current_dir, 'main.ui')}\n- {os.path.join(parent_dir, 'main.ui')}")

        loadUi(ui_path, self)  # Tải giao diện vào cửa sổ này

        # Tạo SoundManager: quản lý âm thanh
        self.sound_mgr = SoundManager(self.base_dir)

        # Kết nối signals cho các button category (nút danh mục)
        # Đặt thuộc tính CSS và kết nối âm thanh click
        for b in (self.btn_dry, self.btn_soup, self.btn_dessert):
            b.setProperty("category", True)  # Đánh dấu để CSS style
            b.clicked.connect(self.sound_mgr.play_click)  # Phát âm thanh khi click

        # Kết nối các sự kiện (signals) cho các nút
        # Khi click nút danh mục: load danh sách món tương ứng
        self.btn_dry.clicked.connect(lambda: self.load_category("Món khô"))
        self.btn_soup.clicked.connect(lambda: self.load_category("Món nước"))
        self.btn_dessert.clicked.connect(lambda: self.load_category("Tráng miệng"))

        # Khi click nút "Xem công thức": hiển thị nguyên liệu và bước chế biến
        self.btn_show.clicked.connect(self.show_recipe)
        self.btn_show.clicked.connect(self.sound_mgr.play_click)  # Phát âm thanh

        # Thiết lập kích thước ban đầu cho splitter (chia màn hình)
        # [340, 640] = panel trái 340px, panel phải 640px
        self.splitter.setSizes([340, 640])

        # Áp dụng CSS stylesheet để tạo giao diện đẹp
        self.apply_styles()

        # Mặc định hiển thị danh mục "Món khô"
        self.load_category("Món khô")

    def apply_styles(self):
        """
        Áp dụng CSS để tạo giao diện đẹp
        """
        self.setStyleSheet("""
            /* Font chữ mặc định cho toàn bộ */
            QWidget { font-size: 14px; }

            /* Tiêu đề chính: to, đậm */
            #AppTitle { font-size: 24px; font-weight: 700; }

            /* Tiêu đề phụ: màu xám */
            #AppSubtitle { color: #666; }

            /* Nhóm (GroupBox): có viền, nền xám nhạt */
            QGroupBox {
                font-weight: 600;
                border: 1px solid #e6e6e6;
                border-radius: 8px;
                padding-top: 10px;
                background: #fafafa;
            }

            /* Nút danh mục: nền trắng, viền nhẹ */
            QPushButton[category="true"] {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 6px 14px;
            }

            /* Nút danh mục khi hover: nền xanh nhạt */
            QPushButton[category="true"]:hover {
                background: #f2f7ff;
                border-color: #a9c7ff;
            }

            /* Nút thường: nền xanh dương, chữ trắng */
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }

            /* Nút khi hover: xanh đậm hơn */
            QPushButton:hover { background: #1e4fd6; }

            /* Nút khi disabled: xám */
            QPushButton:disabled { background: #a3b4ec; }

            /* Tiêu đề section: đậm */
            #SectionTitle { font-weight: 700; margin-bottom: 4px; }

            /* Danh sách món: có viền, nền trắng */
            #DishList {
                border: 1px solid #e6e6e6;
                border-radius: 8px;
                background: #ffffff;
            }

            /* Mỗi item trong danh sách: có padding */
            QListWidget::item { padding: 8px; }

            /* Item được chọn: nền xanh nhạt */
            QListWidget::item:selected { background: #e8f0ff; color: #1e3a8a; }

            /* Ô hiển thị công thức: có viền, nền trắng */
            QTextEdit {
                border: 1px solid #e6e6e6;
                border-radius: 8px;
                background: #ffffff;
                padding: 8px;
            }

            /* Dòng bước đang đếm: nền vàng nhạt */
            StepRow[active="true"] {
                background: #fff9e6;
                border: 1px solid #ffe8a3;
                border-radius: 8px;
            }

            /* Nhãn đếm ngược: màu xám, căn phải */
            #CountdownLabel { color: #555; min-width: 56px; qproperty-alignment: 'AlignRight|AlignVCenter'; }
        """)

    def clear_steps(self):
        """
        Xóa tất cả các bước chế biến đang hiển thị
        """
        # Lặp qua tất cả các item trong layout
        while self.steps_layout.count():
            item = self.steps_layout.takeAt(0)  # Lấy item đầu tiên
            w = item.widget()  # Lấy widget từ item
            if w is not None:
                w.setParent(None)  # Xóa widget (sẽ bị Python tự động xóa)

    def load_steps(self, dish_name: str):
        """
        Tải và hiển thị các bước chế biến cho món được chọn

        Tham số:
            dish_name (str): Tên món ăn
        """
        self.clear_steps()  # Xóa các bước cũ trước

        # Lấy danh sách bước từ STEPS
        steps = STEPS.get(dish_name)

        # Nếu món không có trong STEPS, dùng bước mặc định
        if not steps:
            steps = [
                {"text": "Sơ chế nguyên liệu.", "seconds": None},
                {"text": "Nấu/chế biến theo món.", "seconds": None},
                {"text": "Nêm nếm vừa ăn và trình bày.", "seconds": None},
            ]

        # Tạo một StepRow cho mỗi bước
        for s in steps:
            row = StepRow(s["text"], s["seconds"], self.sound_mgr, self.steps_host)
            self.steps_layout.addWidget(row)  # Thêm vào layout

        # Thêm khoảng trống co giãn ở cuối (để các bước dính trên đầu)
        self.steps_layout.addStretch(1)

    def load_category(self, category_name: str) -> None:
        """
        Tải và hiển thị danh sách món trong danh mục được chọn

        Tham số:
            category_name (str): Tên danh mục (ví dụ: "Món khô")
        """
        # Cập nhật nhãn tiêu đề
        self.lbl_category.setText(f"Danh sách món: {category_name}")

        # Xóa danh sách cũ
        self.list_dishes.clear()

        # Lấy danh sách món từ RECIPES
        dishes = RECIPES.get(category_name, {})

        # Thêm từng món vào danh sách
        for dish_name in dishes.keys():
            self.list_dishes.addItem(dish_name)

        # Tự động chọn món đầu tiên (nếu có)
        if self.list_dishes.count() > 0:
            self.list_dishes.setCurrentRow(0)

    def show_recipe(self) -> None:
        """
        Hiển thị công thức (nguyên liệu) và các bước chế biến cho món được chọn
        Được gọi khi click nút "Xem công thức"
        """
        # Lấy tên danh mục hiện tại từ nhãn
        current_category = self.lbl_category.text().replace("Danh sách món: ", "")

        # Lấy item được chọn trong danh sách
        current_item = self.list_dishes.currentItem()

        # Kiểm tra có món được chọn không
        if not current_item:
            self.text_recipe.setPlainText("Vui lòng chọn một món.")
            self.clear_steps()  # Xóa các bước
            return

        # Lấy tên món
        dish_name = current_item.text()

        # Lấy danh sách nguyên liệu cơ bản (cho 1 người)
        base_ingredients = RECIPES.get(current_category, {}).get(dish_name, [])

        # Lấy số người từ spinner
        people = self.spin_people.value()

        # Tạo danh sách dòng text để hiển thị
        lines = [
            f"Món: {dish_name}",  # Dòng 1: Tên món
            f"Số người: {people}",  # Dòng 2: Số người
            "-" * 30,  # Dòng 3: Dòng gạch ngang
            "Nguyên liệu:"  # Dòng 4: Tiêu đề
        ]

        # Thêm từng nguyên liệu (đã nhân với số người)
        for ingredient_name, base_amount, unit in base_ingredients:
            total_amount = base_amount * people  # Tính tổng cho số người
            # Format đẹp và thêm vào danh sách
            lines.append(f"- {ingredient_name}: {format_quantity(total_amount, unit)}")

        # Hiển thị tất cả vào ô text
        self.text_recipe.setPlainText("\n".join(lines))

        # Tải và hiển thị các bước chế biến
        self.load_steps(dish_name)


# ============================================================================
# HÀM MAIN: ĐIỂM VÀO CỦA CHƯƠNG TRÌNH
# ============================================================================
def main():
    """
    Hàm chính: khởi động ứng dụng
    """
    # Tạo đối tượng QApplication (bắt buộc cho mọi ứng dụng PyQt)
    app = QApplication(sys.argv)

    # Tạo và hiển thị cửa sổ chính
    window = MainWindow()
    window.show()

    # Chạy vòng lặp sự kiện (event loop)
    # Ứng dụng sẽ chạy cho đến khi đóng cửa sổ
    sys.exit(app.exec())


# ============================================================================
# KHỞI CHẠY CHƯƠNG TRÌNH
# ============================================================================
if __name__ == "__main__":
    # Chỉ chạy hàm main() khi file này được chạy trực tiếp
    # (không chạy khi được import từ file khác)
    main()



