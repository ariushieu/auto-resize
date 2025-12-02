"""
Modern GUI for Window Manager using CustomTkinter
"""

import customtkinter as ctk
import threading
from window_manager import WindowManager
import sys
from PIL import Image
import os

# Cấu hình theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class WindowManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Window Manager Pro")
        self.geometry("900x700")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.manager = WindowManager()
        self.monitoring = False

        self.setup_ui()
        self.redirect_output()

    def setup_ui(self):
        # ============ Sidebar (Left) ============
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Window\nManager", 
                                     font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text="v2.1 Pro", 
                                        font=ctk.CTkFont(size=12), text_color="gray")
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Sidebar Buttons
        self.btn_capture = ctk.CTkButton(self.sidebar_frame, text="Capture Vị Trí", 
                                       command=self.capture_windows,
                                       font=ctk.CTkFont(weight="bold"))
        self.btn_capture.grid(row=2, column=0, padx=20, pady=10)

        self.btn_restore = ctk.CTkButton(self.sidebar_frame, text="Restore Vị Trí", 
                                       command=self.restore_windows,
                                       fg_color="transparent", border_width=2, 
                                       text_color=("gray10", "#DCE4EE"))
        self.btn_restore.grid(row=3, column=0, padx=20, pady=10)

        self.btn_rearrange = ctk.CTkButton(self.sidebar_frame, text="Sắp Xếp Lại", 
                                         command=self.rearrange_windows,
                                         fg_color="transparent", border_width=2, 
                                         text_color=("gray10", "#DCE4EE"))
        self.btn_rearrange.grid(row=4, column=0, padx=20, pady=10)
        
        self.btn_list = ctk.CTkButton(self.sidebar_frame, text="Xem Danh Sách", 
                                    command=self.list_patterns,
                                    fg_color="transparent", text_color="gray")
        self.btn_list.grid(row=6, column=0, padx=20, pady=20)

        # ============ Main Area (Right) ============
        
        # 1. Top Panel: Settings
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Tab Name Input
        self.entry_label = ctk.CTkLabel(self.settings_frame, text="Tên Tab Cần Quản Lý:", 
                                      font=ctk.CTkFont(size=14, weight="bold"))
        self.entry_label.pack(anchor="w", pady=(0, 5))
        
        self.title_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="Ví dụ: MetaBomb 2.0", 
                                      height=40, font=ctk.CTkFont(size=14))
        self.title_entry.pack(fill="x", pady=(0, 20))
        self.title_entry.insert(0, "MetaBomb 2.0")

        # Tolerance Slider
        self.tol_label_title = ctk.CTkLabel(self.settings_frame, text="Sai số cho phép (Tolerance):", 
                                          font=ctk.CTkFont(size=14, weight="bold"))
        self.tol_label_title.pack(anchor="w", pady=(0, 5))
        
        self.tol_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.tol_frame.pack(fill="x")
        
        self.tolerance_slider = ctk.CTkSlider(self.tol_frame, from_=0, to=50, number_of_steps=50, 
                                            command=self.update_tolerance_label)
        self.tolerance_slider.pack(side="left", fill="x", expand=True, padx=(0, 20))
        self.tolerance_slider.set(10)
        
        self.tolerance_label = ctk.CTkLabel(self.tol_frame, text="10 px", 
                                          font=ctk.CTkFont(size=14, weight="bold"),
                                          text_color="#3B8ED0")
        self.tolerance_label.pack(side="right")

        # 2. Monitoring Action Area (Big Button)
        self.monitor_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.monitor_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="ew")
        
        self.btn_monitor = ctk.CTkButton(self.monitor_frame, text="▶  BẮT ĐẦU GIÁM SÁT", 
                                       command=self.toggle_monitoring,
                                       height=60, font=ctk.CTkFont(size=16, weight="bold"),
                                       fg_color="#2CC985", hover_color="#229E68") # Green color
        self.btn_monitor.pack(fill="x")

        # 3. Log Area
        self.log_label = ctk.CTkLabel(self, text="Nhật Ký Hoạt Động:", font=ctk.CTkFont(weight="bold"))
        self.log_label.grid(row=2, column=1, padx=20, sticky="w")

        self.log_textbox = ctk.CTkTextbox(self, width=250, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=3, column=1, padx=20, pady=(5, 20), sticky="nsew")

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Sẵn sàng", anchor="w", padx=20, height=30, 
                                     fg_color=("gray90", "gray20"))
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky="ew")

        # Initial Log
        self.log("Hệ thống đã sẵn sàng.")

    def update_tolerance_label(self, value):
        self.tolerance_label.configure(text=f"{int(value)} px")

    def redirect_output(self):
        class OutputRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget
            def write(self, string):
                self.text_widget.insert("end", string)
                self.text_widget.see("end")
            def flush(self): pass
        sys.stdout = OutputRedirector(self.log_textbox)

    def log(self, message):
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def get_title(self):
        title = self.title_entry.get().strip()
        if not title:
            # CTk doesn't have simple messagebox, using print for now or fallback to tk
            self.log("⚠️ Vui lòng nhập tên tab!")
            return None
        return title

    def capture_windows(self):
        title = self.get_title()
        if not title: return
        self.status_bar.configure(text=f"Đang capture '{title}'...", text_color="#3B8ED0")
        threading.Thread(target=lambda: self._run_task(self.manager.capture_windows, title), daemon=True).start()

    def restore_windows(self):
        title = self.get_title()
        if not title: return
        self.status_bar.configure(text=f"Đang restore '{title}'...", text_color="#3B8ED0")
        threading.Thread(target=lambda: self._run_task(self.manager.restore_windows, title), daemon=True).start()

    def rearrange_windows(self):
        title = self.get_title()
        if not title: return
        self.status_bar.configure(text=f"Đang sắp xếp '{title}'...", text_color="#3B8ED0")
        threading.Thread(target=lambda: self._run_task(self.manager.rearrange_windows, title), daemon=True).start()

    def list_patterns(self):
        self.manager.list_saved_patterns()

    def _run_task(self, func, *args):
        func(*args)
        self.status_bar.configure(text="Sẵn sàng", text_color=("black", "white"))

    def toggle_monitoring(self):
        title = self.get_title()
        if not title: return

        if not self.monitoring:
            self.monitoring = True
            self.btn_monitor.configure(text="⏸  DỪNG GIÁM SÁT", fg_color="#E04F5F", hover_color="#B03E4B")
            self.status_bar.configure(text=f"Đang giám sát '{title}'...", text_color="#2CC985")
            
            tol = int(self.tolerance_slider.get())
            self.manager.start_monitoring(title, interval=2.0, tolerance=tol)
        else:
            self.monitoring = False
            self.btn_monitor.configure(text="▶  BẮT ĐẦU GIÁM SÁT", fg_color="#2CC985", hover_color="#229E68")
            self.status_bar.configure(text="Sẵn sàng", text_color=("black", "white"))
            self.manager.stop_monitoring()

    def on_closing(self):
        if self.monitoring:
            self.manager.stop_monitoring()
        self.destroy()

if __name__ == "__main__":
    app = WindowManagerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
