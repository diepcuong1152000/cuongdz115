import requests
import time
import random
import json
import sys
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from colorama import Fore, init, Style

# --- Bổ sung thư viện ---
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.live import Live
from rich.progress import SpinnerColumn, BarColumn, TextColumn, Progress
from rich import box
from rich.prompt import Prompt
from rich.rule import Rule
# ---

import os, platform, uuid, hashlib, subprocess



init(autoreset=True)
console = Console()

# ------------------------- Configuration -------------------------
# Adjust these if needed
DEFAULT_MIN_BUILD = 100.0   # if BUILD minimum is known/required, adjust
GET_ISSUE_TIMEOUT = 15      # seconds for HTTP get calls timeout
PLACE_BET_TIMEOUT = 12      # seconds for POST timeout
WAIT_RESULT_MAX = 60        # seconds to wait for a result after placing bet
SLEEP_BET_BETWEEN = 12      # seconds between betting cycles
HISTORY_FETCH_COUNT = 500    # number of recent issues to show in history

# ------------------------- Helper / API functions -------------------------


SECRET = "MY_SECRET_SALT"

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
    except Exception:
        if mode == "mac":
            raw = str(uuid.getnode())
        elif mode == "cpu":
            raw = f"{platform.processor()}-{platform.machine()}"
        else:
            raw = f"{platform.node()}-{platform.system()}-{platform.release()}"

    device_id = "DEVICE-" + hashlib.md5(raw.encode()).hexdigest()[:15].upper()
    console.print(f"[cyan]📌 Device ID: [yellow]{device_id}")
    return device_id

def make_free_key(user_id):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    raw = today + SECRET + str(user_id)
    return hashlib.md5(raw.encode()).hexdigest()[:10].upper()

def load_vip_key(device_id):
    """Try to load VIP key list from a remote raw file (github/ghproxy). Return (key, expiry) or (None,None)."""
    try:
        url_key = "https://ghproxy.net/https://raw.githubusercontent.com/Cuongdz2828/pt/main/test/a.txt"
        r = requests.get(url_key, timeout=6)
        if r.status_code == 200:
            ds_key_raw = r.text.strip().splitlines()
            dev_local = device_id.replace("DEVICE-", "").strip().upper()
            for dong in ds_key_raw:
                parts = [p.strip() for p in dong.split("|")]
                if len(parts) >= 4:
                    device, key, _, ngay_hh = parts
                    dev_file = device.replace("DEVICE-", "").strip().upper()
                    if dev_file == dev_local:
                        return key, ngay_hh
    except Exception as e:
        console.print(f"[yellow]WARN tải VIP key thất bại: {e}")
    return None, None

def save_link(link, filename="link.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(link.strip())
    except Exception as e:
        console.print(f"[red]Lỗi lưu link: {e}")

def load_link(filename="link.txt"):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None
    return None

def prompt_key_flow(device_id):
    """Interactive flow: let user choose Free bypass or VIP key and validate."""
    console.print(Rule("[bold cyan]CHỌN LOẠI KEY[/]"))
    console.print("[green]1[/]. Key Free (vượt link)")
    console.print("[magenta]2[/]. Key VIP (nếu bạn có)\n")
    choice = Prompt.ask("Chọn (key)", default="1")

    if choice.strip() == "2":
        vip_key, ngay_hh = load_vip_key(device_id)
        if not vip_key:
            console.print("[red]Không tìm thấy key VIP cho device. Bạn có muốn thử Key Free thay thế? (y/N)")
            c = Prompt.ask("Chọn", choices=["y", "n"], default="y")
            if c.lower().startswith("y"):
                return prompt_key_flow(device_id)
            return "NONE", None

        console.print(f"[yellow]Key VIP có thể là: [magenta]{vip_key} (hạn {ngay_hh})")
        attempts = 3
        for i in range(attempts):
            entered = Prompt.ask("Nhập Key VIP:")
            if entered.strip() == vip_key:
                console.print("[green]✅ Key VIP hợp lệ.\n")
                link = Prompt.ask("Dán link game (phải có userId & secretKey)")
                save_link(link)
                return "VIP", link
            else:
                console.print("[red]Key sai, thử lại.")
        console.print("[red]Sai quá số lần. Hủy.")
        return "NONE", None

    else:
        free_links = [
            "https://link4m.com/Bhdv5",
            "https://link4m.com/LvWUEq5F",
            "https://link4m.com/Bhbv5",
            "https://link4m.com/LvWUEq5F",
        ]
        random_link = random.choice(free_links)
        console.print(Panel(f"Vui lòng mở link rút gọn 4m để lấy key:\n\n{random_link}", title="Key Free", border_style="cyan"))
        console.print("Sau khi vượt qua (mở link), trang sẽ cho bạn USER ID. Hãy nhập USER ID vào bên dưới.")
        user_id = Prompt.ask("Nhập User ID (copy từ web):")
        free_key = make_free_key(user_id)
        attempts = 3
        for i in range(attempts):
            key_nhap = Prompt.ask("Nhập Key Free:")
            if key_nhap.strip().upper() == free_key:
                console.print(f"[green]✅ Key Free đúng! (còn hiệu lực trong ngày)\n")
                link = Prompt.ask("Dán link game (phải có userId & secretKey)")
                save_link(link)
                return "FREE", link
            else:
                console.print("[red]Key Free sai, thử lại...")
        console.print("[red]Không nhập được Key Free. Hủy.")
        return "NONE", None


def make_full_headers(user_id, secret_key):
    """Return headers similar to winhas.py to avoid transfer errors."""
    return {
        'accept': '*/*',
        'country-code': 'vn',
        'origin': 'https://winhash.io',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'user-id': str(user_id),
        'user-login': 'login_v2',
        'user-secret-key': str(secret_key),
        'xb-language': 'vi-VN',
        'Content-Type': 'application/json',
    }

def get_hourly_issue_list(headers, session=None):
    """Call hourly_issue_list and return list of issues (may include lucky_codes if finished)."""
    s = session or requests
    try:
        params = {'ts': int(time.time())}
        r = s.get('https://api.winhash.net/lucky_game/hourly_issue_list',
                  params=params, headers=headers, timeout=GET_ISSUE_TIMEOUT)
        if r.status_code == 200:
            d = r.json()
            if d.get('code') == 0:
                return d.get('data', [])
            else:
                # non-zero code, return empty but print message
                console.print(f"[yellow][WARN] API returned code {d.get('code')}: {d.get('msg')}")
        else:
            console.print(f"[yellow][WARN] HTTP {r.status_code} from hourly_issue_list")
    except Exception as e:
        console.print(f"[red][ERROR] get_hourly_issue_list: {e}")
    return []

def find_current_issue_id(headers, session=None):
    issues = get_hourly_issue_list(headers, session=session)
    if not issues:
        return None
    current_time = int(time.time())
    closest = None
    mindiff = float('inf')
    for it in issues:
        start_time = it.get('start_time', 0)
        diff = abs(current_time - start_time)
        if diff < mindiff:
            mindiff = diff
            closest = it
    if closest:
        # The API in winhas.py used closest.issue_id + 1 logic; keep the same.
        return closest.get('issue_id') + 1
    return None

def place_bet_winhash(headers, asset, issue_id, bet_type, amount, session=None):
    """Place bet using /lucky_game/v2/create_order"""
    s = session or requests
    bet_ids = {'small': 70309, 'big': 71218, 'draw': 71011}
    if bet_type not in bet_ids:
        return False, "Loại cược không hợp lệ"
    payload = {
        "game_id": 1,
        "issue_id": issue_id,
        "items": [{"id": bet_ids[bet_type], "amount": str(amount), "asset": asset}]
    }
    try:
        r = s.post('https://api.winhash.net/lucky_game/v2/create_order',
                   headers=headers, json=payload, timeout=PLACE_BET_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if data.get('code') == 0:
                return True, data.get('msg', 'Thành công')
            else:
                # Return API message for clarity (e.g. "Failed to transfer assets (token)")
                return False, data.get('msg', 'API error')
        else:
            return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def wait_for_result(headers, issue_id, session=None, max_wait=WAIT_RESULT_MAX):
    """Poll hourly_issue_list until target issue_id contains lucky_codes or timeout."""
    s = session or requests
    start_time = time.time()
    while time.time() - start_time < max_wait:
        issues = get_hourly_issue_list(headers, session=s)
        for it in issues:
            if it.get('issue_id') == issue_id:
                lc = it.get('lucky_codes', [])
                if lc and isinstance(lc, list) and len(lc) == 3:
                    total = sum(lc)
                    return total, lc
        time.sleep(2)
    return None, None

def check_bet_result(bet_type, total):
    if bet_type == 'small':
        return 3 <= total <= 9
    elif bet_type == 'big':
        return 12 <= total <= 18
    elif bet_type == 'draw':
        return 10 <= total <= 11
    return False


def show_history(headers, count=HISTORY_FETCH_COUNT, session=None):
    """In lịch sử count kỳ gần nhất (mặc định 500)."""
    issues = get_hourly_issue_list(headers, session=session)
    if not issues:
        console.print(f"[cyan]\\n=== LỊCH SỬ {min(count, len(issues))} KỲ GẦN NHẤT ===")
        return
    console.print(f"[cyan]=== LỊCH SỬ {min(count, len(issues))} KỲ GẦN NHẤT ===")
    shown = 0
    for it in issues[:count]:
        issue_id = it.get('issue_id')
        start_ts = it.get('start_time', 0)
        start_dt = datetime.fromtimestamp(start_ts).strftime("%Y-%m-%d %H:%M:%S") if start_ts else "-"
        lc = it.get('lucky_codes')
        if lc and isinstance(lc, list) and len(lc) == 3:
            total = sum(lc)
            console.print(f"[green]#{issue_id} | {start_dt} | {lc} = {total}")
        else:
            console.print(f"[white]#{issue_id} | {start_dt} | (chưa có kết quả)")
        shown += 1
        if shown >= count:
            break
    console.print("[cyan]=== KẾT THÚC LỊCH SỬ ===\\n")


# --- Các hàm giao diện từ demo.py ---
APP_NAME = "LOTO"
VERSION = "v1.0"

def make_banner():
    banner_lines = [
        r"██╗      ██████╗ ████████╗ ██████╗ ",
        r"██║     ██╔═══██╗╚══██╔══╝██╔═══██╗",
        r"██║     ██║   ██║   ██║   ██║   ██║",
        r"██║     ██║   ██║   ██║   ██║   ██║",
        r"███████╗╚██████╔╝   ██║   ╚██████╔╝",
        r"╚══════╝ ╚═════╝    ╚═╝    ╚═════╝ ",
        r"                                   ",
    ]
    text = Text()
    colors = ["#ff00ff", "#ff33cc", "#cc00ff", "#8800ff", "#5500ff", "#00ffff"]
    for i, line in enumerate(banner_lines):
        text.append(line + "\n", style=f"bold {colors[i % len(colors)]}")
    subtitle = Text(f"{APP_NAME} {VERSION}\n", style="bold bright_cyan")
    text.append(subtitle)
    return Panel(Align.center(text), box=box.ROUNDED, padding=(1, 2), border_style="magenta")

def fancy_loader(seconds=2.5):
    progress = Progress(
        SpinnerColumn(style="bold magenta"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    )
    task = progress.add_task("[bold cyan]Đang Vào Tool...", total=100)

    with Live(Align.center(Panel(progress, title="Loading...", border_style="magenta")), refresh_per_second=10, console=console):
        while not progress.finished:
            progress.update(task, advance=1)
            time.sleep(seconds / 100)

def make_menu(selected_index=None):
    table = Table.grid(padding=(0, 2))
    table.add_column("arrow", width=3, justify="right")
    table.add_column("prefix", width=5, justify="center")
    table.add_column("command", justify="left")
    table.add_column("desc", justify="left")

    commands = [
        ("TOOL AUTO CƯỢC WINHASH", ""),
        ("nhập exit", "Thoát Tool"),
    ]

    for idx, (cmd, desc) in enumerate(commands):
        pointer = "➜" if selected_index == idx else " "
        prefix = "[⤓]"
        style_cmd = "bold magenta" if selected_index == idx else "bold cyan"
        table.add_row(pointer, prefix, Text(cmd, style=style_cmd), Text(desc, style="bright_black"))

    panel = Panel(table, title="Menu chức năng", subtitle="[red]!! NHẤN CTRL+C ĐỂ THOÁT !!", border_style="bright_magenta")
    return panel
# ---

def get_wallet_balance(headers, session=None):
    """Attempt to fetch wallet via user.regist endpoint used in winhas.py (best-effort)."""
    s = session or requests
    try:
        params = {'is_cwallet': '1', 'is_mission_setting': 'true', 'version': '', 'time': str(int(time.time() * 1000))}
        r = s.get('https://user.3games.io/user/regist', params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            d = r.json()
            if d.get('code') == 200:
                c = d.get('data', {}).get('cwallet', {})
                return {
                    'BUILD': c.get('ctoken_contribute', 0),
                    'USDT': c.get('ctoken_kusdt', 0),
                    'XWORLD': c.get('ctoken_kther', 0),
                }
    except Exception:
        pass
    return {'BUILD': 0, 'USDT': 0, 'XWORLD': 0}

# ------------------------- Bot loop -------------------------

def run_bot_loop(headers, asset, bet_amount, mode="random", fixed_choice="big", show_hist_every=0):
    """
    mode: "random" or "fixed"
    fixed_choice: 'small'/'big'/'draw' when mode == 'fixed'
    show_hist_every: show history every N bets (0 = never)
    """
    last_issue = None
    bet_count = 0
    session = requests.Session()

    console.print("[cyan][INFO] Bắt đầu bot. Nhấn Ctrl+C để dừng.")

    while True:
        try:
            issue_id = find_current_issue_id(headers, session=session)
            if not issue_id:
                console.print("[yellow][WARN] Không tìm được issue_id, thử lại sau 5s...")
                time.sleep(5)
                continue
            if issue_id == last_issue:
                # chưa tới kỳ mới
                time.sleep(2)
                continue

            last_issue = issue_id
            bet_count += 1

            # choose bet type
            if mode == "fixed":
                bet_type = fixed_choice
            else:
                bet_type = random.choice(["small", "big", "draw"])

            # place bet
            success, msg = place_bet_winhash(headers, asset, issue_id, bet_type, bet_amount, session=session)
            if not success:
                console.print(f"[red]❌ Lỗi đặt cược (kì {issue_id}): {msg}")
                # common API messages: "bet amount is too small", "Failed to transfer assets (token)", etc.
                # If it's small, try auto-upgrade for BUILD
                if "too small" in str(msg).lower() and asset.upper() == "BUILD":
                    console.print(f"[yellow][AUTO] Tăng tiền cược lên {DEFAULT_MIN_BUILD} BUILD và thử lại...")
                    bet_amount = max(bet_amount, DEFAULT_MIN_BUILD)
                    success2, msg2 = place_bet_winhash(headers, asset, issue_id, bet_type, bet_amount, session=session)
                    if success2:
                        console.print(f"[green]✅ (THỬ LẠI) Đặt {bet_amount} {asset} cửa {bet_type} (kì {issue_id})")
                    else:
                        console.print(f"[red]❌ (THỬ LẠI) Lỗi đặt cược: {msg2}")
                # wait longer on transfer error
                time.sleep(8)
                continue

            console.print(f"[green]✅ Đã đặt {bet_amount} {asset} cửa {bet_type} (kì {issue_id})")

            # wait for result
            total, lucky_codes = wait_for_result(headers, issue_id, session=session, max_wait=WAIT_RESULT_MAX)
            if total is None:
                console.print(f"[yellow]⚠️ Không có kết quả cho kì {issue_id} sau {WAIT_RESULT_MAX}s")
            else:
                if check_bet_result(bet_type, total):
                    console.print(f"[green]🎉 THẮNG! Kì {issue_id}: {lucky_codes} = {total}")
                else:
                    console.print(f"[red]😞 THUA! Kì {issue_id}: {lucky_codes} = {total}")

            # luôn hiển thị 500 kỳ gần nhất
            show_history(headers, count=HISTORY_FETCH_COUNT, session=session)

            # optionally show history
            if show_hist_every and (bet_count % show_hist_every == 0):
                show_history(headers, count=HISTORY_FETCH_COUNT, session=session)

            # small sleep between cycles to avoid being too aggressive
            time.sleep(SLEEP_BET_BETWEEN)

        except KeyboardInterrupt:
            console.print("\n[cyan][INFO] Người dùng dừng bot bằng Ctrl+C. Kết thúc.")
            break
        except Exception as e:
            console.print(f"[red][ERROR] Vòng lặp bot: {e}")
            time.sleep(5)

# ------------------------- CLI -------------------------

def main():
    console.clear()
    console.print(make_banner())
    fancy_loader(seconds=1.2)
    console.clear()
    console.print(make_banner())
    console.print(make_menu())

    # --- lấy device id ---
    device_id = get_device_id()

    # --- chọn key Free hoặc VIP ---
    mode, saved_link = prompt_key_flow(device_id)
    if mode == "NONE":
        console.print("[red]Không có key hợp lệ. Thoát.")
        sys.exit(1)

    # --- lấy link (userId & secretKey) ---
    link = saved_link or load_link()
    if not link:
        link = Prompt.ask("Dán link game (phải có userId & secretKey)")
        save_link(link)

    try:
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        user_id = params.get("userId", [""])[0]
        secret_key = params.get("secretKey", [""])[0]
    except Exception:
        user_id = secret_key = None

    if not user_id or not secret_key:
        console.print("[red]Link không hợp lệ hoặc thiếu userId/secretKey. Vui lòng chạy lại và nhập link hợp lệ.")
        sys.exit(1)

    headers = make_full_headers(user_id, secret_key)

    # --- chọn loại tài sản ---
    console.print("\n[cyan]Chọn tài sản:")
    console.print("1. BUILD\n2. USDT\n3. XWORLD\n")
    choice = Prompt.ask("[bold cyan]Chọn", choices=["1", "2", "3"], default="1")
    asset = {"1": "BUILD", "2": "USDT", "3": "XWORLD"}.get(choice, "BUILD")

    # --- nhập số tiền cược ---
    bet_amount = 0.0
    while True:
        bet_amount_str = Prompt.ask("[bold cyan]Nhập số tiền cược ban đầu (ví dụ 100)")
        try:
            bet_amount = float(bet_amount_str)
            break
        except ValueError:
            console.print("[red]Số tiền không hợp lệ. Vui lòng nhập một số.[/]")

    # --- chọn chế độ cược ---
    console.print("\n[cyan]Chọn chế độ cược:")
    console.print("1. Random (mỗi ván random small/big/draw)\n2. Fixed (luôn cược 1 cửa bạn chọn)\n")
    mode_choice = Prompt.ask("[bold cyan]Chọn", choices=["1", "2"], default="1")
    if mode_choice == "2":
        fixed_choice = Prompt.ask("[bold cyan]Chọn cửa cố định (small/big/draw)", choices=["small", "big", "draw"], default="big")
        mode_run = "fixed"
    else:
        fixed_choice = "big"
        mode_run = "random"

    # --- hiển thị lịch sử định kỳ ---
    show_hist_every = 0
    try:
        show_hist_str = Prompt.ask("[bold cyan]Mỗi N ván hiển thị lịch sử (0=không)", default="0")
        show_hist_every = int(show_hist_str)
    except Exception:
        show_hist_every = 0

    # --- hiển thị cấu hình ---
    config_text = Text()
    config_text.append(f"User: ", style="cyan")
    config_text.append(f"{user_id}\n", style="yellow")
    config_text.append(f"Asset: ", style="cyan")
    config_text.append(f"{asset}\n", style="yellow")
    config_text.append(f"Bet: ", style="cyan")
    config_text.append(f"{bet_amount}\n", style="yellow")
    config_text.append(f"Mode: ", style="cyan")
    config_text.append(f"{mode_run} ({fixed_choice if mode_run=='fixed' else 'random'})", style="yellow")

    config_panel = Panel(config_text, title="Cấu hình", border_style="magenta", expand=False)
    console.print(config_panel)

    # --- chạy bot ---
    run_bot_loop(headers, asset, bet_amount, mode=mode_run, fixed_choice=fixed_choice, show_hist_every=show_hist_every)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Đã hủy bằng Ctrl+C[/]")
        sys.exit(0)