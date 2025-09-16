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
from colorama import init
init()  # Khởi tạo colorama
import json
import os
import sys
import time
import threading
import random
import logging
import requests
from collections import deque, defaultdict
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from collections import Counter

import pytz
import websocket
from collections import Counter, defaultdict, deque
import websocket

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.align import Align
from rich import box
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn, SpinnerColumn
from rich.rule import Rule

def show_wallet(headers, asset_mode, retries=3, delay=2, silent=False):
    """
    Hàm show_wallet được sửa từ toolvth.py: Phân tích JSON theo cấu trúc dict "user_asset".
    Không print số dư nếu silent=True, chỉ console.print lỗi nếu có.
    """
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
                    return balances[asset_mode]
        except Exception as e:
            if not silent:
                console.print(f"[red]Lỗi lấy số dư: {e}[/]")
        if attempt < retries - 1:
            time.sleep(delay)
    return balances[asset_mode]
    
    
def preload_history(headers, asset_mode="BUILD"):
    """
    Lấy lịch sử 10 + 100 ván từ API escapemaster, nạp vào killer_history
    và cập nhật thống kê AI (mô phỏng tuần tự như thực tế).
    Robust: xử lý item là str / dict, nhiều tên trường khác nhau.
    """
    try:
        url10 = f"https://api.escapemaster.net/escape_game/recent_10_issues?asset={asset_mode}"
        url100 = f"https://api.escapemaster.net/escape_game/recent_100_issues?asset={asset_mode}"

        def fetch_data(url, headers):
            h = headers.copy() if isinstance(headers, dict) else {}
            h.setdefault("User-Agent", "Mozilla/5.0")
            try:
                r = requests.get(url, headers=h, timeout=10)
            except Exception:
                return []
            if r.status_code == 200:
                try:
                    js = r.json()
                    if isinstance(js, dict) and js.get("code") == 0:
                        return js.get("data", []) or []
                except Exception:
                    # not JSON or unexpected -> return empty
                    return []
            return []

        data_10 = fetch_data(url10, headers)
        data_100 = fetch_data(url100, headers)

        # parser an toàn: trả None nếu không parse được
        def parse_item(item):
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except Exception:
                    return None
            if not isinstance(item, dict):
                return None

            # nhiều tên trường có thể xuất hiện -> thử hết
            rid = item.get("killed_room_id")
            if rid is None:
                rid = item.get("killed_room")
            if rid is None:
                rid = item.get("killedRoom")
            if rid is None:
                rid = item.get("room_id")
            if rid is None:
                rid = item.get("room")

            issue = item.get("issue_id") or item.get("issue") or item.get("issueId")

            # chuyển rid về int nếu có thể
            try:
                rid_int = int(rid)
            except Exception:
                try:
                    rid_int = int(str(rid).strip())
                except Exception:
                    return None

            if rid_int not in ROOM_NAMES:
                return None

            return {"room": ROOM_NAMES[rid_int], "issue": issue, "ts": time.time()}

        # thu thập các record từ 100 trước rồi 10 (tránh trùng)
        data = []
        for item in data_100:
            rec = parse_item(item)
            if rec:
                data.append(rec)

        for item in data_10:
            rec = parse_item(item)
            if rec and not any(d.get("issue") == rec.get("issue") for d in data):
                data.append(rec)

        # cố gắng sắp xếp theo số kỳ nếu có
        try:
            data.sort(key=lambda x: int(x.get("issue") or 0))
        except Exception:
            pass

        # Mô phỏng tuần tự: với mỗi ván trong lịch sử,
        # tính prediction từ ai_system dựa trên killer_history hiện tại,
        # cập nhật ai_stats bằng update_ai_stats(ai_results, killed_room_name),
        # sau đó append ván này vào killer_history (giống thực tế).
        for rec in data:
            # build rates/trends giống choose_room_smart
            def make_rates(history, window):
                last = list(history)[-window:] if len(history) > 0 else []
                total = len(last)
                rates = {}
                names = list(ROOM_NAMES.values())
                if total == 0:
                    for n in names:
                        rates[n] = 100.0
                    return rates
                counts = Counter([h['room'] for h in last])
                for n in names:
                    rates[n] = (counts.get(n, 0) / total) * 100.0
                return rates

            rates_10 = make_rates(killer_history, 10)
            rates_100 = make_rates(killer_history, 100)

            trends = {}
            history_list = list(killer_history)
            total_hist = len(history_list)
            for name in ROOM_NAMES.values():
                r10 = (rates_10.get(name, 0.0) / 100.0)
                r100 = (rates_100.get(name, 0.0) / 100.0)
                trend_diff = r10 - r100
                last_idx = None
                for i in range(total_hist - 1, -1, -1):
                    if history_list[i]['room'] == name:
                        last_idx = i
                        break
                rounds_since = (total_hist - 1 - last_idx) if last_idx is not None else None
                is_overdue = True if (rounds_since is None or rounds_since > 20) else False
                trends[name] = (trend_diff, is_overdue, rounds_since if rounds_since is not None else 999)

            try:
                ai_results = ai_system.predict_advanced(rates_10, rates_100, trends, list(killer_history))
            except Exception:
                ai_results = {}

            # update AI stats theo kết quả thật của ván (killed room)
            try:
                update_ai_stats(ai_results, rec["room"])
            except Exception:
                # bảo đảm không crash nếu update_ai_stats khác signature
                pass

            # cuối cùng nạp ván vào killer_history (để vòng sau AI thấy nó)
            killer_history.append(rec)

        console.print(f"[green]✅ Preload {len(data)} ván từ API (10 + 100 gần nhất) & cập nhật AI stats[/]")
    except Exception as e:
        console.print(f"[red]❌ Lỗi preload lịch sử: {e}[/]")
        
        
        
def load_link():
    if os.path.exists("link.txt"):
        with open("link.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


# ======================= CẤU HÌNH CƠ BẢN =======================
console = Console()
tz = pytz.timezone("Asia/Ho_Chi_Minh")

# Logger
logger = logging.getLogger("vip")
logger.setLevel(logging.INFO)
_log_handler = logging.FileHandler("escape_vip_upgraded.log", encoding="utf-8")
_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(_log_handler)

# ======================= hằng số & trạng thái =======================
ROOM_NAMES = {
    1: "Nhà kho", 2: "Phòng họp", 3: "Phòng giám đốc", 4: "Phòng trò chuyện",
    5: "Phòng giám sát", 6: "Văn phòng", 7: "Phòng tài vụ", 8: "Phòng nhân sự"
}
ROOM_ORDER = [1,2,3,4,5,6,7,8]

# ======================= BIẾN GLOBAL CÒN THIẾU =======================
# Thêm các biến này vào code của bạn:

killer_history = deque(maxlen=100)  # Lưu lịch sử phòng bị kill
room_names_map = {v: k for k, v in ROOM_NAMES.items()}  # Map tên phòng -> ID
room_ids_map = {v: k for k, v in ROOM_NAMES.items()}    # Map tên phòng -> ID  
bet_multiplier = 2.0  # Hệ số nhân cược khi thua
last_ai_results = {}  # Kết quả dự đoán AI gần nhất
fixed_room = 1  # Phòng cố định khi chọn mode FIXED


USER_ID = None
SECRET_KEY = None

# trạng thái vòng
issue_id = None
count_down = None
killed_room = None
round_index = 0

# trạng thái phòng realtime
room_state = {r: {"players": 0, "bet": 0} for r in ROOM_ORDER}

# thống kê phòng
room_stats = {
    r: {
        "kills": 0,
        "survives": 0,
        "last_kill_round": None,
        "last_players": 0,
        "last_bet": 0
    } for r in ROOM_ORDER
}

# UI states
STATE_IDLE = "IDLE"
STATE_ANALYZING = "ANALYZING"
STATE_PREDICTED = "PREDICTED"
STATE_WAITING_RESULT = "WAITING_RESULT"
ui_state = STATE_IDLE


# Số ván bỏ qua khi thua (0 = không nghỉ). Khi thua sẽ set skip_rounds = 3

analysis_start_ts = None
analysis_duration = 30.0  # Phân tích 30s theo yêu cầu

prediction_locked = False
predicted_room = None
last_predicted_room = None
last_killed_room = None
skip_rounds = 0


recent_predictions = deque(maxlen=8)
last_two_predictions = deque(maxlen=2)


# AI Stats
ai_stats = {
    "Heuristic": {"wins": 0, "total": 0},
    "Alternating": {"wins": 0, "total": 0},
    "Clustering": {"wins": 0, "total": 0},
    "Cycles": {"wins": 0, "total": 0},
    "Avoidance": {"wins": 0, "total": 0},
}

# Win/Lose
win_count = 0
lose_count = 0
scored_issue = set()

# health
last_msg_ts = time.time()
last_result_ts = 0
received_result = False

# websocket holder
_ws_holder = {"ws": None, "last_connect_attempts": 0}

# betting config
base_bet = None
bet_sequence = None
current_bet = None
lose_streak = 0
bet_sent_for_issue = set()
bet_attempts = defaultdict(int)
MAX_BET_RETRIES = 2
bet_history = []

# balances
current_balance = None
current_balance_world = None
current_balance_usdt = None
previous_balance_build = None
initial_balance_build = None   # dùng để tính lời/lỗ tổng (so với số dư ban đầu)

max_martingale = None
DEBUG_API = False

BET_API_URL = "https://api.escapemaster.net/escape_game/bet"
BALANCE_API_URL = "https://wallet.3games.io/api/wallet/get_all_wallet_addr"

# modes
MODE_MARTINGALE = "MARTINGALE"
MODE_ALLIN = "ALLIN"
MODE_STATS_ONLY = "STATS"
run_mode = None

ALLIN_ROUNDS_MAX = 2
allin_rounds_left = 0

# selection modes (6 chế độ)
SEL_SMART = "SMART"
SEL_FIXED = "FIXED"
SEL_ORDER = "ORDER"
SEL_MIN_PLAYERS = "MIN_PLAYERS"
SEL_MAX_PLAYERS = "MAX_PLAYERS"
SEL_RANDOM_ONLY = "RANDOM"
selection_mode = SEL_SMART
fixed_room_choice = None
order_pos = 0

# Nhãn cho selection modes và admin
SELECTION_LABELS = {
    SEL_SMART: "AI",
    SEL_FIXED: "CỐ ĐỊNH",
    SEL_ORDER: "THEO THỨ TỰ",
    SEL_MIN_PLAYERS: "ÍT NGƯỜI NHẤT",
    SEL_MAX_PLAYERS: "NHIỀU NGƯỜI NHẤT",
    SEL_RANDOM_ONLY: "NGẪU NHIÊN",
}
def sel_label(mode):
    return SELECTION_LABELS.get(mode, str(mode))

ADMIN_ZALO = "VCUONG"

# filters (giữ mặc định; không hỏi người dùng nữa)
filter_min_bet = 0.0
filter_max_bet = float('inf')
filter_min_players = 0
filter_max_players = 9999

# termux
ask_run_24_7 = False
termux_script_path = "run_escape_termux.sh"

random.seed(int(time.time() * 1000) % 10_000_000)

# ======================= helper input =======================

def safe_input(prompt, default=None, cast=None):
    try:
        txt = input(prompt).strip()
    except EOFError:
        return default
    if txt == "":
        return default
    if cast:
        try:
            return cast(txt)
        except Exception:
            return default
    return txt

SECRET = "MY_SECRET_SALT"
GLOBAL_KEY_MODE = None

# Thêm phần code banner từ toolvth.py
ascii_art = """
        
██╗   ██╗████████╗██╗  ██╗
██║   ██║╚══██╔══╝██║  ██║
██║   ██║   ██║   ███████║
╚██╗ ██╔╝   ██║   ██╔══██║
 ╚████╔╝    ██║   ██║  ██║
  ╚═══╝     ╚═╝   ╚═╝  ╚═╝
                          
                
   ❂𝐀𝐮𝐭𝐨 Đ𝐚̣̆𝐭 𝐂𝐮̛𝐨̛̣𝐜 𝐕𝐓𝐇❂
                                                                                   
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

    device_id = "DEVICE-" + hashlib.md5(raw.encode()).hexdigest()[:20].upper()
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
        url_key = "https://ghproxy.net/https://raw.githubusercontent.com/Cuongdz2828/pt/main/test/a.txt"
        ds_key_raw = requests.get(url_key, timeout=5).text.strip().splitlines()
        dev_local = device_id.replace("DEVICE-", "").strip().upper()
        for dong in ds_key_raw:
            parts = [p.strip() for p in dong.split("|")]   # 👈 đổi ts -> parts
            if len(parts) >= 4:
                device, key, _, ngay_hh = parts
                dev_file = device.replace("DEVICE-", "").strip().upper()
                if dev_file == dev_local:
                    return key, ngay_hh
    except Exception as e:
        print("Lỗi load VIP key:", e)
    return None, None



def kiem_tra_quyen_truy_cap(device_id):
    global GLOBAL_KEY_MODE
    print(Fore.CYAN + "\n" + "=" * 48)
    print(Fore.YELLOW + "   CHỌN LOẠI KEY ( KEY VIP 1k/1 ngày )")
    print(Fore.CYAN + "=" * 48)
    print(Fore.GREEN + "➤[1]. Key Free (vượt link)")
    print(Fore.MAGENTA + "➤[2]. Key VIP (ib Cường để mua)")
    print(Fore.CYAN + "=" * 48)

    choice = input(Fore.YELLOW + "[➤]CHỌN ☞[1-2]: " + Fore.WHITE).strip()

    if choice == "1":
        GLOBAL_KEY_MODE = "FREE"
        print(Fore.CYAN + "\n➤Bạn đã chọn Key Free")

        free_links = [
            "https://link4m.com/Bhdv5",
            "https://link4m.com/LvWUEq5F",
            "https://link4m.com/Bhbv5",
            "https://link4m.com/LvWUEq5F",
             ]
        random_link = random.choice(free_links)

        # Thêm khung bao chỉ cho "Vui lòng mở link rút gọn 4m để lấy key:" và link
        def display_framed_message():
            message = [
                "Vui lòng mở link rút gọn 4m để lấy key:",
                "   " + random_link
            ]
            frame_width = 48
            print(Fore.CYAN + "╔" + "═" * (frame_width - 2) + "╗")
            for line in message:
                padding = " " * ((frame_width - len(line) - 2) // 2)
                if "Vui lòng mở" in line:
                    print(Fore.CYAN + "║" + padding + Fore.YELLOW + line + padding + Fore.CYAN + "║")
                else:
                    print(Fore.CYAN + "║" + padding + Fore.GREEN + line + padding + Fore.CYAN + "║")
            print(Fore.CYAN + "╚" + "═" * (frame_width - 2) + "╝")

        display_framed_message()

        print(Fore.YELLOW + "➤ Sau khi vượt qua, để thấy User ID + Key Free")

        user_id = input(Fore.YELLOW + "➤ Nhập User ID (copy từ web): " + Fore.WHITE).strip()
        free_key = make_free_key(user_id)

        while True:
            key_nhap = input(Fore.YELLOW + "➤ Nhập Key Free: " + Fore.WHITE).strip()
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



def parse_login():
    global USER_ID, SECRET_KEY
    console.print(Rule("[bold cyan]Đăng nhập[/]"))
    link = safe_input("Dán link trò chơi (từ xworld.info) tại đây (acc chính) > ", default=None)
    if not link:
        console.print("[red]❌ Không nhập link. Dừng chương trình.[/]")
        sys.exit(1)
    try:
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        USER_ID = int(params.get("userId", [None])[0]) if params.get("userId") else None
        SECRET_KEY = params.get("secretKey", [None])[0]
    except Exception:
        USER_ID = SECRET_KEY = None
    if USER_ID and SECRET_KEY:
        console.print(f"[green]✅ Đăng nhập: {USER_ID}[/]")
    else:
        console.print(f"[red]❌ Link không hợp lệ. Dừng chương trình.[/]")
        sys.exit(1)


def main_menu():
    console.print(Rule("[bold magenta]ESCAPE VIP [/]"))
    console.print("[bold]Chọn chức năng:[/]")
    console.print("  [cyan]1[/]. Gấp cược tự động")
    console.print("  [cyan]2[/]. ALL-IN (đang fix)")
    console.print("  [cyan]3[/]. xem dự đoán không đặt cược)")
    while True:
        choice = safe_input("Nhập số (1/2/3): ", default=None)
        if choice in ("1","2","3"):
            return choice
        console.print("[yellow]Vui lòng nhập 1, 2 hoặc 3.[/]")


def prompt_common_settings():
    global DEBUG_API, selection_mode, fixed_room_choice
    global filter_min_bet, filter_max_bet, filter_min_players, filter_max_players
    global ask_run_24_7

    console.print(Rule("[bold cyan]CÀI ĐẶT CHUNG[/]"))
    dbg = safe_input("Bật debug API? (y/N): ", default="n")
    DEBUG_API = (dbg and dbg.lower() == "y")
    logger.setLevel(logging.DEBUG if DEBUG_API else logging.INFO)
    if DEBUG_API:
        console.print("[yellow]Debug API: BẬT (ghi file escape_vip_upgraded.log)[/]")

    # CHỌN CHẾ ĐỘ CHỌN PHÒNG (6 chế độ) — trực tiếp
    console.print("\n[bold]Chế độ chọn phòng (Enter=1):\n  1. AI\n  2. CỐ ĐỊNH\n  3. THEO THỨ TỰ\n  4. ÍT NGƯỜI NHẤT\n  5. NHIỀU NGƯỜI NHẤT\n  6. NGẪU NHIÊN\n")
    sel = safe_input("Chọn 1-6 (Enter=1): ", default="1")
    try:
        sel_i = int(sel)
    except:
        sel_i = 1
    if sel_i == 2:
        selection_mode = SEL_FIXED
        fixed_room_choice = safe_input("Nhập ID phòng chọn (1..8): ", default=None, cast=int)
        if fixed_room_choice not in ROOM_ORDER:
            console.print("[yellow]Phòng không hợp lệ, quay về AI.[/]")
            selection_mode = SEL_SMART
            fixed_room_choice = None
    elif sel_i == 3:
        selection_mode = SEL_ORDER
    elif sel_i == 4:
        selection_mode = SEL_MIN_PLAYERS
    elif sel_i == 5:
        selection_mode = SEL_MAX_PLAYERS
    elif sel_i == 6:
        selection_mode = SEL_RANDOM_ONLY
    else:
        selection_mode = SEL_SMART

    # Bỏ prompt nhập filter: tool tự động dùng filter mặc định và không hỏi người dùng nữa
    console.print(f"[cyan]Chọn: {sel_label(selection_mode)} | BetFilter={filter_min_bet}-{('no_limit' if filter_max_bet==float('inf') else filter_max_bet)} | Players={filter_min_players}-{('no_limit' if filter_max_players>=9999 else filter_max_players)}[/]")

    # 24/7 run
    ask_run = safe_input("bạn có muốn chạy termux 24/7 không bị tắt (treo tool) (y/N): ", default="n")
    ask_run_24_7 = (ask_run and ask_run.lower() == 'y')
    if ask_run_24_7:
        try:
            with open(termux_script_path, 'w', encoding='utf-8') as f:
                f.write('#!/data/data/com.termux/files/usr/bin/sh\n')
                f.write('while true; do\n')
                f.write(f'  python3 "{os.path.abspath(sys.argv[0])}"\n')
                f.write('  sleep 3\n')
                f.write('done\n')
            os.chmod(termux_script_path, 0o755)
            console.print(f"[green]Tạo script Termux: {termux_script_path} — chạy: bash {termux_script_path}[/]")
        except Exception as e:
            console.print(f"[red]Không thể tạo script Termux: {e}[/]")

# ======================= mạng: headers & balance =======================

def api_headers():
    return {
        'authority': 'api.escapemaster.net',
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://xworld.info',
        'referer': 'https://xworld.info/',
        'user-agent': 'Mozilla/5.0',
        'user-id': str(USER_ID),
        'user-login': 'login_v2',
        'user-secret-key': SECRET_KEY,
        'country-code': 'vn',
        'xb-language': 'vi-VN',
    }


def balance_headers():
    return {'accept': 'application/json', 'user-agent': 'Mozilla/5.0', 'referer': 'https://xworld.info/'}

def fetch_balances_detailed():
    try:
        headers = {
            "User-Id": str(USER_ID),
            "User-Secret-Key": SECRET_KEY,
            "Content-Type": "application/json",
        }
        build = show_wallet(headers, "BUILD", silent=True)
        world = show_wallet(headers, "WORLD", silent=True)
        usdt = show_wallet(headers, "USDT", silent=True)

        global current_balance, current_balance_world, current_balance_usdt
        current_balance = build
        current_balance_world = world
        current_balance_usdt = usdt

        return build, world, usdt
    except Exception as e:
        return None, None, None

def fetch_balance():
    b, _, _ = fetch_balances_detailed()
    return b

# ======================= thuật toán VIP v2 + bộ lọc =======================

def _posterior_kill_prob(room_id:int) -> float:
    st = room_stats.get(room_id, {})
    k = st.get("kills", 0); s = st.get("survives", 0)
    return (k + 1.0) / (k + s + 2.0)


def _cooldown_penalty(room_id:int, now_round:int) -> float:
    last_k = room_stats[room_id].get("last_kill_round")
    if last_k is None: return 0.0
    dist = max(0, now_round - last_k)
    return 0.6 ** max(0, dist)


def _crowd_score(players:int, target:int=12) -> float:
    target = max(1, target)
    diff = abs(players - target) / float(target)
    return min(1.0, max(0.0, 1.0 - min(diff, 1.0)))


def _money_score(total_bet:float, ref:float=12000.0) -> float:
    x = max(0.0, float(total_bet))
    return 1.0 / (1.0 + (x / max(1.0, ref)))


def _delta_penalty(curr:float, prev:float, th_ratio:float=0.35) -> float:
    prev = max(0.0, float(prev)); curr = max(0.0, float(curr))
    if prev == 0 and curr == 0: return 0.0
    base = prev if prev > 0 else 1.0
    ratio = (curr - prev) / base
    if ratio <= th_ratio: return 0.0
    return min(1.0, (ratio - th_ratio) / (1.0 + ratio))


def _repeat_penalty(room_id:int) -> float:
    rep_counts = defaultdict(int)
    for r in recent_predictions: rep_counts[r] += 1
    m = max(rep_counts.values()) if rep_counts else 0
    return 0.3 * (rep_counts[room_id] / float(m)) if m > 0 else 0.0


def _raw_scores_components():
    comps = {}
    banned = set(last_two_predictions)
    if last_killed_room: banned.add(last_killed_room)
    for rid in ROOM_ORDER:
        players = room_state.get(rid, {}).get("players", 0)
        bet = room_state.get(rid, {}).get("bet", 0)
        comps[rid] = {
            "banned": (rid in banned),
            "p_kill": _posterior_kill_prob(rid),
            "players": players,
            "bet": bet,
            "cd_pen": _cooldown_penalty(rid, round_index),
            "d_players": _delta_penalty(players, room_stats[rid]["last_players"], 0.35),
            "d_money": _delta_penalty(bet, room_stats[rid]["last_bet"], 0.35),
            "rep_pen": _repeat_penalty(rid),
        }
    return comps


def _score_from_components(c:dict, w:dict, bias:dict) -> float:
    safety = 1.0 - c["p_kill"]
    crowd  = _crowd_score(c["players"])
    money  = _money_score(c["bet"])
    score = (
        w["safety"] * safety +
        w["crowd"]  * crowd  +
        w["money"]  * money  -
        w["cd_pen"] * c["cd_pen"] -
        w["d_players"] * c["d_players"] -
        w["d_money"]   * c["d_money"]   -
        w["rep_pen"]   * c["rep_pen"]
    )
    score += bias.get("prefer_low_players", 0.0) * (1.0 - min(1.0, c["players"]/20.0))
    score += bias.get("prefer_low_bet", 0.0)     * (1.0 - min(1.0, c["bet"]/20000.0))
    if last_killed_room and bias.get("avoid_last_kill", 0.0) > 0 and last_killed_room == c.get("rid", -1):
        score -= bias["avoid_last_kill"] * 0.8
    return score


def score_rooms_vip(style: str):
    comps = _raw_scores_components()
    scores = {}
    for rid in ROOM_ORDER:
        c = comps[rid]
        if c.get("banned"):
            scores[rid] = -1e9
            continue
        c["rid"] = rid
        w = {"safety": 0.50, "crowd": 0.18, "money": 0.18,
            "cd_pen": 0.07, "d_players": 0.04, "d_money": 0.04, "rep_pen": 0.03}
        b = {"prefer_low_players": 0.0, "prefer_low_bet": 0.0, "avoid_last_kill": 0.0}
        scores[rid] = _score_from_components(c, w, b)
    return scores


def _choose_deterministic(scores:dict, candidates:list):
    ranked = sorted(((rid,scores[rid]) for rid in candidates), key=lambda kv: (-kv[1], kv[0]))
    return ranked[0][0] if ranked else (candidates[0] if candidates else ROOM_ORDER[0])


def _choose_randomized(scores:dict, candidates:list):
    ranked = sorted(((rid,scores[rid]) for rid in candidates), key=lambda kv: (-kv[1], kv[0]))
    usable = [rid for rid,sc in ranked]
    if not usable:
        return random.choice(ROOM_ORDER)
    topk = usable[:3] if len(usable)>=3 else usable
    return random.choice(topk)


def apply_filters(candidates:list):
    out = []
    for rid in candidates:
        st = room_state.get(rid, {})
        players = st.get("players", 0); bet = st.get("bet", 0)
        if players < filter_min_players or players > filter_max_players: continue
        if bet < filter_min_bet or bet > filter_max_bet: continue
        out.append(rid)
    return out
    
    
def choose_room_smart():
    global order_pos, last_ai_results

    if selection_mode == SEL_SMART:
        # --- tạo rates_10 / rates_100 từ killer_history ---
        def make_rates(history, window):
            last = list(history)[-window:] if len(history) > 0 else []
            total = len(last)
            rates = {}
            names = list(ROOM_NAMES.values())
            if total == 0:
                for n in names: 
                    rates[n] = 100.0
                return rates
            counts = Counter([h['room'] for h in last])
            for n in names:
                rates[n] = (counts.get(n, 0) / total) * 100.0
            return rates

        rates_10 = make_rates(killer_history, 10)
        rates_100 = make_rates(killer_history, 100)

        # --- trends đơn giản ---
        trends = {}
        history_list = list(killer_history)
        total_hist = len(history_list)
        for name in ROOM_NAMES.values():
            r10 = (rates_10.get(name, 0.0) / 100.0)
            r100 = (rates_100.get(name, 0.0) / 100.0)
            trend_diff = r10 - r100
            # tìm lần cuối xuất hiện
            last_idx = None
            for i in range(total_hist - 1, -1, -1):
                if history_list[i]['room'] == name:
                    last_idx = i
                    break
            rounds_since = (total_hist - 1 - last_idx) if last_idx is not None else None
            is_overdue = True if (rounds_since is None or rounds_since > 20) else False
            trends[name] = (trend_diff, is_overdue, rounds_since if rounds_since is not None else 999)

        # --- gọi 5 AI ---
        try:
            ai_results = ai_system.predict_advanced(rates_10, rates_100, trends, list(killer_history))
        except Exception as e:
            if DEBUG_API:
                logger.exception(f"predict_advanced error: {e}")
            ai_results = {}

        # lưu lại để update sau khi có kết quả
        last_ai_results = ai_results

        # --- vote: phòng nào được nhiều AI chọn nhất ---
        vote_count = defaultdict(int)
        for ai_name, room in ai_results.items():
            if room in room_ids_map:    # room là tên
                vote_count[room] += 1

        if vote_count:
            best_room_name = max(vote_count, key=vote_count.get)
            room_id = room_ids_map.get(best_room_name)
            if room_id in ROOM_ORDER:
                filtered = apply_filters([room_id])
                if filtered:
                    return room_id

        # fallback: nếu không có vote thì theo heuristic
        if ai_results.get("Heuristic"):
            return room_ids_map.get(ai_results["Heuristic"], random.choice(ROOM_ORDER))

        return random.choice(ROOM_ORDER)

    elif selection_mode == SEL_FIXED:
        return fixed_room
    elif selection_mode == SEL_ORDER:
        room = ROOM_ORDER[order_pos]
        order_pos = (order_pos + 1) % len(ROOM_ORDER)
        return room
    else:
        # fallback cũ
        return random.choice(ROOM_ORDER)

# ======================= cược =======================

def place_bet_http(issue, room_id, amount):
    url = BET_API_URL
    payload = {"asset_type": "BUILD", "user_id": USER_ID, "room_id": int(room_id), "bet_amount": float(amount)}
    try:
        r = requests.post(url, headers=api_headers(), json=payload, timeout=10)
        try: j = r.json()
        except: j = {"http_status": r.status_code, "raw": r.text}
        return j
    except Exception as e:
        if DEBUG_API: logger.exception(f"place_bet_http error: {e}")
        return {"error": str(e)}


def _record_bet(issue, room_id, amount, api_response):
    now = datetime.now(tz).strftime("%H:%M:%S")
    rec = {
        "issue_id": issue, "room_id": room_id, "room": ROOM_NAMES.get(room_id, f"Phòng {room_id}"),
        "amount": float(amount), "time": now, "result": "Đang chờ",
        "profit_loss": 0.0, "start_balance": current_balance if current_balance is not None else None,
        "end_balance": None, "api_response": api_response
    }
    bet_history.append(rec); return rec


def place_bet_async(issue, room_id, amount):
    def _worker():
        global bet_attempts, bet_sent_for_issue
        amt = float(amount)
        console.print(f"[cyan]Đang đặt {amt} BUILD vào PHÒNG_{room_id} (v{issue})...[/]")
        res = place_bet_http(issue, room_id, amt)
        if DEBUG_API: logger.debug(f"Bet resp: {res}")
        rec = _record_bet(issue, room_id, amt, res)
        if isinstance(res, dict) and (res.get("msg") == "Must login" or res.get("code") == 1004):
            bet_attempts[issue] += 1
            console.print(f"[red]API 'Must login' v{issue} → gửi enter_game & thử lại ({bet_attempts[issue]})[/]")
            try: safe_send_enter_game()
            except: pass
            time.sleep(0.8)
            if bet_attempts[issue] <= MAX_BET_RETRIES:
                place_bet_async(issue, room_id, amt)
            else:
                console.print(f"[red]Không thể đặt cược v{issue} sau nhiều lần thử.[/]")
            return
        success = isinstance(res, dict) and (res.get("msg") == "ok" or res.get("code") == 0 or res.get("status") in ("ok", 1))
        if success:
            bet_sent_for_issue.add(issue)
            console.print(f"[green]✅ Đặt thành công: {amt} BUILD vào PHÒNG_{room_id} (v{issue}).[/]")
        else:
            bet_attempts[issue] += 1
            console.print(f"[red]Đặt cược lỗi (v{issue}).{' Bật DEBUG để xem log.' if not DEBUG_API else ''}]")
    threading.Thread(target=_worker, daemon=True).start()

# ======================= WebSocket =======================

def safe_send_enter_game():
    ws = _ws_holder.get("ws")
    if not ws:
        if DEBUG_API: logger.debug("enter_game skipped: ws None")
        return
    payload = {"msg_type": "handle_enter_game", "asset_type": "BUILD", "user_id": USER_ID, "user_secret_key": SECRET_KEY}
    try:
        ws.send(json.dumps(payload))
        if DEBUG_API: logger.debug("Sent enter_game")
    except Exception as e:
        if DEBUG_API: logger.exception(f"send_enter_game err: {e}")


def on_open(ws):
    global ui_state
    console.print("[green]KẾT NỐI THÀNH CÔNG[/]")
    _ws_holder["ws"] = ws
    safe_send_enter_game()
    ui_state = STATE_IDLE


def on_error(ws, error):
    if DEBUG_API: logger.exception(f"WS error: {error}")
    console.print(f"[red]WS lỗi (bật DEBUG để ghi chi tiết).[/]")


def on_close(ws, code, reason):
    console.print(f"[magenta]🔌 WS đóng (code={code}). Tự reconnect...[/]")
    try:
        _ws_holder['ws'] = None
    except: pass


def on_ping(ws, message):
    if DEBUG_API: logger.debug("Ping received")


def on_pong(ws, message):
    if DEBUG_API: logger.debug("Pong received")


def _lock_prediction_if_needed():
    global prediction_locked, predicted_room, ui_state, skip_rounds
    if isinstance(skip_rounds, int) and skip_rounds > 0:
        console.log(f"⏸️ Đang nghỉ sau thua — còn {skip_rounds} ván...")
        return
    if not prediction_locked:
        chosen = choose_room_smart()
        prediction_locked = True
        set_prediction(chosen)
        ui_state = STATE_PREDICTED
        threading.Timer(0.12, auto_place_bet_if_needed).start()
        
        

def on_message(ws, message):
    global issue_id, count_down, killed_room, round_index
    global ui_state, analysis_start_ts, prediction_locked, predicted_room
    global last_killed_room, last_predicted_room
    global win_count, lose_count, last_msg_ts, received_result, last_result_ts
    global current_bet, lose_streak, bet_sequence, max_martingale
    global current_balance, last_ai_results   # thêm last_ai_results

    last_msg_ts = time.time()
    try:
        data = json.loads(message)
    except Exception:
        if DEBUG_API:
            logger.debug("Non-json ws msg")
        return

    msg_type = data.get("msg_type")

    # ================== TRẠNG THÁI PHÒNG ==================
    if msg_type == "notify_issue_stat":
        new_issue = data.get("issue_id")
        rooms = data.get("rooms", [])
        for rm in rooms:
            try:
                rid = int(rm.get("room_id", 0))
            except:
                continue
            players = int(rm.get("user_cnt", 0) or 0)
            bet = int(rm.get("total_bet_amount", 0) or 0)
            room_state[rid] = {"players": players, "bet": bet}
            room_stats[rid]["last_players"] = players
            room_stats[rid]["last_bet"] = bet
        if "balance" in data:
            try:
                current_balance = float(data.get("balance", current_balance) or current_balance)
            except:
                pass
        if new_issue != issue_id:
            issue_id = new_issue
            round_index += 1
            killed_room = None
            prediction_locked = False
            last_predicted_room = predicted_room
            predicted_room = None
            received_result = False
            ui_state = STATE_ANALYZING
            analysis_start_ts = time.time()
            if new_issue in bet_attempts:
                del bet_attempts[new_issue]
        if "count_down" in data:
            count_down = data.get("count_down")

    # ================== COUNTDOWN ==================
    elif msg_type == "notify_count_down":
        count_down = data.get("count_down")
        if ui_state == STATE_IDLE and issue_id is not None:
            ui_state = STATE_ANALYZING
            analysis_start_ts = time.time()
        if isinstance(count_down, int) and count_down <= 10 and not prediction_locked:
            _lock_prediction_if_needed()

    # ================== KẾT QUẢ ROUND ==================
    elif msg_type == "notify_result":
        kr = data.get("killed_room") if data.get("killed_room") is not None else data.get("killed_room_id")
        if kr is not None:
            try:
                killed_room_id = int(kr)
            except:
                killed_room_id = kr
            killed_room = killed_room_id
            last_killed_room = killed_room

            # --- thêm vào killer_history ---
            try:
                room_name = ROOM_NAMES.get(killed_room)
                killer_history.append({
                    "room": room_name,
                    "issue": issue_id,
                    "ts": time.time()
                })
            except Exception:
                pass

            # --- update stats rooms ---
            for rid in ROOM_ORDER:
                if rid == killed_room:
                    room_stats[rid]["kills"] += 1
                    room_stats[rid]["last_kill_round"] = round_index
                else:
                    room_stats[rid]["survives"] += 1

            # --- tính win/lose theo phòng cược ---
            if issue_id is not None and issue_id not in scored_issue:
                bet_rec = None
                for b in reversed(bet_history):
                    if b.get("issue_id") == issue_id:
                        bet_rec = b
                        break

                if bet_rec:
                    bet_room_id = int(bet_rec.get("room_id", -1))
                    amt = float(bet_rec.get("amount", 0) or 0)

                    if bet_room_id != int(killed_room):
                        win_count += 1
                        bet_rec["result"] = "Thắng"
                        bet_rec["profit_loss"] = amt   # chỉ tiền lời
                        console.print(f"[green]🏆 Thắng ván này! Lời: +{amt} BUILD[/]")
                    else:
                        lose_count += 1
                        bet_rec["result"] = "Thua"
                        bet_rec["profit_loss"] = -amt
                        console.print(f"[red]💥 Thua ván này! Mất: -{amt} BUILD[/]")

                    # ----------------- Martingale -----------------
                    if run_mode == MODE_MARTINGALE:
                        if bet_rec["result"] == "Thắng":
                            lose_streak = 0
                            if base_bet is not None:
                                current_bet = base_bet
                        else:
                            skip_rounds = 3   # nghỉ 3 ván sau khi thua
                            console.print(f"[magenta]⏸️ Thua ván này → nghỉ {skip_rounds} ván tiếp theo.[/]")
                            lose_streak += 1
                            if base_bet is not None:
                                current_bet = float(base_bet) * (bet_multiplier ** lose_streak)
                    # ------------------------------------------------

                else:
                    # fallback: dùng predicted_room
                    if predicted_room is not None:
                        if int(predicted_room) != int(killed_room):
                            win_count += 1
                        else:
                            lose_count += 1

                # update AI stats
                killed_name = ROOM_NAMES.get(killed_room)
                if last_ai_results:
                    try:
                        update_ai_stats(last_ai_results, killed_name)
                        show_ai_stats()
                    except Exception as e:
                        if DEBUG_API:
                            logger.exception(f"AI stats update error: {e}")

                scored_issue.add(issue_id)

            if run_mode == MODE_ALLIN:
                global allin_rounds_left
                allin_rounds_left = max(0, allin_rounds_left - 1)
                if allin_rounds_left == 0:
                    console.print(Panel("[bold green]Đã hoàn thành 10 ván ALL-IN. Tắt tool.[/]", border_style="green"))
                    time.sleep(1.2)
                    os._exit(0)

        received_result = True
        last_result_ts = time.time()
        ui_state = STATE_WAITING_RESULT

# ======================= vòng giám sát =======================

def monitor_loop():
    global received_result, last_result_ts, last_msg_ts, ui_state
    while True:
        now = time.time()
        if received_result and now - last_result_ts >= 1.6:
            received_result = False; ui_state = STATE_IDLE
            try: safe_send_enter_game()
            except Exception:
                pass
        no_msg_for = now - last_msg_ts
        if no_msg_for >= 15:
            try: safe_send_enter_game()
            except: pass
        if no_msg_for >= 60:
            console.print("[magenta]🔄 Lâu không có dữ liệu, khởi động lại kết nối...[/]")
            try:
                ws = _ws_holder.get("ws")
                if ws: ws.close()
            except: pass
            if ask_run_24_7:
                time.sleep(1.2)
                os.execv(sys.executable, [sys.executable] + sys.argv)
        time.sleep(0.8)

# ======================= UI (tiếng Việt) =======================
LOGO_TN = r"""
██    ██   ██████  
██    ██  ██    
██    ██  ██    
██    ██  ██    
 ██████    ██████
"""

def build_rooms_table():
    t = Table(box=box.MINIMAL_HEAVY_HEAD, expand=True, show_lines=False, pad_edge=False)
    t.add_column("ID", justify="center", style="bold", width=3, no_wrap=True)
    t.add_column("Phòng", justify="left", style="cyan", no_wrap=True)
    t.add_column("Ng", justify="right", style="yellow", width=4, no_wrap=True)
    t.add_column("Cược", justify="right", style="yellow", width=9, no_wrap=True)
    t.add_column("TT", justify="center", style="magenta", width=10, no_wrap=True)
    for rid in ROOM_ORDER:
        name = ROOM_NAMES.get(rid, f"Phòng {rid}")
        st = room_state.get(rid, {})
        players = st.get("players", 0)
        bet = st.get("bet", 0)
        status = ""
        if killed_room == rid: status = "[red]☠ Kill[/]"
        elif predicted_room == rid: status = "[green]✓ Dự đoán[/]"
        t.add_row(str(rid), name, f"{players}", f"{bet:,}", status)
    return t

def build_analysis_view():
    global prediction_locked, ui_state, analysis_start_ts, skip_rounds
    global current_balance, initial_balance_build

    # Nếu đang nghỉ sau khi thua
    if isinstance(skip_rounds, int) and skip_rounds > 0:
        msg = f"[magenta]⏸️ Đang nghỉ sau thua — còn {skip_rounds} ván...[/]"
        skip_rounds -= 1
        return Panel(Align.center(msg), title="⏸ Nghỉ", border_style="magenta", box=box.ROUNDED)

    # Thời gian phân tích
    elapsed = time.time() - (analysis_start_ts or time.time())
    if elapsed >= analysis_duration and not prediction_locked:
        _lock_prediction_if_needed()

    # Cập nhật balance mới nhất
    b, _, _ = fetch_balances_detailed()
    if isinstance(b, (int, float)):
        current_balance = b

    # Thanh tiến trình
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[bold cyan]Phân tích ({int(analysis_duration)}s)...[/]"),
        BarColumn(bar_width=None),
        TextColumn("[yellow]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        expand=True, transient=False
    )
    progress.add_task("", total=analysis_duration, completed=min(elapsed, analysis_duration))

    # ===== Số dư và lời lỗ =====
    build_str = f"{current_balance:.4f}" if isinstance(current_balance, (int,float)) else "-"
    profit_loss = None
    if isinstance(initial_balance_build, (int,float)) and isinstance(current_balance, (int,float)):
        profit_loss = current_balance - initial_balance_build

    info_table = Table.grid(expand=True)
    info_table.add_column(justify="center")
    info_table.add_row(f"[cyan]Tổng số dư BUILD:[/] {build_str}")
    if profit_loss is not None:
        info_table.add_row(f"[bold]Tổng Lời/Lỗ:[/] {profit_loss:+.4f}")

    return Panel(Group(progress, info_table), title="ĐANG PHÂN TÍCH", border_style="bright_magenta", box=box.ROUNDED)
    
    
def set_prediction(room_id: int):
    global predicted_room, recent_predictions, last_two_predictions
    predicted_room = room_id
    recent_predictions.append(room_id)
    last_two_predictions.append(room_id)


def build_prediction_view():
    name = ROOM_NAMES.get(predicted_room, f"Phòng {predicted_room}")
    info = Table.grid(expand=True)
    info.add_column(justify="center")
    mode_txt = "ALL-IN (10 ván)" if run_mode == MODE_ALLIN else "GẤP CƯỢC"
    sub = f"[dim]Chọn:[/] {sel_label(selection_mode)}"
    info.add_row(f"[bold green]✓ PHÒNG AN TOÀN: {name}[/]")
    if run_mode == MODE_MARTINGALE:
        info.add_row(f"[bold]BUILD hiện tại:[/] {current_bet if current_bet is not None else '-'}")
        info.add_row(f"[bold]Chuỗi gấp:[/] {bet_sequence if bet_sequence is not None else 'Tắt'}")
        info.add_row(f"[bold]X LẦN:[/] {max_martingale if max_martingale is not None else '-'}")
    else:
        info.add_row(f"[bold]Chế độ:[/] ALL-IN | [bold]Ván còn:[/bold] {allin_rounds_left}")
    return Panel(Align.center(info), title=f"DỰ ĐOÁN & CƯỢC ({mode_txt})", subtitle=sub, border_style="green", box=box.HEAVY)


def build_header():
    bal_build = f"{current_balance:.4f}" if isinstance(current_balance, (int,float)) else "-"
    bal_world = f"{current_balance_world:.4f}" if isinstance(current_balance_world, (int,float)) else "-"
    bal_usdt  = f"{current_balance_usdt:.4f}"  if isinstance(current_balance_usdt,  (int,float)) else "-"
    total = win_count + lose_count
    winrate = (win_count / total * 100.0) if total > 0 else 0.0
    head = Table.grid(expand=True)
    head.add_column(justify="left")
    head.add_column(justify="center")
    head.add_column(justify="right")
    left = f"[bold]User[/]: {USER_ID} | [bold]BUILD[/]: {bal_build}"
    middle = f"[bold]Phiên[/]: {issue_id or '-'} | [bold]Còn[/]: {count_down if count_down is not None else '-'}"
    right = f"✅ {win_count} / ❌ {lose_count}  •  🏆 {winrate:.1f}%"
    head.add_row(left, middle, right)
    title = "TOOL VUA THOÁT HIỂM VIP"
    logo_panel = Panel(LOGO_TN + f"\nAdmin: {ADMIN_ZALO}", border_style="cyan")
    return Panel(Group(logo_panel, head), title=title, border_style="cyan", box=box.SQUARE)


def build_bet_table():
    bet_table = Table(title="Lịch sử cược (mới nhất)", box=box.MINIMAL_DOUBLE_HEAD, expand=True, pad_edge=False)
    bet_table.add_column("Ván", justify="right", no_wrap=True)
    bet_table.add_column("Phòng", justify="left", no_wrap=True)
    bet_table.add_column("Tiền", justify="right", no_wrap=True)
    bet_table.add_column("KQ", justify="center", no_wrap=True)
    bet_table.add_column("± BUILD", justify="right", no_wrap=True)
    for b in bet_history[-8:]:
        pl = b.get("profit_loss")
        pl_str = f"{pl:.4f}" if isinstance(pl,(int,float)) else str(pl)
        bet_table.add_row(str(b.get("issue_id")), str(b.get("room")), f"{b.get('amount')}", str(b.get("result")), pl_str)
    return bet_table


def build_footer():
    footer = Table.grid(expand=True)
    footer.add_column(justify="left")
    footer.add_column(justify="right")
    mode_txt = "ALL-IN" if run_mode == MODE_ALLIN else ("GẤP CƯỢC" if run_mode == MODE_MARTINGALE else "THỐNG KÊ")
    rounds_txt = f" • ALL-IN còn: {allin_rounds_left}" if run_mode == MODE_ALLIN else ""
    time_txt = datetime.now(tz).strftime("%H:%M:%S")
    footer.add_row(f"[bold]Chế độ:[/] {mode_txt} • [dim]{sel_label(selection_mode)}[/]{rounds_txt}", time_txt)
    return footer


def build_layout():
    header = build_header()
    rooms = build_rooms_table()

    if ui_state == STATE_ANALYZING:
        mid = build_analysis_view()
    elif ui_state == STATE_PREDICTED:
        mid = build_prediction_view()
    elif ui_state == STATE_WAITING_RESULT:
        wait_tbl = Table.grid(expand=True)
        wait_tbl.add_column(justify="center")
        wait_tbl.add_row("[bold magenta]⌛ Đang chờ kết quả ván...[/]")
        mid = Panel(Align.center(wait_tbl), title="⏳ Chờ kết quả", border_style="magenta", box=box.ROUNDED)
    else:
        idle_tbl = Table.grid(expand=True)
        idle_tbl.add_column(justify="center")
        idle_tbl.add_row("[dim]Chờ ván mới...[/]")
        mid = Panel(Align.center(idle_tbl), title="🕊️ Idle", border_style="white", box=box.ROUNDED)

    bets = build_bet_table()
    footer = build_footer()

    # 📊 Bảng thống kê AI (luôn hiển thị)
    ai_table = Table(title="📊 Tỷ lệ dự đoán AI", box=box.MINIMAL_DOUBLE_HEAD)
    ai_table.add_column("AI", style="cyan")
    ai_table.add_column("Phòng dự đoán", style="green")
    ai_table.add_column("Winrate", justify="center")
    ai_table.add_column("Wins", justify="center")
    ai_table.add_column("Total", justify="center")

    for ai_name, st in ai_stats.items():
        wins = st["wins"]
        total = st["total"]
        winrate = f"{wins/total*100:.1f}%" if total > 0 else "N/A"

        # lấy phòng dự đoán mới nhất từ last_ai_results (nếu có)
        predicted_room_name = "-"
        if "last_ai_results" in globals() and last_ai_results:
            predicted_room_name = last_ai_results.get(ai_name, "-")

        ai_table.add_row(ai_name, predicted_room_name, winrate, str(wins), str(total))

    return Panel(
        Group(header, mid, rooms, bets, ai_table, footer),
        border_style="white",
        box=box.MINIMAL
    )

# ======================= auto-bet =======================

def auto_place_bet_if_needed():
    global issue_id, predicted_room, current_bet, current_balance
    if issue_id is None or predicted_room is None: return
    if issue_id in bet_sent_for_issue: return
    if run_mode == MODE_ALLIN:
        bld, _, _ = fetch_balances_detailed()
        if bld is None or bld <= 0:
            console.print("[red]Không lấy được số dư BUILD hoặc = 0, bỏ qua all-in ván này.[/]")
            return
        current_balance = bld; amt = float(bld)
    else:
        if current_bet is None:
            console.print("[yellow]Chưa có current_bet (martingale), bỏ qua ván này.[/]")
            return
        try: amt = float(current_bet)
        except: amt = 0.0
    if amt <= 0:
        console.print("[yellow]Số tiền đặt <= 0, bỏ qua.[/]")
        return
    sb, _, _ = fetch_balances_detailed()
    place_bet_async(issue_id, predicted_room, amt)

# ======================= start ws (reconnect được cải thiện) =======================
def start_ws():
    url = "wss://api.escapemaster.net/escape_master/ws"
    while True:
        try:
            ws = websocket.WebSocketApp(
                url,
                on_open=on_open,
                on_message=on_message,
                on_close=on_close,
                on_error=on_error,
                on_ping=on_ping,
                on_pong=on_pong
            )
            _ws_holder["ws"] = ws
            console.print("[green]✅ Đã kết nối WebSocket[/]")
            ws.run_forever(ping_interval=15, ping_timeout=6)
        except Exception as e:
            now = time.strftime("%H:%M:%S")
            console.print(f"[red]{now} ❌ WS lỗi: {e}[/]")
        now = time.strftime("%H:%M:%S")
        console.print(f"[yellow]{now} 🔄 Đang thử kết nối lại sau 5 giây...[/]")
        time.sleep(5)   # nghỉ 5 giây rồi thử lại

# ======================= các cấu hình trước khi chạy =======================

def prompt_martingale_settings():
    global base_bet, current_bet, lose_streak, max_martingale, bet_multiplier
    console.print(Rule("[bold cyan]CẤU HÌNH GẤP CƯỢC (x mỗi lần thua)[/]"))
    while True:
        txt = safe_input("BUILD đặt mỗi ván (base bet): ", default=None)
        try:
            b = float(txt) if txt is not None else None
            if b is None or b <= 0:
                raise Exception('no')
            base_bet = b
            break
        except Exception:
            console.print("[yellow]BUILD phải là số > 0. Thử lại.[/]")

    # 👉 nhập hệ số gấp
    while True:
        txt = safe_input("Hệ số gấp (ví dụ 2 = x2, 3 = x3): ", default="2")
        try:
            bet_multiplier = float(txt)
            if bet_multiplier <= 0:
                raise Exception('no')
            break
        except Exception:
            console.print("[yellow]Hệ số phải > 1. Thử lại.[/]")

    max_martingale = 10   # giới hạn số lần gấp liên tiếp
    current_bet = base_bet
    lose_streak = 0
    console.print(f"[cyan]Gấp cược: Base={base_bet} | Thua x{bet_multiplier}, Thắng reset | MaxSteps={max_martingale}[/]")
    
    
def init_allin_settings():
    global base_bet, bet_sequence, current_bet, lose_streak, max_martingale, allin_rounds_left
    base_bet = None; bet_sequence = None; current_bet = None
    lose_streak = 0; max_martingale = 0
    allin_rounds_left = ALLIN_ROUNDS_MAX
    console.print(f"[cyan]ALL-IN: sẽ chơi {ALLIN_ROUNDS_MAX} ván, sau đó tự tắt tool.[/]")

# ======================= CÁC LỖI CUỐI CÙNG CẦN SỬA =======================

# 1. THIẾU CLASS PatternDetector - Thêm NGAY TRƯỚC class AdvancedAISystem (khoảng dòng 1050)
class PatternDetector:
    def detect_patterns(self, killer_history):
        patterns = {
            "alternating": 0.0,
            "clustering": 0.0, 
            "cycles": {"score": 0.0, "length": 0},
            "avoidance": {}
        }
        
        if len(killer_history) < 3:
            return patterns
            
        rooms = [h["room"] for h in killer_history[-10:]]
        
        # Detect alternating pattern
        alternating_count = 0
        for i in range(len(rooms) - 1):
            if rooms[i] != rooms[i + 1]:
                alternating_count += 1
        patterns["alternating"] = alternating_count / max(1, len(rooms) - 1)
        
        # Detect clustering
        if rooms:
            most_common = max(set(rooms), key=rooms.count)
            patterns["clustering"] = rooms.count(most_common) / len(rooms)
        
        # Simple avoidance
        all_rooms = list(ROOM_NAMES.values())
        recent_rooms = set(rooms[-5:])
        for room in all_rooms:
            if room not in recent_rooms:
                patterns["avoidance"][room] = 1.0
            else:
                patterns["avoidance"][room] = 0.0
        
        return patterns

# 2. SỬA LỖI TRONG class AdvancedAISystem (dòng 1055)
# Thay đổi room_names_map.values() thành ROOM_NAMES.values()
class AdvancedAISystem:
    def __init__(self):
        self.pattern_detector = PatternDetector()

    def fallback_prediction(self, rates_10, rates_100, trends):
        room_scores = {}
        for room_name in ROOM_NAMES.values():  # ← Sửa từ room_names_map.values()
            base_score = (rates_10.get(room_name, 100/8) * 0.4 +
                          rates_100.get(room_name, 100/8) * 0.6)
            trend_data = trends.get(room_name, (0, False, 0))
            trend_diff, is_overdue, rounds_since = trend_data
            if trend_diff > 0.1:
                base_score -= (trend_diff * 20)
            if is_overdue:
                base_score += 5.0
            room_scores[room_name] = base_score

        best_room = max(room_scores, key=room_scores.get)
        confidence = room_scores[best_room] / sum(room_scores.values()) if room_scores.values() else 0
        return best_room, confidence, {"heuristic": best_room}

    def predict_advanced(self, rates_10, rates_100, trends, killer_history):
        ai_results = {}

        # AI1: heuristic
        heuristic_room, confidence, _ = self.fallback_prediction(rates_10, rates_100, trends)
        ai_results["Heuristic"] = heuristic_room

        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(killer_history)

        # AI2: alternating
        if patterns.get("alternating", 0) > 0.6 and killer_history:
            last_room = killer_history[-1]["room"]
            candidates = [r for r in ROOM_NAMES.values() if r != last_room]  # ← Sửa
            if candidates:
                ai_results["Alternating"] = random.choice(candidates)

        # AI3: clustering
        if patterns.get("clustering", 0) > 0.3 and killer_history:
            rooms = [h["room"] for h in killer_history]
            common_room = max(set(rooms), key=rooms.count)
            ai_results["Clustering"] = common_room

        # AI4: cycles
        cycle = patterns.get("cycles", {})
        if cycle and cycle.get("score", 0) > 0.5:
            cycle_len = cycle.get("length", 0)
            if cycle_len and len(killer_history) >= cycle_len:
                ai_results["Cycles"] = killer_history[-cycle_len]["room"]

        # AI5: avoidance
        avoidance = patterns.get("avoidance", {})
        if avoidance:
            ai_results["Avoidance"] = max(avoidance, key=avoidance.get)

        return ai_results

# 3. THÊM KHỞI TẠO AI SYSTEM (sau class definitions, khoảng dòng 1120)
ai_system = AdvancedAISystem()

# 4. SỬA LỖI TRONG choose_room_smart() (dòng 767)
# Thay đổi fixed_room thành fixed_room_choice
def choose_room_smart():
    global order_pos, last_ai_results

    if selection_mode == SEL_SMART:
        # --- code AI như cũ ---
        # (giữ nguyên phần code AI)
        
        return random.choice(ROOM_ORDER)  # fallback cuối

    elif selection_mode == SEL_FIXED:
        return fixed_room_choice if fixed_room_choice else random.choice(ROOM_ORDER)  # ← Sửa
    elif selection_mode == SEL_ORDER:
        room = ROOM_ORDER[order_pos]
        order_pos = (order_pos + 1) % len(ROOM_ORDER)
        return room
    elif selection_mode == SEL_MIN_PLAYERS:
        candidates = apply_filters(ROOM_ORDER)
        if candidates:
            return min(candidates, key=lambda r: room_state.get(r, {}).get("players", 0))
        return random.choice(ROOM_ORDER)
    elif selection_mode == SEL_MAX_PLAYERS:
        candidates = apply_filters(ROOM_ORDER)
        if candidates:
            return max(candidates, key=lambda r: room_state.get(r, {}).get("players", 0))
        return random.choice(ROOM_ORDER)
    else:  # SEL_RANDOM_ONLY
        candidates = apply_filters(ROOM_ORDER)
        return random.choice(candidates if candidates else ROOM_ORDER)

# 5. CÀI ĐẶT WEBSOCKET-CLIENT
# Chạy lệnh này trước khi chạy code:
# pip install websocket-client

# 6. DỌN DẸP IMPORT TRÙNG LẶP (đầu file)
# Xóa các dòng import trùng lặp:
from collections import deque, defaultdict, Counter  # ← Giữ dòng này
# Xóa: from collections import Counter (dòng 18)
# Xóa: from collections import Counter, defaultdict, deque (dòng 22)
# Xóa: import websocket (dòng 23) - đã có 

def update_ai_stats(ai_results, killed_room_name):
    """
    Cập nhật thống kê cho từng AI sau mỗi ván.
    ai_results: {"Heuristic": "Nhà kho", "Alternating": "Phòng họp", ...}
    killed_room_name: tên phòng vừa bị nổ
    """
    if not ai_results or killed_room_name is None:
        return
    for ai_name, predicted in ai_results.items():
        if ai_name not in ai_stats:
            continue
        ai_stats[ai_name]["total"] += 1
        if predicted == killed_room_name:
            ai_stats[ai_name]["wins"] += 1

def show_ai_stats():
    table = Table(title="📊 Tỷ lệ dự đoán AI", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("AI", style="cyan")
    table.add_column("Winrate", justify="center")
    table.add_column("Wins", justify="center")
    table.add_column("Total", justify="center")

    for ai_name, st in ai_stats.items():
        wins = st["wins"]
        total = st["total"]
        winrate = f"{wins/total*100:.1f}%" if total > 0 else "N/A"
        table.add_row(ai_name, winrate, str(wins), str(total))

    console.print(table)


def main():
    console.print(Rule("[bold cyan]KẾT NỐI NGƯỜI DÙNG[/]"))

    # đọc lại link nếu đã lưu
    saved_link = None
    if os.path.exists("link.txt"):
        try:
            with open("link.txt", "r") as f:
                saved_link = f.read().strip()
        except:
            saved_link = None

    if saved_link:
        console.print(f"[green]Đã tìm thấy link đã lưu: {saved_link}[/]")
        use_saved = safe_input("Dùng link đã lưu? (y/n): ", default="y")
        if use_saved.lower() == "y":
            url = saved_link
        else:
            url = safe_input("Dán link XWorld: ", default=None)
    else:
        url = safe_input("Dán link XWorld: ", default=None)

    if url is None or "userId=" not in url or "secretKey=" not in url:
        console.print("[red]❌ Link không hợp lệ![/]")
        return

    # lưu link lại cho lần sau
    try:
        with open("link.txt", "w") as f:
            f.write(url.strip())
    except:
        pass

    # --- Gán global USER_ID / SECRET_KEY ---
    global USER_ID, SECRET_KEY, initial_balance_build
    user_id = url.split("userId=")[1].split("&")[0]
    secret_key = url.split("secretKey=")[1].split("&")[0]

    try:
        USER_ID = int(user_id)
    except Exception:
        USER_ID = user_id
    SECRET_KEY = secret_key

    # headers dùng chung
    headers = {
        "User-Id": str(USER_ID),
        "User-Secret-Key": SECRET_KEY,
        "Content-Type": "application/json",
    }

    # Lấy số dư ban đầu để hiển thị lãi/lỗ
    try:
        initial_balance_build = show_wallet(headers, 'BUILD')
    except Exception:
        initial_balance_build = None

    # Gán cho global balance
    global current_balance, current_balance_world, current_balance_usdt
    current_balance = show_wallet(headers, 'BUILD')
    current_balance_world = show_wallet(headers, 'WORLD')
    current_balance_usdt = show_wallet(headers, 'USDT')

    console.print("[cyan]Chọn asset:[/]")
    console.print("1. BUILD")
    console.print("2. WORLD")
    console.print("3. USDT")
    choice = safe_input("Chọn (1/2/3): ", default="1")

    if choice == "2":
        asset_mode = "WORLD"
    elif choice == "3":
        asset_mode = "USDT"
    else:
        asset_mode = "BUILD"
    
    preload_history(headers, asset_mode=asset_mode)  # hoặc "BUILD"

    # 🔹 Thêm phần này: hỏi debug + chế độ chọn phòng
    prompt_common_settings()

    # 🔹 Sau đó mới tới chọn chế độ chơi
    console.print(Rule("[bold cyan]CHỌN CHẾ ĐỘ[/]"))
    console.print("[green]1. Martingale (gấp cược)[/]")
    console.print("[yellow]2. All-in (10 ván)[/]")
    console.print("[blue]3. Chỉ thống kê (không cược)[/]")

    choice = safe_input("Chọn chế độ (1/2/3): ", default="1")

    global run_mode, current_bet, lose_streak
    if choice == "1":
        run_mode = MODE_MARTINGALE
        prompt_martingale_settings()
        current_bet = base_bet   # tiền cược ban đầu
        lose_streak = 0
    elif choice == "2":
        run_mode = MODE_ALLIN
        init_allin_settings()
    else:
        run_mode = MODE_STATS_ONLY
        console.print("[cyan]Chế độ thống kê: KHÔNG tự đặt cược.[/]")

    # ✅ Chạy monitor + hiển thị bảng UI
    threading.Thread(target=monitor_loop, daemon=True).start()
    with Live(build_layout(), refresh_per_second=4, screen=True) as live:
        def refresher():
            while True:
                live.update(build_layout())
                time.sleep(0.8)
        threading.Thread(target=refresher, daemon=True).start()
        start_ws()
        
                    
if __name__ == "__main__":
    device_id = get_device_id()
    display_ascii_art()
    print(Fore.YELLOW + f"📌 Device ID: {device_id}\n")   # hiện ra nhưng không gây lỗi
    kiem_tra_quyen_truy_cap(device_id)
    main()
