#!/usr/bin/env python3
# vt_full_winhash.py
# Full vt.py adapted to run Winhash (big/small/draw) + history viewer.
# Usage: python vt_full_winhash.py
# Paste the game link (contains userId & secretKey) when prompted.

import requests
import time
import random
import json
import sys
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from colorama import Fore, init, Style

init(autoreset=True)

# ------------------------- Configuration -------------------------
# Adjust these if needed
DEFAULT_MIN_BUILD = 100.0   # if BUILD minimum is known/required, adjust
GET_ISSUE_TIMEOUT = 15      # seconds for HTTP get calls timeout
PLACE_BET_TIMEOUT = 12      # seconds for POST timeout
WAIT_RESULT_MAX = 60        # seconds to wait for a result after placing bet
SLEEP_BET_BETWEEN = 12      # seconds between betting cycles
HISTORY_FETCH_COUNT = 20    # number of recent issues to show in history

# ------------------------- Helper / API functions -------------------------

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
                print(Fore.YELLOW + f"[WARN] API returned code {d.get('code')}: {d.get('msg')}")
        else:
            print(Fore.YELLOW + f"[WARN] HTTP {r.status_code} from hourly_issue_list")
    except Exception as e:
        print(Fore.RED + f"[ERROR] get_hourly_issue_list: {e}")
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
    """Print recent issues and their results (if available)."""
    issues = get_hourly_issue_list(headers, session=session)
    if not issues:
        print(Fore.YELLOW + "[INFO] Không lấy được lịch sử.")
        return
    print(Fore.CYAN + f"\n=== LỊCH SỬ {min(count, len(issues))} KỲ GẦN NHẤT ===")
    shown = 0
    for it in issues[:count]:
        issue_id = it.get('issue_id')
        start_ts = it.get('start_time', 0)
        start_dt = datetime.fromtimestamp(start_ts).strftime("%Y-%m-%d %H:%M:%S") if start_ts else "-"
        lc = it.get('lucky_codes')
        if lc and isinstance(lc, list) and len(lc) == 3:
            total = sum(lc)
            print(Fore.GREEN + f"#{issue_id} | {start_dt} | {lc} = {total}")
        else:
            print(Fore.WHITE + f"#{issue_id} | {start_dt} | (chưa có kết quả)")
        shown += 1
        if shown >= count:
            break
    print(Fore.CYAN + "=== KẾT THÚC LỊCH SỬ ===\n")

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

    print(Fore.CYAN + "[INFO] Bắt đầu bot. Nhấn Ctrl+C để dừng.")

    while True:
        try:
            issue_id = find_current_issue_id(headers, session=session)
            if not issue_id:
                print(Fore.YELLOW + "[WARN] Không tìm được issue_id, thử lại sau 5s...")
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
                print(Fore.RED + f"❌ Lỗi đặt cược (kì {issue_id}): {msg}")
                # common API messages: "bet amount is too small", "Failed to transfer assets (token)", etc.
                # If it's small, try auto-upgrade for BUILD
                if "too small" in str(msg).lower() and asset.upper() == "BUILD":
                    print(Fore.YELLOW + f"[AUTO] Tăng tiền cược lên {DEFAULT_MIN_BUILD} BUILD và thử lại...")
                    bet_amount = max(bet_amount, DEFAULT_MIN_BUILD)
                    success2, msg2 = place_bet_winhash(headers, asset, issue_id, bet_type, bet_amount, session=session)
                    if success2:
                        print(Fore.GREEN + f"✅ (THỬ LẠI) Đặt {bet_amount} {asset} cửa {bet_type} (kì {issue_id})")
                    else:
                        print(Fore.RED + f"❌ (THỬ LẠI) Lỗi đặt cược: {msg2}")
                # wait longer on transfer error
                time.sleep(8)
                continue

            print(Fore.GREEN + f"✅ Đã đặt {bet_amount} {asset} cửa {bet_type} (kì {issue_id})")

            # wait for result
            total, lucky_codes = wait_for_result(headers, issue_id, session=session, max_wait=WAIT_RESULT_MAX)
            if total is None:
                print(Fore.YELLOW + f"⚠️ Không có kết quả cho kì {issue_id} sau {WAIT_RESULT_MAX}s")
            else:
                if check_bet_result(bet_type, total):
                    print(Fore.GREEN + f"🎉 THẮNG! Kì {issue_id}: {lucky_codes} = {total}")
                else:
                    print(Fore.RED + f"😞 THUA! Kì {issue_id}: {lucky_codes} = {total}")

            # optionally show history
            if show_hist_every and (bet_count % show_hist_every == 0):
                show_history(headers, count=HISTORY_FETCH_COUNT, session=session)

            # small sleep between cycles to avoid being too aggressive
            time.sleep(SLEEP_BET_BETWEEN)

        except KeyboardInterrupt:
            print(Fore.CYAN + "\n[INFO] Người dùng dừng bot bằng Ctrl+C. Kết thúc.")
            break
        except Exception as e:
            print(Fore.RED + f"[ERROR] Vòng lặp bot: {e}")
            time.sleep(5)

# ------------------------- CLI -------------------------

def main():
    print(Fore.CYAN + "\n=== VT Full Winhash (big/small/draw) ===\n")
    link = input("Dán link game (phải có userId & secretKey): ").strip()
    if not link:
        print(Fore.RED + "Link rỗng, thoát.")
        sys.exit(1)

    parsed = urlparse(link)
    params = parse_qs(parsed.query)
    user_id = params.get("userId", [""])[0]
    secret_key = params.get("secretKey", [""])[0]
    if not user_id or not secret_key:
        print(Fore.RED + "Không tìm thấy userId hoặc secretKey trong link. Kiểm tra lại link.")
        sys.exit(1)

    headers = make_full_headers(user_id, secret_key)

    print("\nChọn tài sản (tiền):")
    print("1. BUILD\n2. USDT\n3. XWORLD\n")
    choice = input("Chọn (1-3, default 1): ").strip() or "1"
    asset = {"1": "BUILD", "2": "USDT", "3": "XWORLD"}.get(choice, "BUILD")

    try:
        bet_amount = float(input("Nhập số tiền cược ban đầu (ví dụ 100): ").strip() or "100")
    except Exception:
        bet_amount = 100.0

    print("\nChọn chế độ cược:")
    print("1. Random (mỗi ván random small/big/draw)\n2. Fixed (luôn cược 1 cửa bạn chọn)\n")
    mode_choice = input("Chọn (1-2, default 1): ").strip() or "1"
    if mode_choice == "2":
        fixed_choice = input("Chọn cửa cố định (small/big/draw): ").strip().lower() or "big"
        mode = "fixed"
    else:
        fixed_choice = "big"
        mode = "random"

    show_hist_every = 0
    try:
        x = input("Mỗi N ván hiển thị lịch sử (0=không, default 0): ").strip() or "0"
        show_hist_every = int(x)
    except Exception:
        show_hist_every = 0

    print(Fore.CYAN + "\nBắt đầu bot với cấu hình:")
    print(f"User: {user_id} | Asset: {asset} | Bet: {bet_amount} | Mode: {mode} ({fixed_choice if mode=='fixed' else 'random'})\n")

    # run
    run_bot_loop(headers, asset, bet_amount, mode=mode, fixed_choice=fixed_choice, show_hist_every=show_hist_every)

if __name__ == '__main__':
    main()
  
