import requests
import time
import os
import uuid
import random
import hashlib
import subprocess
import platform
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
from colorama import Fore, init, Style  

init(autoreset=True)

# chữ
ascii_art = """
        
 ▌ ▐·    ▄▄▄▄▄     ▄ .▄
▪█·█▌    •██      ██▪▐█
▐█▐█•     ▐█.▪    ██▀▐█
 ███      ▐█▌·    ██▌▐▀
. ▀       ▀▀▀     ▀▀▀ ·
   𝐀𝐮𝐭𝐨 Đ𝐚̣̆𝐭 𝐂𝐮̛𝐨̛̣𝐜 𝐕𝐓𝐇
                                                                                   
"""

colors = [
    Fore.RED,
    Fore.YELLOW,
    Fore.GREEN,
    Fore.CYAN,
    Fore.BLUE,
    Fore.MAGENTA
]

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

USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; arm64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0 Safari/537.36",

    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",

    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:101.0) Gecko/20100101 Firefox/101.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:118.0) Gecko/20100101 Firefox/118.0",

    # Mac Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",

    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.8 Mobile Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.6 Mobile Safari/604.1",

    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.7 Mobile Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 13_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.4 Mobile Safari/604.1",

    # Android Chrome
    "Mozilla/5.0 (Linux; Android 11; SM-A205) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; Mi 9T Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0 Mobile Safari/537.36",

    # Android khác
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-M315F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; ONEPLUS A6013) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; Huawei P30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Samsung Galaxy S22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0 Mobile Safari/537.36",

    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0 Safari/537.36 Edg/109.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0 Safari/537.36 Edg/111.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0 Safari/537.36 Edg/110.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0 Safari/537.36 Edg/112.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/110.0 Mobile/15E148 Safari/604.1 EdgiOS/110.0",
]

room_names_map = {
    "1": "Nhà Kho",
    "2": "Phòng Họp",
    "3": "Phòng Giám Đốc",
    "4": "Phòng Trò Chuyện",
    "5": "Phòng Giám Sát",
    "6": "Văn Phòng",
    "7": "Phòng Tài Vụ",
    "8": "Phòng Nhân Sự",
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
        # PC thì chọn mode
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

    device_id = "DEVICE-" + hashlib.md5(raw.encode()).hexdigest()[:15].upper()
    print(Fore.BLUE + "📌 Device ID:" +Fore.YELLOW + f" {device_id}")
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
        ds_key_raw = requests.get(url_key, timeout=5).text.strip().splitlines()
        dev_local = device_id.replace("DEVICE-", "").strip().upper()
        for dong in ds_key_raw:
            parts = [p.strip() for p in dong.split("|")]
            if len(parts) >= 4:
                device, key, _, ngay_hh = parts
                dev_file = device.replace("DEVICE-", "").strip().upper()
                if dev_file == dev_local:
                    return key, ngay_hh
    except:
        pass
    return None, None



def kiem_tra_quyen_truy_cap(device_id):
    global GLOBAL_KEY_MODE
    print(Fore.CYAN + "\n" + "=" * 48)
    print(Fore.YELLOW + "   CHỌN LOẠI KEY ( KEY VIP 1k/2 ngày )")
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

        if vip_key:
            print(Fore.YELLOW + f"⭐ Key VIP của bạn: {Fore.MAGENTA}{vip_key} (hạn {ngay_hh})")
        else:
            print(Fore.RED + "❌ Không tìm thấy Key VIP ")
            exit()

        while True:
            key_nhap = input(Fore.YELLOW + "Nhập Key VIP: " + Fore.WHITE).strip()
            if key_nhap == vip_key:
                try:
                    ngay_hh_dt = datetime.strptime(ngay_hh, "%d/%m/%Y")
                    if datetime.now() <= ngay_hh_dt:
                        print(Fore.GREEN + "✅ Key VIP còn hiệu lực!\n")
                        break
                    else:
                        print(Fore.RED + "❌ Key VIP đã hết hạn!")
                except:
                    print(Fore.RED + "❌ Lỗi định dạng ngày trong VIP key!")
            else:
                print(Fore.RED + "❌ Key VIP sai, thử lại...")
    else:
        print(Fore.RED + "❌ Lựa chọn không hợp lệ!")
        exit()


def fetch_data(url, headers):
    headers["User-Agent"] = random.choice(USER_AGENTS)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                return data["data"]
    except:
        pass
    return None


def analyze_data(headers, asset_mode):
    url_recent_10 = f"https://api.escapemaster.net/escape_game/recent_10_issues?asset={asset_mode}"
    url_recent_100 = f"https://api.escapemaster.net/escape_game/recent_100_issues?asset={asset_mode}"
    data_10 = fetch_data(url_recent_10, headers)
    data_100 = fetch_data(url_recent_100, headers)

    if not data_10 or not data_100:
        return None, [], None, None, {}

    current_issue = data_10[0].get("issue_id")
    killed_room_id = str(data_10[0].get("killed_room_id", "0"))
    killed_room_name = room_names_map.get(killed_room_id, f"Phòng #{killed_room_id}")

    rates_100 = {}
    stats_100 = data_100.get("room_id_2_killed_times", {})
    for rid, name in room_names_map.items():
        count = stats_100.get(rid, 0)
        rates_100[rid] = 100 - (count / 100 * 100) if count > 0 else 100

    sorted_rooms = sorted(rates_100.items(), key=lambda x: x[1], reverse=True)
    return current_issue, sorted_rooms, killed_room_id, killed_room_name, rates_100


def place_bet(headers, asset, issue_id, room_id, bet_amount):
    url = "https://api.escapemaster.net/escape_game/bet"
    payload = {
        "asset_type": asset,
        "issue_id": str(issue_id),
        "room_id": int(room_id),
        "bet_amount": bet_amount,
    }

    headers["User-Agent"] = random.choice(USER_AGENTS)
    delay = random.uniform(3.0, 13.0)  # chờ 1–4s trước khi đặt
    time.sleep(delay)

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                print(Fore.GREEN + f"✅ Đặt cược {bet_amount} {asset} vào phòng {room_id} (Kỳ {issue_id}) sau {delay:.1f}s")
                return True
    except Exception as e:
        print(Fore.RED + f"⚠️ Lỗi khi đặt cược: {e}")
    return False


def show_wallet(headers, asset_mode, retries=3, delay=2, silent=False):
    url = "https://wallet.3games.io/api/wallet/user_asset"
    balances = {"USDT": 0.0, "WORLD": 0.0, "BUILD": 0.0}
    payload = {"user_id": headers.get("User-Id")}

    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                vi_data = r.json()
                if vi_data.get("code") == 0:
                    data = vi_data.get("data", {})
                    if isinstance(data, dict) and "user_asset" in data:
                        ua = data["user_asset"]
                        for k, v in ua.items():
                            if k in balances:
                                value = float(v) if v is not None else 0.0
                                balances[k] = round(value, 2) if value >= 0.01 else 0.0
                    if not silent:
                        print(
                            Fore.LIGHTGREEN_EX
                            + f"Số dư ({asset_mode}): {balances[asset_mode]}\n"
                        )
                    return balances[asset_mode]
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(delay)
    return balances[asset_mode]


def save_link(link):
    with open("link.txt", "w") as f:
        f.write(link)


def load_link():
    if os.path.exists("link.txt"):
        with open("link.txt", "r") as f:
            return f.read().strip()
    return None


if __name__ == "__main__":
    # Added call to display_ascii_art from toolvtd.py
    display_ascii_art()

    device_id = get_device_id()
    kiem_tra_quyen_truy_cap(device_id)

    print(Fore.CYAN + "\n================= LIÊN HỆ ADMIN ================")
    print(Fore.YELLOW + "👨‍💻 Admin: " + Fore.GREEN + "Cường")
    print(Fore.YELLOW + "💬 Zalo Group: " + Fore.CYAN + "https://zalo.me/g/cdomty095")
    print(Fore.CYAN + "================================================\n")

    print(Fore.YELLOW + "\n================ HƯỚNG DẪN LẤY LINK ============\n")
    print(Fore.CYAN + "0. Mở Chrome")
    print(Fore.CYAN + "1. Truy cập website: " + Fore.GREEN + "xworld.io")
    print(Fore.CYAN + "2. Đăng nhập vào tài khoản")
    print(Fore.CYAN + "3. Tìm và nhấp vào: " + Fore.GREEN + "Vua thoát hiểm")
    print(Fore.CYAN + "4. Nhấn lập tức truy cập")
    print(Fore.CYAN + "5. Sao chép link website và dán vào đây\n")

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
    headers = {
        "User-Id": user_id,
        "User-Secret-Key": secret_key,
        "Content-Type": "application/json",
    }

    print(Fore.CYAN + "═" * 48)
    print(Fore.YELLOW + "   CHỌN CHẾ ĐỘ")
    print(Fore.CYAN + "═" * 48)
    print(Fore.GREEN + "1. BUILD")
    print(Fore.MAGENTA + "2. USDT")
    print(Fore.LIGHTYELLOW_EX + "3. WORLD")
    choice = input(Fore.GREEN + "Chọn (1-3): ")
    asset_mode = {"1": "BUILD", "2": "USDT", "3": "WORLD"}.get(choice, "BUILD")

    try:
        bet_amount = float(input(Fore.YELLOW + "Nhập số tiền cược ban đầu mỗi trận: ").strip())
        amount_to_increase_on_loss = float(input(Fore.YELLOW + "Nhập số tiền muốn tăng cược sau mỗi lần thua: ").strip())
        win_limit = int(input(Fore.YELLOW + "Win mấy ván thì sẽ dừng cược: ").strip())
        rest_games = int(input(Fore.YELLOW + "Sẽ dừng cược bao nhiêu ván: ").strip())
        win_stop = float(input(Fore.YELLOW + "Thắng bao nhiêu BUILD thì dừng: ").strip())
        loss_stop = float(input(Fore.YELLOW + "Thua bao nhiêu BUILD thì dừng: ").strip())
    except ValueError:
        bet_amount = 10.0
        amount_to_increase_on_loss = 10.0
        win_limit = 0
        rest_games = 0
        win_stop = 0.0
        loss_stop = 0.0
        print(Fore.YELLOW + "Nhập sai. Dùng giá trị mặc định.")

    current_bet_amount = bet_amount
    total_wins, total_losses = 0, 0
    win_streak = 0
    pending_issue, pending_room = None, None
    total_profit = 0.0

    room_picked_count = {}
    locked_rooms = {}
    pick_pattern = [1, 1, 2, 1, 2]

    pick_index = 0
    skip_rounds = 0

    initial_balance = show_wallet(headers, asset_mode)
    print(Fore.YELLOW + f"Số dư ban đầu ({asset_mode}): {initial_balance}")

    while True:
        if GLOBAL_KEY_MODE == "FREE":
            h, m = thoi_gian_con_lai_trong_ngay()
            print(Fore.GREEN + f"\nKey FREE VTH còn hiệu lực ({h}h {m}m)")

        current_balance = show_wallet(headers, asset_mode, silent=True)
        current_issue, sorted_rooms, killed_room_id, killed_room_name, rates_100 = analyze_data(headers, asset_mode)

        if not current_issue:
            print(Fore.RED + "Không lấy được dữ liệu API...")
            time.sleep(5)
            continue

        if pending_issue and str(pending_issue) == str(current_issue):
            time.sleep(3)
            new_balance = show_wallet(headers, asset_mode)
            profit = new_balance - current_balance
            total_profit = new_balance - initial_balance
            
            if killed_room_id != pending_room:
                total_wins += 1
                win_streak += 1
                print(Fore.GREEN + f"🎉 Kỳ {current_issue}: THẮNG (+{profit:.2f} {asset_mode})")
                current_bet_amount = bet_amount
                if win_limit > 0 and total_wins % win_limit == 0:
                    print(Fore.CYAN + f"🛑 Đã thắng {total_wins} ván, tạm nghỉ {rest_games} ván...")
                    skip_rounds = rest_games
            else:
                total_losses += 1
                win_streak = 0
                print(Fore.RED + f"💀 Kỳ {current_issue}: THUA ({profit:.2f} {asset_mode})")
                current_bet_amount += amount_to_increase_on_loss
            
            if win_stop > 0 and total_profit >= win_stop:
                print(Fore.CYAN + f"🏆 Đã lời {total_profit:.2f} {asset_mode} (>= {win_stop}), tự động dừng!")
                exit()
            
            if loss_stop > 0 and total_profit <= -loss_stop:
                print(Fore.RED + f"💀 Đã lỗ {abs(total_profit):.2f} {asset_mode} (>= {loss_stop}), tự động thoát.")
                exit()
            
            print(f"  AI chọn: {room_names_map.get(pending_room, f'Phòng #{pending_room}')}")
            print(Fore.RED + f"  Sát thủ: {killed_room_name}")
            
            pending_issue, pending_room = None, None
            time.sleep(2)

        pred_id = str(int(current_issue) + 1)
        
        if skip_rounds > 0:
            print(Fore.MAGENTA + f"⏸️ Đang nghỉ, còn {skip_rounds} ván...")
            print(Fore.RED + f"🔪 Sát thủ kỳ {current_issue}: {killed_room_name}\n")
            skip_rounds -= 1
            
            countdown = 1
            while True:
                time.sleep(1)
                print(Fore.YELLOW + f"đang phân tích...{countdown}s", end="\r")
                countdown += 1
                new_issue, _, _, _, _ = analyze_data(headers, asset_mode)
                if new_issue and new_issue != current_issue:
                    print(Fore.GREEN + "\n🎉 Có kỳ mới! Đang xử lý...")
                    break
            continue

        print(Fore.BLUE + "╔═══════════════════════════╗" + Fore.WHITE)
        print(Fore.BLUE + "║" + Fore.YELLOW + " ĐẶT CƯỢC CHO KỲ TIẾP THEO " + Fore.BLUE + "║" + Fore.WHITE)
        print(Fore.BLUE + "╚═══════════════════════════╝" + Fore.WHITE)
        
        
        for rid in list(locked_rooms.keys()):
            if locked_rooms[rid] > 0:
                locked_rooms[rid] -= 1
            if locked_rooms[rid] <= 0:
                locked_rooms.pop(rid, None)

        if sorted_rooms:
            target_rank = pick_pattern[pick_index]
            pick_index = (pick_index + 1) % len(pick_pattern)

            available_rooms = [(rid, rate) for rid, rate in sorted_rooms
                               if locked_rooms.get(str(rid), 0) == 0 and str(rid) != str(killed_room_id)]
            
            if not available_rooms:
                print(Fore.RED + "⚠️ Tất cả phòng đều bị khóa hoặc vừa có sát thủ, bỏ qua kỳ này.")
                time.sleep(2)
                continue
                
            if len(available_rooms) >= target_rank:
                best_room_id, best_rate = available_rooms[target_rank - 1]
            else:
                best_room_id, best_rate = available_rooms[0]
            
            best_room_name = room_names_map.get(str(best_room_id), f"Phòng #{best_room_id}")
            print(Fore.CYAN + f"🔄 chọn phòng: chọn phòng {target_rank} ({best_room_name})")
            
            room_picked_count[best_room_id] = room_picked_count.get(best_room_id, 0) + 1
            if room_picked_count[best_room_id] >= 2:
                locked_rooms[best_room_id] = 1
                room_picked_count[best_room_id] = 0

            print(Fore.MAGENTA + f"✅ Phòng được chọn: {best_room_name}")
            print(Fore.GREEN + f"🎲 độ an toàn: {best_rate:.1f}%")

            print(Fore.YELLOW + "📈 Top 3 phòng an toàn:")
            for i in range(min(3, len(sorted_rooms))):
                room_id, rate = sorted_rooms[i]
                room_name = room_names_map.get(str(room_id), f"Phòng #{room_id}")
                print(Fore.YELLOW + f"   {i+1}. {room_name}: {rate:.1f}%")

            print(Fore.RED + "╔══════════════════╗" + Fore.WHITE)
            print(Fore.RED + "║" + Fore.YELLOW + " THỐNG KÊ KẾT QUẢ " + Fore.RED +"║" + Fore.WHITE)
            print(Fore.RED + "╚══════════════════╝" + Fore.WHITE)
            
            print(Fore.YELLOW + f"📊 Tỉ lệ thắng/thua: {total_wins}/{total_losses}")
            print(Fore.YELLOW + f"   Tổng trận: {total_wins + total_losses}")
            print(Fore.YELLOW + f"   Chuỗi thắng: {win_streak}")
            print(Fore.YELLOW + f"   Lời/Lỗ: {total_profit:.2f} {asset_mode}\n")

            print(Fore.CYAN + f"💰 Số tiền cược cho kỳ {pred_id}: {current_bet_amount} {asset_mode}")
            success = place_bet(headers, asset_mode, pred_id, int(best_room_id), current_bet_amount)
            if success:
                pending_issue, pending_room = pred_id, str(best_room_id)

        print(Fore.RED + f"🔪 Sát thủ kỳ {current_issue}: {killed_room_name}\n")

        countdown = 1
        while True:
            time.sleep(1)
            print(Fore.YELLOW + f"đang phân tích...{countdown}s", end="\r")
            countdown += 1
            new_issue, _, _, _, _ = analyze_data(headers, asset_mode)
            if new_issue and new_issue != current_issue:
                print(Fore.GREEN + "\n🎉 Có kỳ mới! Đang xử lý...")
                break