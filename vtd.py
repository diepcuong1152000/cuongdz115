# -*- coding: utf-8 -*-
import requests
import time
import os
import uuid
import random
import hashlib
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
from colorama import Fore, init, Style
import platform
import subprocess

init(autoreset=True)

# Danh sách User-Agents được thay thế từ yêu cầu của bạn
USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",

    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:113.0) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",

    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:114.0) Gecko/20100101 Firefox/114.0",

    # Mac Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",

    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.7 Mobile/15E148 Safari/604.1",

    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.5 Mobile/15E148 Safari/604.1",

    # Android Chrome
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",

    # Android khác
    "Mozilla/5.0 (Linux; Android 12; Xiaomi 12 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Vivo V20) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Oppo Reno8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",

    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.51",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 EdgiOS/115.0.1901.183",
]

ascii_art = """
        
 ▌ ▐·    ▄▄▄▄▄    ·▄▄▄▄  
▪█·█▌    •██      ██▪ ██ 
▐█▐█•     ▐█.▪    ▐█· ▐█▌
 ███      ▐█▌·    ██. ██ 
. ▀       ▀▀▀     ▀▀▀▀▀• 
   𝐀𝐮𝐭𝐨 Đ𝐚̣̆𝐭 𝐂𝐮̛𝐨̛̣𝐜 𝐕𝐓𝐃
                                                                                   
                                             """

# màu
colors = [
    Fore.RED,
    Fore.YELLOW,
    Fore.GREEN,
    Fore.CYAN,
    Fore.BLUE,
    Fore.MAGENTA
]

# load ASCII 
def display_ascii_art():
    lines = ascii_art.strip().split('\n')
    for i in range(len(lines)):
        os.system('cls' if os.name == 'nt' else 'clear')
        current_lines = lines[:i + 1]
        for line_idx, line in enumerate(current_lines):
            colored_line = ''
            for j, char in enumerate(line):
                color_idx = (j + line_idx) % len(colors)
                colored_line += colors[color_idx] + char
            print(colored_line + Style.RESET_ALL)
        time.sleep(0.1)
    os.system('cls' if os.name == 'nt' else 'clear')
    for line in lines:
        colored_line = ''
        for j, char in enumerate(line):
            color_idx = j % len(colors)
            colored_line += colors[color_idx] + char
        print(colored_line + Style.RESET_ALL)
    print()

# Bản đồ tên phòng
room_names_map = {
    "1": "Bậc Thầy Tấn Công",
    "2": "Quyền Sắt",
    "3": "Thợ Lặn Sâu",
    "4": "Cơn Lốc Sân Cỏ",
    "5": "Hiệp Sĩ Phi Nhanh",
    "6": "Vua Home Run",
}

SECRET = "MY_SECRET_SALT"
GLOBAL_KEY_MODE = None

def get_device_id(mode="mac"):
    try:
        android_id = os.popen("settings get secure android_id").read().strip()
        model = os.popen("getprop ro.product.model").read().strip()
        brand = os.popen("getprop ro.product.brand").read().strip()
        serial = os.popen("getprop ro.serialno").read().strip()

        if android_id and model and brand:
            raw = f"{android_id}-{brand}-{model}-{serial}"
        else:
            raise Exception("Not Android")
    except:
        if mode == "mac":
            raw = str(uuid.getnode())
        elif mode == "cpu":
            raw = f"{platform.processor()}-{platform.machine()}"
        elif mode == "disk":
            try:
                if platform.system() == "Windows":
                    disk_serial = subprocess.check_output(
                        "wmic diskdrive get SerialNumber", shell=True
                    ).decode(errors="ignore").split("\n")[1].strip()
                else:
                    disk_serial = subprocess.check_output(
                        "udevadm info --query=property --name=/dev/sda | grep ID_SERIAL",
                        shell=True
                    ).decode(errors="ignore").strip()
            except:
                disk_serial = "NOSERIAL"
            raw = disk_serial
        else:
            raw = f"{platform.node()}-{platform.system()}-{platform.release()}"

    device_id = "DEVICE-" + hashlib.md5(raw.encode()).hexdigest()[:25].upper()
    print(Fore.BLUE + "📌 Device ID:" + Fore.YELLOW + f" {device_id}")
    return device_id

def make_free_key(user_id):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = today + SECRET + user_id
    return hashlib.md5(raw.encode()).hexdigest()[:10].upper()

def thoi_gian_con_lai_trong_ngay():
    now = datetime.utcnow() + timedelta(hours=7)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delta = tomorrow - now
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return hours, minutes

def load_vip_key(device_id):
    try:
        url_key = "https://raw.githubusercontent.com/Cuongdz2828/pt/main/test/a.txt"
        r = requests.get(url_key, timeout=8)
        r.raise_for_status()
        ds_key_raw = r.text.strip().splitlines()
        dev_local = device_id.replace("DEVICE-", "").strip().upper()
        for dong in ds_key_raw:
            parts = [p.strip() for p in dong.split("|")]
            if len(parts) >= 4:
                device, key, _, ngay_hh = parts[:4]
                dev_file = device.replace("DEVICE-", "").strip().upper()
                if dev_file == dev_local:
                    return key, ngay_hh
    except Exception:
        pass
    return None, None

def kiem_tra_quyen_truy_cap(device_id):
    global GLOBAL_KEY_MODE
    print(Fore.CYAN + "\n" + "=" * 48)
    print(Fore.YELLOW + "   CHỌN LOẠI KEY")
    print(Fore.CYAN + "=" * 48)
    print(Fore.GREEN + "1. Key Free (vượt link)")
    print(Fore.MAGENTA + "2. Key VIP (ib Cường để mua)")
    print(Fore.CYAN + "=" * 48)
    choice = input(Fore.YELLOW + "Chọn (1-2): " + Fore.WHITE).strip()

    if choice == "1":
        GLOBAL_KEY_MODE = "FREE"
        print(Fore.CYAN + "\nBạn đã chọn Key Free")
        print(Fore.YELLOW + "👉 Vui lòng mở link rút gọn 4m để lấy key:")

        free_links = [
            "https://link4m.com/Bhdv5",
            "https://link4m.com/LvWUEq5F",
            "https://link4m.com/Bhbv5",
            "https://link4m.com/LvWUEq5F",
        ]
        random_link = random.choice(free_links)
        print(Fore.GREEN + "   " + random_link)

        print(Fore.YELLOW + "Sau khi vượt qua, để thấy User ID + Key Free")

        user_id = input(Fore.YELLOW + "👉 Nhập User ID (copy từ web): " + Fore.WHITE).strip()
        free_key = make_free_key(user_id)

        while True:
            key_nhap = input(Fore.YELLOW + "Nhập Key Free: " + Fore.WHITE).strip()
            if key_nhap == free_key:
                h, m = thoi_gian_con_lai_trong_ngay()
                print(Fore.GREEN + f"✅ Dùng Key Free thành công! Còn hiệu lực {h}h {m}m\n")
                break
            else:
                print(Fore.RED + "❌ Key Free sai, thử lại...")

    elif choice == "2":
        GLOBAL_KEY_MODE = "VIP"
        print(Fore.CYAN + "\nBạn đã chọn Key VIP")
        vip_key, ngay_hh = load_vip_key(device_id)
        if not vip_key:
            print(Fore.RED + "❌ Không tìm thấy Key VIP ")
            raise SystemExit(1)
        print(Fore.YELLOW + f"⭐ Key VIP của bạn: {Fore.MAGENTA}{vip_key} (hạn {ngay_hh})")
        while True:
            key_nhap = input(Fore.YELLOW + "Nhập Key VIP: " + Fore.WHITE).strip()
            if key_nhap == vip_key:
                try:
                    ngay_hh_dt = datetime.strptime(ngay_hh, "%d/%m/%Y").date()
                    today_local = (datetime.utcnow() + timedelta(hours=7)).date()
                    if today_local <= ngay_hh_dt:
                        print(Fore.GREEN + "✅ Key VIP còn hiệu lực!\n")
                        break
                    else:
                        print(Fore.RED + "❌ Key VIP đã hết hạn!")
                except Exception:
                    print(Fore.RED + "❌ Lỗi định dạng ngày trong VIP key!")
            else:
                print(Fore.RED + "❌ Key VIP sai, thử lại...")
    else:
        print(Fore.RED + "❌ Lựa chọn không hợp lệ!")
        raise SystemExit(1)

def fetch_data(url, headers):
    headers["User-Agent"] = random.choice(USER_AGENTS)  # Thêm User-Agent ngẫu nhiên
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(Fore.RED + f"⚠️ API trả về mã {r.status_code}: {r.text}")
    except Exception as e:
        print(Fore.RED + f"⚠️ Lỗi fetch_data: {e}")
    return None

def analyze_data(headers, asset_mode="BUILD"):
    url_recent_10 = f"https://api.sprintrun.win/sprint/recent_10_issues?asset={asset_mode}"
    url_recent_100 = f"https://api.sprintrun.win/sprint/recent_100_issues?asset={asset_mode}"
    data_10 = fetch_data(url_recent_10, headers)
    data_100 = fetch_data(url_recent_100, headers)

    if not data_10 or not data_100:
        return None, [], None, None, {}, [], {}

    issues_10 = []
    if isinstance(data_10, dict):
        if "data" in data_10 and isinstance(data_10["data"], dict):
            issues_10 = (
                data_10["data"].get("recent_10")
                or data_10["data"].get("issues")
                or data_10["data"].get("list")
                or []
            )
        else:
            issues_10 = (
                data_10.get("data")
                or data_10.get("issues")
                or []
            )
    elif isinstance(data_10, list):
        issues_10 = data_10

    if not isinstance(issues_10, list) or not issues_10:
        print(Fore.RED + "❌ API không trả về dữ liệu 10 ván hoặc dữ liệu không hợp lệ.")
        return None, [], None, None, {}, [], {}

    first_issue = issues_10[0]
    current_issue = first_issue.get("issue_id")
    champion_id = None
    if isinstance(first_issue.get("result"), list) and first_issue["result"]:
        champion_id = first_issue["result"][0]
    killed_room_id = str(champion_id) if champion_id is not None else None
    killed_room_name = room_names_map.get(killed_room_id, f"Phòng #{killed_room_id}") if killed_room_id else "N/A"

    stats_100 = {}
    if isinstance(data_100, dict):
        if "data" in data_100 and isinstance(data_100["data"], dict):
            stats_100 = (
                data_100["data"].get("athlete_2_win_times")
                or data_100["data"].get("room_id_2_killed_times")
                or data_100["data"].get("stats")
                or {}
            )
        else:
            stats_100 = (
                data_100.get("athlete_2_win_times")
                or data_100.get("room_id_2_killed_times")
                or data_100.get("stats")
                or {}
            )
        if not isinstance(stats_100, dict):
            stats_100 = {}

    rates_100 = {}
    for rid in room_names_map.keys():
        try:
            rates_100[rid] = int(stats_100.get(str(rid), 0))
        except Exception:
            rates_100[rid] = 0

    sorted_rooms_win = sorted(rates_100.items(), key=lambda x: x[1], reverse=True)
    sorted_rooms_not_win = sorted(rates_100.items(), key=lambda x: x[1])

    return current_issue, [sorted_rooms_win, sorted_rooms_not_win], killed_room_id, killed_room_name, rates_100, issues_10, stats_100

def place_bet(headers, bet_group, asset_type, athlete_id, issue_id, bet_amount=1.0):
    headers["User-Agent"] = random.choice(USER_AGENTS)  # Thêm User-Agent ngẫu nhiên
    url = "https://api.sprintrun.win/sprint/bet"
    payload = {
        "issue_id": str(issue_id),
        "bet_group": bet_group,
        "asset_type": asset_type,
        "athlete_id": int(athlete_id),
        "bet_amount": float(bet_amount)
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        data = r.json()
        if data.get("code") in (0, 200):
            # Thay đổi ở đây: Sử dụng tên từ room_names_map thay vì athlete_id
            athlete_name = room_names_map.get(str(athlete_id), f"Phòng #{athlete_id}")
            print(Fore.GREEN + f"✅ Đặt cược thành công: {bet_amount} {asset_type} -> {athlete_name}")
            return True
        else:
            print(Fore.RED + f"❌ Đặt cược thất bại: {data}")
    except Exception as e:
        print(Fore.RED + f"❌ Lỗi đặt cược: {e}")
    return False

def manual_place_bet(headers, issue_id, champion_id, user_data, asset_mode="BUILD"):
    headers["User-Agent"] = random.choice(USER_AGENTS)  # Thêm User-Agent ngẫu nhiên
    url = "https://api.sprintrun.win/sprint/bet"
    bet_mode = "champion" if user_data.get("choice_bet") == "winner" else "not_champion"
    bet_group = "winner" if bet_mode == "champion" else "not_winner"

    payload = {
        "coin": asset_mode,
        "issue_id": str(issue_id),
        "champion_id": int(champion_id),
        "bet_amount": float(user_data.get("coins", 1)),
        "bet_mode": bet_mode,
        "bet_group": bet_group
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                print(Fore.GREEN + f"✅ Đặt cược tay thành công kỳ {issue_id}")
                return True
            else:
                print(Fore.RED + f"❌ Đặt cược tay thất bại: {data}")
        else:
            print(Fore.RED + f"❌ HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print(Fore.RED + f"❌ Lỗi đặt cược tay: {e}")
    return False

def show_wallet(headers, retries=3, delay=2, silent=False):
    headers["User-Agent"] = random.choice(USER_AGENTS)  # Thêm User-Agent ngẫu nhiên
    url = "https://wallet.3games.io/api/wallet/user_asset"
    balances = {"USDT": 0.0, "WORLD": 0.0, "BUILD": 0.0}
    payload = {"user_id": headers.get("User-Id")}
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                vi_data = r.json()
                if isinstance(vi_data, dict) and vi_data.get("code") == 0:
                    data = vi_data.get("data", {})
                    if isinstance(data, dict) and "user_asset" in data:
                        ua = data["user_asset"] or {}
                        for k in balances.keys():
                            v = ua.get(k)
                            try:
                                value = float(v) if v is not None else 0.0
                            except Exception:
                                value = 0.0
                            balances[k] = round(value, 2) if value >= 0.01 else 0.0
                    if not silent:
                        print(
                            Fore.LIGHTGREEN_EX
                            + f"Số dư của bạn:\nUSDT: {balances['USDT']}   WORLD: {balances['WORLD']}   BUILD: {balances['BUILD']}"
                        )
                    return balances["BUILD"]
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(delay)
    return balances["BUILD"]

def save_link(link):
    try:
        with open("links.txt", "w", encoding="utf-8") as f:
            f.write(link.strip())
    except Exception:
        pass

def load_link():
    try:
        if os.path.exists("links.txt"):
            with open("links.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return None

def print_game_data(issues_10, stats_100, bot_choice_name, last_champion_name):
    print(Fore.CYAN + "\n╔════════════════════╗" + Fore.WHITE)
    print(Fore.CYAN + "║" + Fore.YELLOW + " DỮ LIỆU 10 VÁN     " + Fore.CYAN + "║" + Fore.WHITE)
    print(Fore.CYAN + "╚════════════════════╝" + Fore.WHITE)
    for issue in issues_10:
        issue_id = issue.get("issue_id", "N/A")
        champion_id = None
        if isinstance(issue.get("result"), list) and issue["result"]:
            champion_id = issue["result"][0]
        champion_name = room_names_map.get(str(champion_id), f"Phòng #{champion_id}")
        print(Fore.CYAN + f"Kì {issue_id}: Người về nhất : {champion_name}")

    print(Fore.CYAN + "\n╔═════════════════╗" + Fore.WHITE)
    print(Fore.CYAN + "║" + Fore.YELLOW + " DỮ LIỆU 100 VÁN " + Fore.CYAN + "║" + Fore.WHITE)
    print(Fore.CYAN + "╚═════════════════╝" + Fore.WHITE)
    for rid, name in room_names_map.items():
        try:
            count = int(stats_100.get(str(rid), 0))
        except Exception:
            count = 0
        print(Fore.YELLOW + f"{name} về nhất {count} lần")
    
    print(Fore.CYAN + "\n╔══════════╗" + Fore.WHITE)
    print(Fore.CYAN + "║" + Fore.YELLOW + " BOT CHỌN " + Fore.CYAN + "║" + Fore.WHITE)
    print(Fore.CYAN + "╚══════════╝" + Fore.WHITE)
    print(Fore.BLUE + f"BOT CHỌN : {bot_choice_name or 'N/A'}")
    print(Fore.GREEN + f"Quán quân kỳ trước : {last_champion_name}")

def calc_next_issue_id(current_issue):
    s = str(current_issue)
    tail = s.split("-")[-1]
    try:
        n = int(tail)
        return str(n + 1)
    except Exception:
        try:
            return str(int(s) + 1)
        except Exception:
            return s

if __name__ == "__main__":
    # Hiển thị hiệu ứng ASCII art khi khởi động
    display_ascii_art()

    device_id = get_device_id()
    kiem_tra_quyen_truy_cap(device_id)

    print(Fore.CYAN + "\n================= LIÊN HỆ ADMIN ================")
    print(Fore.YELLOW + "👨‍💻 Admin: " + Fore.GREEN + "Cường")
    print(Fore.YELLOW + "💬 Zalo Group: " + Fore.CYAN + "https://zalo.me/g/cdomty095")
    print(Fore.CYAN + "================================================\n")

    print(Fore.YELLOW + "\n================ HƯỚNG DẪN LẤY LINK ============\n")
    print(Fore.CYAN + "0. Mở Chrome")
    print(Fore.CYAN + "1. Đăng nhập xworld.io → mở game SprintRun")
    print(Fore.CYAN + "2. Sao chép link có dạng ?userId=...&secretKey=...&language=vi-VN")
    print(Fore.CYAN + "3. Dán link vào đây\n")

    saved_link = load_link()
    if saved_link:
        use_saved = input(Fore.YELLOW + "Sử dụng lại link đã lưu? (y/n): ").strip().lower()
        if use_saved == "y":
            link = saved_link
            print(Fore.GREEN + f"✅ Sử dụng link đã lưu: {link}")
        else:
            link = input("Dán link game mới: ").strip()
            save_link(link)
    else:
        link = input("Dán link game: ").strip()
        save_link(link)

    parsed = urlparse(link)
    params = parse_qs(parsed.query)
    user_id = params.get("userId", [""])[0]
    secret_key = params.get("secretKey", [""])[0]
    lang = params.get("language", ["vi-VN"])[0]

    if not user_id or not secret_key:
        print(Fore.RED + "❌ Link không hợp lệ (thiếu userId/secretKey).")
        raise SystemExit(1)

    headers = {
        "User-Id": user_id,
        "User-Secret-Key": secret_key,
        "Accept-Language": lang,
        "Content-Type": "application/json",
    }

    print(Fore.CYAN + "═" * 40)
    print(Fore.YELLOW + "   CHỌN KIỂU CƯỢC")
    print(Fore.CYAN + "═" * 40)
    print(Fore.GREEN + "1. Cược Quán quân")
    print(Fore.MAGENTA + "2. Cược Không quán quân")
    bet_mode_choice = input(Fore.RED + "Chọn (1-2): " + Fore.WHITE).strip()
    bet_mode = "champion" if bet_mode_choice == "1" else "not_champion"

    try:
        bet_amount = float(input(Fore.YELLOW + "Nhập số BUILD cược ban đầu: ").strip())
        amount_to_increase_on_loss = float(input(Fore.YELLOW + "Tăng cược sau mỗi lần thua: ").strip())
        win_limit = int(input(Fore.YELLOW + "Thắng mấy ván thì nghỉ: ").strip())
        rest_games = int(input(Fore.YELLOW + "Nghỉ bao nhiêu ván: ").strip())
        win_stop = float(input(Fore.YELLOW + "Thắng tổng cộng bao nhiêu BUILD thì dừng (0=bỏ qua): ").strip())
        loss_stop = float(input(Fore.YELLOW + "Thua bao nhiêu BUILD thì dừng (0=bỏ qua): ").strip())
    except ValueError:
        bet_amount = 30.0
        amount_to_increase_on_loss = 10.0
        win_limit = 0
        rest_games = 0
        win_stop = 0.0
        loss_stop = 0.0
        print(Fore.YELLOW + "Nhập sai. Dùng giá trị mặc định.")

    current_bet_amount = bet_amount
    total_wins, total_losses = 0, 0
    win_streak = 0
    total_profit = 0.0
    pending_issue, pending_target = None, None
    room_picked_count = {}
    locked_rooms = {}
    pick_pattern = [1, 2, 1, 3, 1]
    pick_index = 0
    skip_rounds = 0

    initial_balance = show_wallet(headers)
    print(Fore.YELLOW + f"Số dư ban đầu (BUILD): {initial_balance}")

    last_processed_issue = None

    while True:
        if GLOBAL_KEY_MODE == "FREE":
            h, m = thoi_gian_con_lai_trong_ngay()
            print(Fore.GREEN + f"\nKey FREE VTH còn hiệu lực ({h}h {m}m)")

        current_balance = show_wallet(headers, silent=True)
        current_issue, rankings, last_champion_id, last_champion_name, w100, issues_10, stats_100 = analyze_data(headers)

        if not current_issue:
            print(Fore.RED + "API thiếu issue hiện tại, thử lại...")
            time.sleep(3)
            continue

        champion_sorted, not_champion_sorted = rankings

        if last_processed_issue and str(last_processed_issue) != str(current_issue):
            time.sleep(3)
            new_balance = show_wallet(headers)
            profit = (new_balance - current_balance) if (new_balance is not None and current_balance is not None) else 0.0
            total_profit = new_balance - initial_balance if new_balance is not None else total_profit

            if bet_mode == "champion":
                is_win = (str(pending_target) == str(last_champion_id))
            else:
                is_win = (str(pending_target) != str(last_champion_id))

            if is_win:
                total_wins += 1
                win_streak += 1
                print(Fore.GREEN + f"🎉 Kỳ {last_processed_issue}: THẮNG (+{profit:.2f} BUILD)")
                current_bet_amount = bet_amount
                if win_limit > 0 and (total_wins % win_limit == 0):
                    print(Fore.CYAN + f"🛑 Đã thắng {total_wins} ván, tạm nghỉ {rest_games} ván...")
                    skip_rounds = rest_games
            else:
                total_losses += 1
                win_streak = 0
                print(Fore.RED + f"💀 Kỳ {last_processed_issue}: THUA ({profit:.2f} BUILD)")
                current_bet_amount = max(bet_amount, current_bet_amount + amount_to_increase_on_loss)

            if win_stop > 0 and total_profit >= win_stop:
                print(Fore.CYAN + f"🏆 Đã lời {total_profit:.2f} BUILD (>= {win_stop}), tự động thoát.")
                raise SystemExit(0)

            if loss_stop > 0 and total_profit <= -loss_stop:
                print(Fore.RED + f"💀 Đã lỗ {abs(total_profit):.2f} BUILD (>= {loss_stop}), tự động thoát.")
                raise SystemExit(0)

            target_name = room_names_map.get(str(pending_target), f"Quán quân #{pending_target}")
            print(Fore.YELLOW + f"🎯 Bạn chọn: {target_name}")
            print(Fore.CYAN + f"👑 Quán quân: {last_champion_name}")
            pending_issue, pending_target = None, None
            time.sleep(2)

        if not pending_issue:
            if skip_rounds > 0:
                print(Fore.MAGENTA + f"⏸️ Đang nghỉ, còn {skip_rounds} ván...")
                skip_rounds -= 1
                last_processed_issue = current_issue
                time.sleep(4)
                continue

        for rid in list(locked_rooms.keys()):
            locked_rooms[rid] = max(0, locked_rooms[rid] - 1)
            if locked_rooms[rid] <= 0:
                locked_rooms.pop(rid, None)

        ranking = champion_sorted if bet_mode == "champion" else not_champion_sorted
        if not ranking:
            print(Fore.RED + "⚠️ Không có dữ liệu xếp hạng. Bỏ qua kỳ này.")
            last_processed_issue = current_issue
            time.sleep(2)
            continue

        target_rank = pick_pattern[pick_index]
        pick_index = (pick_index + 1) % len(pick_pattern)

        available = [(rid, val) for rid, val in ranking if locked_rooms.get(str(rid), 0) == 0]
        if not available:
            print(Fore.RED + "⚠️ Tất cả lựa chọn đang bị khóa, bỏ qua kỳ này.")
            last_processed_issue = current_issue
            time.sleep(2)
            continue

        if len(available) >= target_rank:
            best_id, _best_val = available[target_rank - 1]
        else:
            best_id, _best_val = available[0]

        best_name = room_names_map.get(str(best_id), f"Quán quân #{best_id}")
        room_picked_count[best_id] = room_picked_count.get(best_id, 0) + 1
        if room_picked_count[best_id] >= 2:
            locked_rooms[str(best_id)] = 1
            room_picked_count[best_id] = 0

        print_game_data(issues_10, stats_100, best_name, last_champion_name)

        print(Fore.RED + "╔══════════════════╗" + Fore.WHITE)
        print(Fore.YELLOW + "║" + Fore.YELLOW + " THỐNG KÊ KẾT QUẢ " + "║" + Fore.YELLOW)
        print(Fore.RED + "╚══════════════════╝" + Fore.WHITE)
        print(Fore.YELLOW + f"📊 Thắng/Thua: {total_wins}/{total_losses}")
        print(Fore.YELLOW + f"   Tổng trận: {total_wins + total_losses}")
        print(Fore.YELLOW + f"   Chuỗi thắng: {win_streak}")
        print(Fore.YELLOW + f"   Lời/Lỗ: {total_profit:.2f} BUILD\n")

        print(Fore.YELLOW + "⏳ Chờ để lấy kỳ mới...")
        time.sleep(10)

        try:
            next_issue = str(int(current_issue) + 1)
            print(
                Fore.CYAN
                + f"💰 Cược kỳ {next_issue}: {current_bet_amount} BUILD "
                + (f"({'Quán quân' if bet_mode=='champion' else 'Không quán quân'})")
            )

            bet_group = "winner" if bet_mode == "champion" else "not_winner"
            success = place_bet(headers, bet_group, "BUILD", int(best_id), next_issue, current_bet_amount)
            if success:
                pending_issue, pending_target = next_issue, str(best_id)
            else:
                print(Fore.RED + "⚠️ Không có quán quân để cược, bỏ qua kỳ này.")
        except Exception as e:
            print(Fore.RED + f"❌ Lỗi xác định kỳ tiếp theo: {e}")
            success = False

        last_processed_issue = current_issue
        print(Fore.RED + f"👑 Quán quân kỳ {current_issue}: {last_champion_name}\n")

        countdown = 1
        while True:
            time.sleep(1)
            print(Fore.YELLOW + f"đang phân tích...{countdown}s", end="\r")
            countdown += 1
            new_issue, *_rest = analyze_data(headers)
            if new_issue and new_issue != current_issue:
                print(Fore.GREEN + "\n🎉 Có kỳ mới! Đang xử lý...")
                break
