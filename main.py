from dotenv import load_dotenv
from app.service.git import check_for_updates
load_dotenv()

import sys, json
from datetime import datetime
from app.menus.util import clear_screen, pause
from app.client.engsel import (
    get_balance,
    get_tiering_info,
)
from app.client.famplan import validate_msisdn
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.client.registration import dukcapil

WIDTH = 55

def show_main_menu(profile):
    clear_screen()
    print("╔" + "═" * (WIDTH-2) + "╗")
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    print(f"║ {'AMIFI STORE - MODERN':^{WIDTH-2}} ║")
    print("╠" + "═" * (WIDTH-2) + "╣")
    print(f"║ 📱 Nomor: {profile['number']:<{WIDTH-15}} ║")
    print(f"║ 🎫 Type: {profile['subscription_type']:<{WIDTH-14}} ║")
    print(f"║ 💰 Pulsa: Rp {profile['balance']:<{WIDTH-20}} ║")
    print(f"║ 📅 Aktif sampai: {expired_at_dt:<{WIDTH-25}} ║")
    print(f"║ ⭐ {profile['point_info']:<{WIDTH-5}} ║")
    print("╠" + "═" * (WIDTH-2) + "╣")
    print("║ 🎯 MENU UTAMA:".ljust(WIDTH-1) + "║")
    print("╠" + "─" * (WIDTH-2) + "╣")
    print("║ 1. 🔐 Login/Ganti akun".ljust(WIDTH-1) + "║")
    print("║ 2. 📦 Lihat Paket Saya".ljust(WIDTH-1) + "║")
    print("║ 3. 🔥 Beli Paket HOT".ljust(WIDTH-1) + "║")
    print("║ 4. 🔥 Beli Paket HOT-2".ljust(WIDTH-1) + "║")
    print("║ 5. 🔢 Beli Paket Berdasarkan Option Code".ljust(WIDTH-1) + "║")
    print("║ 6. 👨‍👩‍👧‍👦 Beli Paket Berdasarkan Family Code".ljust(WIDTH-1) + "║")
    print("║ 7. 🔄 Beli Semua Paket di Family Code (loop)".ljust(WIDTH-1) + "║")
    print("║ 8. 📋 Riwayat Transaksi".ljust(WIDTH-1) + "║")
    print("║ 9. 👪 Family Plan/Akrab Organizer".ljust(WIDTH-1) + "║")
    print("║ 10. 🔵 Circle".ljust(WIDTH-1) + "║")
    print("║ 11. 🏪 Store Segments".ljust(WIDTH-1) + "║")
    print("║ 12. 📑 Store Family List".ljust(WIDTH-1) + "║")
    print("║ 13. 📦 Store Packages".ljust(WIDTH-1) + "║")
    print("║ 14. 🎁 Redemables".ljust(WIDTH-1) + "║")
    print("║ R. 📝 Register".ljust(WIDTH-1) + "║")
    print("║ N. 🔔 Notifikasi".ljust(WIDTH-1) + "║")
    print("║ V. ✅ Validate msisdn".ljust(WIDTH-1) + "║")
    print("║ 00. 📌 Bookmark Paket".ljust(WIDTH-1) + "║")
    print("║ 99. 🚪 Tutup aplikasi".ljust(WIDTH-1) + "║")
    print("╚" + "═" * (WIDTH-2) + "╝")
    print()

def show_loading(message="Loading..."):
    """Simple loading animation"""
    import time
    for i in range(3):
        print(f"\r{message}{'.' * (i+1)}", end="", flush=True)
        time.sleep(0.3)
    print("\r" + " " * (len(message) + 3) + "\r", end="", flush=True)

def main():
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            balance_remaining = balance.get("remaining")
            balance_expired_at = balance.get("expired_at")
            
            point_info = "Points: N/A | Tier: N/A"
            
            if active_user["subscription_type"] == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                tier = tiering_data.get("tier", 0)
                current_point = tiering_data.get("current_point", 0)
                point_info = f"Points: {current_point} | Tier: {tier}"
            
            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance_remaining,
                "balance_expired_at": balance_expired_at,
                "point_info": point_info
            }

            show_main_menu(profile)

            choice = input("🎮 Pilih menu: ")
            # Testing shortcuts
            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print("❌ No user selected or failed to load user.")
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                option_code = input("🔢 Enter option code (or '99' to cancel): ")
                if option_code == "99":
                    continue
                show_loading("Mengambil detail paket...")
                show_package_details(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    option_code,
                    False
                )
            elif choice == "6":
                family_code = input("👨‍👩‍👧‍👦 Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue
                show_loading("Mengambil paket berdasarkan family...")
                get_packages_by_family(family_code)
            elif choice == "7":
                family_code = input("🔄 Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue

                start_from_option = input("🔢 Start purchasing from option number (default 1): ")
                try:
                    start_from_option = int(start_from_option)
                except ValueError:
                    start_from_option = 1

                use_decoy = input("🎯 Use decoy package? (y/n): ").lower() == 'y'
                pause_on_success = input("⏸️  Pause on each successful purchase? (y/n): ").lower() == 'y'
                delay_seconds = input("⏱️  Delay seconds between purchases (0 for no delay): ")
                try:
                    delay_seconds = int(delay_seconds)
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(
                    family_code,
                    use_decoy,
                    pause_on_success,
                    delay_seconds,
                    start_from_option
                )
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "11":
                input_11 = input("🏢 Is enterprise store? (y/n): ").lower()
                is_enterprise = input_11 == 'y'
                show_store_segments_menu(is_enterprise)
            elif choice == "12":
                input_12_1 = input("🏢 Is enterprise? (y/n): ").lower()
                is_enterprise = input_12_1 == 'y'
                show_family_list_menu(profile['subscription_type'], is_enterprise)
            elif choice == "13":
                input_13_1 = input("🏢 Is enterprise? (y/n): ").lower()
                is_enterprise = input_13_1 == 'y'
                
                show_store_packages_menu(profile['subscription_type'], is_enterprise)
            elif choice == "14":
                input_14_1 = input("🏢 Is enterprise? (y/n): ").lower()
                is_enterprise = input_14_1 == 'y'
                
                show_redeemables_menu(is_enterprise)
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                print("👋 Exiting the application.")
                sys.exit(0)
            elif choice.lower() == "r":
                msisdn = input("📱 Enter msisdn (628xxxx): ")
                nik = input("🆔 Enter NIK: ")
                kk = input("🏠 Enter KK: ")
                
                show_loading("Memproses registrasi...")
                res = dukcapil(
                    AuthInstance.api_key,
                    msisdn,
                    kk,
                    nik,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "v":
                msisdn = input("✅ Enter the msisdn to validate (628xxxx): ")
                show_loading("Memvalidasi MSISDN...")
                res = validate_msisdn(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    msisdn,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice == "s":
                enter_sentry_mode()
            else:
                print("❌ Invalid choice. Please try again.")
                pause()
        else:
            # Not logged in
            print("🔐 Silakan login terlebih dahulu...")
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
                print("✅ Login berhasil!")
            else:
                print("❌ No user selected or failed to load user.")

if __name__ == "__main__":
    try:
        print("🔍 Checking for updates...")
        need_update = check_for_updates()
        if need_update:
            print("⚠️  Update tersedia! Silakan perbarui aplikasi.")
            pause()

        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting the application.")
    # except Exception as e:
    #     print(f"❌ An error occurred: {e}")
