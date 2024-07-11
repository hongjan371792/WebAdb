import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
from PIL import Image, ImageTk
import io
import threading
import time

class AdbToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB Tool")
        
        self.create_widgets()
        self.refresh_device_list()  # 初始化時更新裝置列表
        
        # 開始自動截圖
        self.auto_refresh_screen()

    def create_widgets(self):
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # 左側框架（裝置信息和操作）
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 下拉選單
        self.device_selector = ttk.Combobox(left_frame, width=30, state="readonly")
        self.device_selector.grid(row=0, column=0, padx=10, pady=5, sticky='w')  # 調整下拉選單上下間距
        self.device_selector.bind("<<ComboboxSelected>>", self.update_info_on_select)
        
        # 刷新裝置列表按鈕
        self.refresh_button = tk.Button(left_frame, text="重新載入裝置列表", command=self.refresh_device_list)
        self.refresh_button.grid(row=0, column=1, padx=10, pady=5, sticky='w')  # 調整刷新按鈕的上下間距

        # 裝置訊息顯示區域
        self.info_text = tk.Text(left_frame, width=50, height=30, wrap=tk.WORD, font=("Arial", 10))
        self.info_text.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')  # 調整訊息顯示區域的位置和間距

        # 刷新按鈕
        self.screenshot_button = tk.Button(left_frame, text="重新載入裝置訊息", command=self.update_info_on_select)
        self.screenshot_button.grid(row=2, column=0, padx=10, pady=5, sticky='w')  # 調整截圖按鈕的上下間距

        # 右側框架（裝置畫面）
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 裝置畫面顯示區域
        self.screen_canvas = tk.Canvas(right_frame, width=480, height=800, bg='white')
        self.screen_canvas.pack(padx=10, pady=10)  # 調整畫面顯示區域的位置和間距

    def refresh_device_list(self, event=None):
        try:
            # 使用adb命令列出連接的所有裝置
            devices_output = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            devices_list = devices_output.stdout.strip().split('\n')[1:]  # 第一行是表頭，跳過
            
            # 提取裝置序列號並更新下拉選單
            self.devices = []
            for device in devices_list:
                if 'device' in device:
                    self.devices.append(device.split('\t')[0])
            
            self.device_selector['values'] = self.devices
            if self.devices:
                self.device_selector.current(0)  # 選擇第一個裝置
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while refreshing device list: {str(e)}")

    def load_screen(self):
        selected_device = self.device_selector.get()
        if not selected_device:
            messagebox.showwarning("Warning", "Please select a device first.")
            return

        try:
            # 截取裝置螢幕畫面並顯示
            screenshot_process = subprocess.Popen(['adb', '-s', selected_device, 'exec-out', 'screencap', '-p'],
                                                  stdout=subprocess.PIPE)
            screenshot_bytes = screenshot_process.stdout.read()
            screenshot_process.stdout.close()
            screenshot_image = Image.open(io.BytesIO(screenshot_bytes))
            
            # 調整大小以適應Canvas
            width, height = screenshot_image.size
            ratio = min(1.0, 480 / width, 800 / height)  # 確保在480x800內顯示
            resized_image = screenshot_image.resize((int(width * ratio), int(height * ratio)), Image.LANCZOS)
            
            # 將圖片轉換為Tkinter格式並顯示在Canvas上
            self.screen_image = ImageTk.PhotoImage(resized_image)
            self.screen_canvas.create_image(0, 0, anchor='nw', image=self.screen_image)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading screen: {str(e)}")

    def update_info_on_select(self, event=None):
        selected_device = self.device_selector.get()
        if not selected_device:
            return
        
        try:
            # 獲取裝置信息
            device_model = self.adb_command(['-s', selected_device, 'shell', 'getprop', 'ro.product.model'])
            android_version = self.adb_command(['-s', selected_device, 'shell', 'getprop', 'ro.build.version.release'])
            imei = self.get_imei(selected_device)
            sim_operator = self.get_sim_operator(selected_device)
            boot_time = self.get_boot_time(selected_device)
            bluetooth_address = self.get_bluetooth_address(selected_device)
            wifi_mac = self.get_wifi_mac(selected_device)
            baseband_version = self.get_baseband_version(selected_device)
            last_google_play_update = self.get_last_google_play_update(selected_device)
            
            # 顯示裝置信息
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert(tk.END, f"裝置型號: {device_model}\n")
            self.info_text.insert(tk.END, f"安卓版本: {android_version}\n")
            self.info_text.insert(tk.END, f"IMEI: {imei}\n")
            self.info_text.insert(tk.END, f"SIM 供應商: {sim_operator}\n")
            self.info_text.insert(tk.END, f"開機時間: {boot_time}\n")
            self.info_text.insert(tk.END, f"藍牙位置: {bluetooth_address}\n")
            self.info_text.insert(tk.END, f"Wi-Fi MAC地址: {wifi_mac}\n")
            self.info_text.insert(tk.END, f"基頻版本: {baseband_version}\n")
            self.info_text.insert(tk.END, f"最後一次Google Play系統更新: {last_google_play_update}\n")
            self.info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while fetching device info: {str(e)}")

    def adb_command(self, command):
        adb_path = 'adb'
        full_command = [adb_path] + command
        result = subprocess.run(full_command, capture_output=True, text=True)
        return result.stdout.strip()

    def take_screenshot(self):
        selected_device = self.device_selector.get()
        if not selected_device:
            messagebox.showwarning("Warning", "Please select a device first.")
            return

        try:
            # 截取裝置螢幕畫面並保存截圖
            screenshot_process = subprocess.Popen(['adb', '-s', selected_device, 'exec-out', 'screencap', '-p'],
                                                  stdout=subprocess.PIPE)
            screenshot_bytes = screenshot_process.stdout.read()
            screenshot_process.stdout.close()
            screenshot_image = Image.open(io.BytesIO(screenshot_bytes))
            
            # 儲存截圖文件
            screenshot_filename = f"screenshot_{int(time.time())}.png"
            screenshot_image.save(screenshot_filename)
            messagebox.showinfo("Screenshot", f"Screenshot saved as {screenshot_filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while taking screenshot: {str(e)}")

    def auto_refresh_screen(self):
        # 定義自動更新裝置畫面的函數
        def refresh():
            while True:
                selected_device = self.device_selector.get()
                if selected_device:
                    self.load_screen()
                    self.update_info_on_select()
                time.sleep()  # 每秒更新一次

        # 創建並啟動自動更新線程
        refresh_thread = threading.Thread(target=refresh)
        refresh_thread.daemon = True  # 設置為守護線程，隨主程序退出而退出
        refresh_thread.start()

    def get_imei(self, device):
        try:
            # 使用 adb shell 命令獲取 IMEI
            imei_output = self.adb_command(['-s', device, 'shell', 'service', 'call', 'iphonesubinfo', '1'])
            imei = imei_output.split("'")[1]
            return imei.strip()
        
        except Exception as e:
            # 如果直接命令失敗，嘗試另一種方法
            try:
                imei_output = self.adb_command(['-s', device, 'shell', 'dumpsys', 'iphonesubinfo'])
                imei = imei_output.split('Device ID')[1].split(':')[1].strip()
                return imei
            
            except Exception as e:
                return "N/A"

    def get_boot_time(self, device):
        try:
            # 使用 adb shell 命令獲取開機時間
            boot_time_output = self.adb_command(['-s', device, 'shell', 'uptime'])
            boot_time = boot_time_output.split(',')[0]
            return boot_time.strip()
        
        except Exception as e:
            return "N/A"

    def get_bluetooth_address(self, device):
        try:
            # 使用 adb shell 命令獲取藍芽地址
            bluetooth_output = self.adb_command(['-s', device, 'shell', 'settings', 'get', 'secure', 'bluetooth_address'])
            bluetooth_address = bluetooth_output.strip()
            return bluetooth_address
        
        except Exception as e:
            return "N/A"

    def get_wifi_mac(self, device):
        try:
            # 使用 adb shell 命令獲取 Wi-Fi MAC 地址
            wifi_mac_output = self.adb_command(['-s', device, 'shell', 'cat', '/sys/class/net/wlan0/address'])
            wifi_mac = wifi_mac_output.strip()
            return wifi_mac
        
        except Exception as e:
            return "N/A"

    def get_sim_operator(self, device):
        try:
            # 使用 adb shell 命令獲取 SIM 卡服務供應商
            sim_operator_output = self.adb_command(['-s', device, 'shell', 'service', 'call', 'iphonesubinfo', '7'])
            sim_operator = sim_operator_output.split("'")[1]
            return sim_operator.strip()
        
        except Exception as e:
            return "N/A"

    def get_baseband_version(self, device):
        try:
            # 使用 adb shell 命令獲取基頻版本
            baseband_output = self.adb_command(['-s', device, 'shell', 'getprop', 'gsm.version.baseband'])
            baseband_version = baseband_output.strip()
            return baseband_version
        
        except Exception as e:
            return "N/A"

    def get_last_google_play_update(self, device):
        try:
            # 使用 adb shell 命令獲取 Google Play 最後更新日期
            last_update_output = self.adb_command(['-s', device, 'shell', 'dumpsys', 'package', 'com.android.vending'])
            last_update_index = last_update_output.find("lastUpdateTime")
            last_update = last_update_output[last_update_index+15:last_update_index+35].strip()
            return last_update
        
        except Exception as e:
            return "N/A"

if __name__ == "__main__":
    root = tk.Tk()
    app = AdbToolApp(root)
    root.mainloop()
