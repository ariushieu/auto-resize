"""
Window Manager Tool - Quản lý vị trí và kích thước các tab trình duyệt
Tự động lưu, restore và sắp xếp lại vị trí các cửa sổ
"""

import pygetwindow as gw
import json
import time
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import threading


@dataclass
class WindowInfo:
    """Thông tin về một cửa sổ"""
    title: str
    index: int  # Vị trí trong danh sách các tab cùng tên
    x: int
    y: int
    width: int
    height: int
    timestamp: float


class WindowManager:
    """Quản lý vị trí và kích thước các cửa sổ trình duyệt"""
    
    def __init__(self, config_file: str = "window_positions.json"):
        self.config_file = config_file
        self.windows_data: Dict[str, List[WindowInfo]] = {}
        self.monitoring = False
        self.monitor_thread = None
        self.load_config()
    
    def load_config(self):
        """Tải cấu hình từ file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for title, windows in data.items():
                        self.windows_data[title] = [
                            WindowInfo(**w) for w in windows
                        ]
                print(f"✓ Đã tải cấu hình từ {self.config_file}")
            except Exception as e:
                print(f"✗ Lỗi khi tải cấu hình: {e}")
                self.windows_data = {}
        else:
            print(f"ℹ Chưa có file cấu hình, sẽ tạo mới")
    
    def save_config(self):
        """Lưu cấu hình vào file"""
        try:
            data = {}
            for title, windows in self.windows_data.items():
                data[title] = [asdict(w) for w in windows]
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Đã lưu cấu hình vào {self.config_file}")
        except Exception as e:
            print(f"✗ Lỗi khi lưu cấu hình: {e}")
    
    def get_windows_by_title(self, title_pattern: str) -> List[gw.Win32Window]:
        """Lấy tất cả các cửa sổ có tiêu đề chứa pattern"""
        all_windows = gw.getAllWindows()
        matching_windows = [
            w for w in all_windows 
            if title_pattern.lower() in w.title.lower() and w.visible
        ]
        return matching_windows
    
    def capture_windows(self, title_pattern: str):
        """
        Capture vị trí và kích thước của tất cả các tab có tiêu đề chứa pattern
        """
        windows = self.get_windows_by_title(title_pattern)
        
        if not windows:
            print(f"✗ Không tìm thấy cửa sổ nào với tiêu đề chứa '{title_pattern}'")
            return
        
        # Sắp xếp theo vị trí x, y để đảm bảo thứ tự nhất quán
        windows.sort(key=lambda w: (w.left, w.top))
        
        window_infos = []
        for idx, window in enumerate(windows):
            info = WindowInfo(
                title=title_pattern,
                index=idx,
                x=window.left,
                y=window.top,
                width=window.width,
                height=window.height,
                timestamp=time.time()
            )
            window_infos.append(info)
            print(f"✓ Đã capture tab #{idx}: {window.title[:50]}... tại ({info.x}, {info.y}) - {info.width}x{info.height}")
        
        self.windows_data[title_pattern] = window_infos
        self.save_config()
        print(f"\n✓ Đã capture {len(window_infos)} tab với tiêu đề '{title_pattern}'")
    
    def restore_windows(self, title_pattern: str):
        """
        Restore vị trí và kích thước của các tab
        """
        if title_pattern not in self.windows_data:
            print(f"✗ Không có dữ liệu đã lưu cho '{title_pattern}'")
            return
        
        saved_windows = self.windows_data[title_pattern]
        current_windows = self.get_windows_by_title(title_pattern)
        
        if not current_windows:
            print(f"✗ Không tìm thấy cửa sổ nào với tiêu đề chứa '{title_pattern}'")
            return
        
        # Sắp xếp theo vị trí hiện tại
        current_windows.sort(key=lambda w: (w.left, w.top))
        
        print(f"\nRestoring {len(current_windows)} tab(s)...")
        
        for idx, window in enumerate(current_windows):
            if idx < len(saved_windows):
                saved_info = saved_windows[idx]
                try:
                    # Restore vị trí và kích thước
                    window.moveTo(saved_info.x, saved_info.y)
                    window.resizeTo(saved_info.width, saved_info.height)
                    print(f"✓ Đã restore tab #{idx} về ({saved_info.x}, {saved_info.y}) - {saved_info.width}x{saved_info.height}")
                except Exception as e:
                    print(f"✗ Lỗi khi restore tab #{idx}: {e}")
            else:
                print(f"⚠ Tab #{idx} không có dữ liệu đã lưu")
        
        print(f"\n✓ Hoàn tất restore cho '{title_pattern}'")
    
    def rearrange_windows(self, title_pattern: str):
        """
        Sắp xếp lại các tab khi có tab bị đóng
        Tự động lấp đầy vị trí trống
        """
        if title_pattern not in self.windows_data:
            print(f"✗ Không có dữ liệu đã lưu cho '{title_pattern}'")
            return
        
        saved_windows = self.windows_data[title_pattern]
        current_windows = self.get_windows_by_title(title_pattern)
        
        if not current_windows:
            print(f"✗ Không tìm thấy cửa sổ nào với tiêu đề chứa '{title_pattern}'")
            return
        
        # Sắp xếp theo vị trí hiện tại
        current_windows.sort(key=lambda w: (w.left, w.top))
        
        print(f"\nSắp xếp lại {len(current_windows)} tab(s) vào {len(saved_windows)} vị trí đã lưu...")
        
        # Ánh xạ các tab hiện tại vào các vị trí đã lưu
        for idx, window in enumerate(current_windows):
            if idx < len(saved_windows):
                saved_info = saved_windows[idx]
                try:
                    window.moveTo(saved_info.x, saved_info.y)
                    window.resizeTo(saved_info.width, saved_info.height)
                    print(f"✓ Đã di chuyển tab #{idx} về vị trí đã lưu #{idx}: ({saved_info.x}, {saved_info.y})")
                except Exception as e:
                    print(f"✗ Lỗi khi di chuyển tab #{idx}: {e}")
        
        print(f"\n✓ Hoàn tất sắp xếp lại cho '{title_pattern}'")
    
    def monitor_windows(self, title_pattern: str, interval: float = 2.0, tolerance: int = 10):
        """
        Giám sát và tự động sắp xếp lại các tab
        Giám sát cả số lượng, vị trí và kích thước
        
        Args:
            title_pattern: Pattern tên tab cần giám sát
            interval: Khoảng thời gian giữa các lần kiểm tra (giây)
            tolerance: Sai số cho phép cho vị trí/kích thước (pixel)
        """
        print(f"\n🔍 Bắt đầu giám sát tab '{title_pattern}' (mỗi {interval}s)")
        print(f"📏 Sai số cho phép: ±{tolerance}px")
        print("Nhấn Ctrl+C để dừng giám sát\n")
        
        last_count = 0
        last_positions = []  # Lưu vị trí lần kiểm tra trước
        
        while self.monitoring:
            try:
                current_windows = self.get_windows_by_title(title_pattern)
                current_count = len(current_windows)
                
                # Lấy vị trí hiện tại của các tab
                current_windows.sort(key=lambda w: (w.left, w.top))
                current_positions = [
                    (w.left, w.top, w.width, w.height) 
                    for w in current_windows
                ]
                
                needs_rearrange = False
                reason = ""
                
                # Kiểm tra số lượng tab thay đổi
                if current_count != last_count and current_count > 0:
                    needs_rearrange = True
                    reason = f"Số lượng tab: {last_count} → {current_count}"
                
                # Kiểm tra vị trí/kích thước thay đổi (chỉ khi có dữ liệu đã lưu)
                elif current_count > 0 and title_pattern in self.windows_data:
                    saved_windows = self.windows_data[title_pattern]
                    
                    for idx, (x, y, w, h) in enumerate(current_positions):
                        if idx < len(saved_windows):
                            saved = saved_windows[idx]
                            
                            # Kiểm tra sai lệch vị trí
                            x_diff = abs(x - saved.x)
                            y_diff = abs(y - saved.y)
                            w_diff = abs(w - saved.width)
                            h_diff = abs(h - saved.height)
                            
                            if x_diff > tolerance or y_diff > tolerance or \
                               w_diff > tolerance or h_diff > tolerance:
                                needs_rearrange = True
                                reason = f"Tab #{idx} bị di chuyển/resize: ({x},{y}) {w}x{h} → ({saved.x},{saved.y}) {saved.width}x{saved.height}"
                                break
                
                # Thực hiện sắp xếp lại nếu cần
                if needs_rearrange:
                    print(f"\n⚡ Phát hiện thay đổi: {reason}")
                    self.rearrange_windows(title_pattern)
                    last_count = current_count
                    last_positions = current_positions
                
                time.sleep(interval)
            except Exception as e:
                print(f"✗ Lỗi trong quá trình giám sát: {e}")
                time.sleep(interval)
    
    def start_monitoring(self, title_pattern: str, interval: float = 2.0, tolerance: int = 10):
        """
        Bắt đầu giám sát trong thread riêng
        
        Args:
            title_pattern: Pattern tên tab cần giám sát
            interval: Khoảng thời gian giữa các lần kiểm tra (giây)
            tolerance: Sai số cho phép cho vị trí/kích thước (pixel)
        """
        if self.monitoring:
            print("⚠ Đang giám sát rồi!")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self.monitor_windows,
            args=(title_pattern, interval, tolerance),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Dừng giám sát"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            print("\n✓ Đã dừng giám sát")
    
    def list_saved_patterns(self):
        """Liệt kê tất cả các pattern đã lưu"""
        if not self.windows_data:
            print("ℹ Chưa có dữ liệu nào được lưu")
            return
        
        print("\n📋 Danh sách các pattern đã lưu:")
        print("=" * 60)
        for title, windows in self.windows_data.items():
            print(f"\n'{title}': {len(windows)} tab(s)")
            for idx, w in enumerate(windows):
                print(f"  #{idx}: ({w.x}, {w.y}) - {w.width}x{w.height}")
        print("=" * 60)


def main():
    """Hàm main để chạy tool"""
    import sys
    
    manager = WindowManager()
    
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║          Window Manager - Quản lý vị trí tab trình duyệt     ║
╚══════════════════════════════════════════════════════════════╝

Cách sử dụng:
  python window_manager.py capture <tên_tab>      - Capture vị trí các tab
  python window_manager.py restore <tên_tab>      - Restore vị trí đã lưu
  python window_manager.py rearrange <tên_tab>    - Sắp xếp lại khi có tab đóng
  python window_manager.py monitor <tên_tab>      - Tự động giám sát và sắp xếp
  python window_manager.py list                   - Liệt kê các pattern đã lưu

Ví dụ:
  python window_manager.py capture "MetaBomb 2.0"
  python window_manager.py restore "MetaBomb 2.0"
  python window_manager.py monitor "MetaBomb 2.0"
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        manager.list_saved_patterns()
    elif command in ["capture", "restore", "rearrange", "monitor"]:
        if len(sys.argv) < 3:
            print("✗ Vui lòng cung cấp tên tab")
            return
        
        title_pattern = sys.argv[2]
        
        if command == "capture":
            manager.capture_windows(title_pattern)
        elif command == "restore":
            manager.restore_windows(title_pattern)
        elif command == "rearrange":
            manager.rearrange_windows(title_pattern)
        elif command == "monitor":
            try:
                manager.start_monitoring(title_pattern)
                # Giữ chương trình chạy
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_monitoring()
                print("\n👋 Tạm biệt!")
    else:
        print(f"✗ Lệnh không hợp lệ: {command}")


if __name__ == "__main__":
    main()
