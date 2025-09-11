
import requests
import time
import random
import os
import json
import threading
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich import box
from colorama import Fore, Style, init

init() #Tool By PhuocAn 
console = Console()
#Tool By PhuocAn 
# ======= TẠO HEADER =========
def tao_header(user_id, secret_key):
    return {
        'accept': '*/*',
        'accept-language': 'vi,en;q=0.9',
        'content-type': 'application/json',
        'country-code': 'vn',
        'origin': 'https://winhash.io',
        'priority': 'u=1, i',
        'referer': 'https://winhash.io/',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)',
        'user-login': 'login_v2',
        'user-id': user_id,
        'user-secret-key': secret_key,
        'xb-language': 'default',
    }

# ======= HIỂN THỊ KẾT QUẢ ========
def hien_thi_ket_qua_table(kq, ten=""):
    table = Table(title=f"🎰 {ten} - KẾT QUẢ", box=box.SQUARE, border_style="green" if kq['hit'] else "red")
    table.add_column("Thông tin", style="bold cyan")
    table.add_column("Giá trị", justify="right", style="bold")
    table.add_row("🎲 Kết quả", "[green]Thắng[/green]" if kq['hit'] else "[red]Thua[/red]")
    table.add_row("🎯 Số quay ra", f"{kq['num_result']}")
    table.add_row("🪙 Xu cược", f"{kq['bet_amount']}")
    table.add_row("💸 Lãi nhận", f"{kq['award_amount']} BUILD")
    table.add_row("📈 Tỷ lệ cược", f"{kq['odds']}x")
    console.print(table)

# ======= AUTO CƯỢC ==========
def auto_bet_loop(headers, ten="Tài khoản"):
    print(f"\n{Fore.CYAN}--- {ten} bắt đầu auto cược WinHash ---{Style.RESET_ALL}")
 #Tool By PhuocAn 
    try:
        initial_bet = float(input(f"{ten} 🪙 Số tiền cược ban đầu (BUILD): "))
        delay_min = int(input(f"{ten} ⏱️ Delay tối thiểu (giây): "))
        delay_max = int(input(f"{ten} ⏱️ Delay tối đa (giây): "))
        break_x2 = int(input(f"{ten} 🛑 Giới hạn số lần x2 khi thua (mặc định 5): ") or 5)
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi nhập: {e}{Style.RESET_ALL}")
        return

    odds = 1.3031
    num_left = 70.6
    num_right = 29.39
    bet_amount = initial_bet
    lose_streak = 0

    while True:
        is_less_than = random.choice([0, 1])
        json_data = {
            "odds": odds,
            "num_left": num_left,
            "num_right": num_right,
            "bet_amount": round(bet_amount, 2),
            "asset": "BUILD",
            "is_less_than": is_less_than
        }

        print(Fore.LIGHTYELLOW_EX + f"\n[{ten}] Gửi lệnh cược: {json_data}" + Style.RESET_ALL)

        try:
            res = requests.post('https://api.winhash.net/lucky_hash/create_order', headers=headers, json=json_data)
            if 'application/json' not in res.headers.get('Content-Type', ''):
                print(f"{Fore.RED}❌ API không trả JSON:\n{res.text}{Style.RESET_ALL}")
                continue

            data = res.json()
            if res.status_code == 200 and data.get('code') == 0:
                kq = data['data']
                hien_thi_ket_qua_table(kq, ten)
                if kq['hit']:
                    bet_amount = initial_bet
                    lose_streak = 0
                else:
                    lose_streak += 1
                    if lose_streak >= break_x2:
                        print(Fore.RED + f"{ten} 🛑 Thua {lose_streak} lần liên tiếp → Reset cược gốc!" + Style.RESET_ALL)
                        bet_amount = initial_bet
                        lose_streak = 0
                    else:
                        bet_amount *= 2
            else:
                print(f"{Fore.RED}❌ {ten} Lỗi cược: {data.get('msg')}{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ {ten} Lỗi kết nối: {e}{Style.RESET_ALL}")

        delay = random.randint(delay_min, delay_max)
        with Progress(transient=True) as progress:
            task = progress.add_task(f"[cyan]{ten} ⏳ Nghỉ {delay}s...", total=delay)
            for _ in range(delay):
                time.sleep(1)#Tool By PhuocAn 
                progress.update(task, advance=1)#Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn #Tool By PhuocAn 

# ======= CHẠY NHIỀU ACC ==========#Tool By PhuocAn 
def nhap_nhieu_tai_khoan():
    accs = []
    try:
        so_luong = int(input("🔢 Nhập số tài khoản muốn chạy: "))#Tool By PhuocAn 
        for i in range(so_luong):
            print(Fore.CYAN + f"\n=== Tài khoản #{i+1} ===" + Style.RESET_ALL)
            uid = input("➤ UID: ").strip()#Tool By PhuocAn 
            key = input("➤ Secret Key: ").strip()#Tool By PhuocAn 
            accs.append({#Tool By PhuocAn 
                "ten": f"Tài khoản {i+1}",
                "headers": tao_header(uid, key)
            })#Tool By PhuocAn 
        return accs#Tool By PhuocAn 
    except:#Tool By PhuocAn 
        print(Fore.RED + "⚠️ Lỗi nhập tài khoản" + Style.RESET_ALL)
        return []#Tool By PhuocAn 
#Tool By PhuocAn 
# ======= MAIN ==#Tool By PhuocAn ========
if __name__ == "__main__":
    chon = input("🤖 Bạn có muốn chạy đa luồng nhiều tài khoản? (y/n): ").strip().lower()
#Tool By PhuocAn 
    if chon == "y":#Tool By PhuocAn 
        acc_list = nhap_nhieu_tai_khoan()
        for acc in acc_list:
            t = threading.Thread(target=auto_bet_loop, args=(acc["headers"], acc["ten"]))
            t.start()
    else:
        uid = input("➤ Nhập UID Xworld: ").strip()#Tool By PhuocAn 
        key = input("➤ Nhập Secret Key: ").strip()#Tool By PhuocAn 
        headers = tao_header(uid, key)#Tool By PhuocAn 
        auto_bet_loop(headers, "Tài khoản 1")#Tool By PhuocAn 
