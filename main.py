from dotenv import load_dotenv
from app.service.git import check_for_updates
load_dotenv()

import sys, json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich import box
import time

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

# Initialize Rich console
console = Console()

class AMIFIStore:
    def __init__(self):
        self.width = 70
        self.version = "2.0.0"
        
    def show_banner(self):
        """Menampilkan banner AMIFI Store yang modern"""
        banner_text = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    █████╗ ███╗   ███╗██╗███████╗██╗     ███████╗████████╗   ║
║   ██╔══██╗████╗ ████║██║██╔════╝██║     ██╔════╝╚══██╔══╝   ║
║   ███████║██╔████╔██║██║█████╗  ██║     █████╗     ██║      ║
║   ██╔══██║██║╚██╔╝██║██║██╔══╝  ██║     ██╔══╝     ██║      ║
║   ██║  ██║██║ ╚═╝ ██║██║███████╗███████╗███████╗   ██║      ║
║   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝      ║
║                                                              ║
║                   📱 STORE MANAGEMENT SYSTEM 📱             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        console.print(banner_text, style="bold cyan")
        console.print(f"🚀 AMIFI Store v{self.version} - Modern Package Management", style="bold green")
        console.print()

    def show_user_profile(self, profile):
        """Menampilkan profil user dengan tampilan modern"""
        expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
        
        # Create profile table
        profile_table = Table(show_header=False, box=box.ROUNDED, style="blue")
        profile_table.add_column("Field", style="bold cyan")
        profile_table.add_column("Value", style="white")
        
        profile_table.add_row("📱 Nomor", profile['number'])
        profile_table.add_row("🎫 Type", profile['subscription_type'])
        profile_table.add_row("💰 Pulsa", f"Rp {profile['balance']:,}")
        profile_table.add_row("📅 Aktif Sampai", expired_at_dt)
        profile_table.add_row("⭐ Info Points", profile['point_info'])
        
        console.print(Panel(profile_table, title="👤 User Profile", title_align="left", style="bold blue"))

    def show_main_menu(self, profile):
        """Menampilkan menu utama dengan tampilan modern"""
        clear_screen()
        self.show_banner()
        self.show_user_profile(profile)
        
        # Create menu options
        menu_table = Table.grid(padding=1)
        menu_table.add_column("No", style="bold yellow", width=4)
        menu_table.add_column("Menu", style="white", width=50)
        menu_table.add_column("Icon", style="green", width=3)
        
        menu_options = [
            ("1", "Login/Ganti akun", "🔐"),
            ("2", "Lihat Paket Saya", "📦"),
            ("3", "Beli Paket 🔥 HOT", "🔥"),
            ("4", "Beli Paket 🔥 HOT-2", "🔥"),
            ("5", "Beli Paket Berdasarkan Option Code", "🔢"),
            ("6", "Beli Paket Berdasarkan Family Code", "👨‍👩‍👧‍👦"),
            ("7", "Beli Semua Paket di Family Code (loop)", "🔄"),
            ("8", "Riwayat Transaksi", "📋"),
            ("9", "Family Plan/Akrab Organizer", "👪"),
            ("10", "Circle", "🔵"),
            ("11", "Store Segments", "🏪"),
            ("12", "Store Family List", "📑"),
            ("13", "Store Packages", "📦"),
            ("14", "Redemables", "🎁"),
            ("R", "Register", "📝"),
            ("N", "Notifikasi", "🔔"),
            ("V", "Validate msisdn", "✅"),
            ("00", "Bookmark Paket", "📌"),
            ("99", "Tutup aplikasi", "🚪"),
        ]
        
        for option in menu_options:
            menu_table.add_row(option[0], option[1], option[2])
        
        console.print(Panel(menu_table, title="🎯 Main Menu", title_align="left", style="bold green"))
        console.print()

    def show_loading(self, message="Loading..."):
        """Menampilkan animasi loading"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=message, total=None)
            time.sleep(1)

    def get_menu_choice(self):
        """Mendapatkan pilihan menu dengan validasi"""
        return Prompt.ask(
            "🎮 Pilih menu",
            choices=[
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                '11', '12', '13', '14', 'r', 'n', 'v', '00', '99', 's'
            ],
            show_choices=False
        )

    def handle_option_code_purchase(self, active_user):
        """Handle pembelian berdasarkan option code"""
        option_code = Prompt.ask("🔢 Masukkan option code", default="").strip()
        if option_code.lower() == '99':
            return
        
        if not option_code:
            console.print("❌ Option code tidak boleh kosong!", style="bold red")
            pause()
            return
            
        self.show_loading("Mengambil detail paket...")
        show_package_details(
            AuthInstance.api_key,
            active_user["tokens"],
            option_code,
            False
        )

    def handle_family_code_purchase(self, active_user):
        """Handle pembelian berdasarkan family code"""
        family_code = Prompt.ask("👨‍👩‍👧‍👦 Masukkan family code", default="").strip()
        if family_code.lower() == '99':
            return
            
        if not family_code:
            console.print("❌ Family code tidak boleh kosong!", style="bold red")
            pause()
            return
            
        self.show_loading("Mengambil paket berdasarkan family...")
        get_packages_by_family(family_code)

    def handle_bulk_family_purchase(self):
        """Handle pembelian massal berdasarkan family code"""
        family_code = Prompt.ask("🔄 Masukkan family code untuk pembelian massal", default="").strip()
        if family_code.lower() == '99':
            return
            
        if not family_code:
            console.print("❌ Family code tidak boleh kosong!", style="bold red")
            pause()
            return

        start_from_option = Prompt.ask(
            "🔢 Mulai pembelian dari option nomor", 
            default="1"
        )
        try:
            start_from_option = int(start_from_option)
        except ValueError:
            start_from_option = 1

        use_decoy = Confirm.ask("🎯 Gunakan decoy package?")
        pause_on_success = Confirm.ask("⏸️  Pause pada setiap pembelian berhasil?")
        
        delay_seconds = Prompt.ask(
            "⏱️  Delay detik antara pembelian", 
            default="0"
        )
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

    def handle_registration(self):
        """Handle proses registrasi"""
        console.print(Panel("📝 Registration Process", style="bold yellow"))
        msisdn = Prompt.ask("📱 Masukkan MSISDN (628xxxx)")
        nik = Prompt.ask("🆔 Masukkan NIK", password=True)
        kk = Prompt.ask("🏠 Masukkan KK", password=True)
        
        self.show_loading("Memproses registrasi...")
        res = dukcapil(AuthInstance.api_key, msisdn, kk, nik)
        console.print(json.dumps(res, indent=2))
        pause()

    def handle_validation(self, active_user):
        """Handle validasi MSISDN"""
        msisdn = Prompt.ask("✅ Masukkan MSISDN untuk divalidasi (628xxxx)")
        self.show_loading("Memvalidasi MSISDN...")
        res = validate_msisdn(AuthInstance.api_key, active_user["tokens"], msisdn)
        console.print(json.dumps(res, indent=2))
        pause()

    def handle_store_menus(self, profile):
        """Handle menu store dengan enterprise option"""
        is_enterprise = Confirm.ask("🏢 Apakah enterprise store?")
        return is_enterprise

    def run(self):
        """Method utama untuk menjalankan aplikasi"""
        try:
            # Check for updates
            console.print("🔍 Checking for updates...", style="bold yellow")
            need_update = check_for_updates()
            if need_update:
                console.print("⚠️  Update tersedia! Silakan perbarui aplikasi.", style="bold yellow")
                pause()

            while True:
                active_user = AuthInstance.get_active_user()

                if active_user is not None:
                    # Get user balance and info
                    self.show_loading("Mengambil info user...")
                    balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
                    balance_remaining = balance.get("remaining")
                    balance_expired_at = balance.get("expired_at")
                    
                    point_info = "Points: N/A | Tier: N/A"
                    
                    if active_user["subscription_type"] == "PREPAID":
                        tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                        tier = tiering_data.get("tier", 0)
                        current_point = tiering_data.get("current_point", 0)
                        point_info = f"⭐ Points: {current_point} | 🏆 Tier: {tier}"
                    
                    profile = {
                        "number": active_user["number"],
                        "subscriber_id": active_user["subscriber_id"],
                        "subscription_type": active_user["subscription_type"],
                        "balance": balance_remaining,
                        "balance_expired_at": balance_expired_at,
                        "point_info": point_info
                    }

                    self.show_main_menu(profile)
                    choice = self.get_menu_choice()

                    # Menu handlers
                    if choice.lower() == "t":
                        pause()
                    elif choice == "1":
                        selected_user_number = show_account_menu()
                        if selected_user_number:
                            AuthInstance.set_active_user(selected_user_number)
                        else:
                            console.print("❌ Tidak ada user yang dipilih atau gagal memuat user.", style="bold red")
                    elif choice == "2":
                        fetch_my_packages()
                    elif choice == "3":
                        show_hot_menu()
                    elif choice == "4":
                        show_hot_menu2()
                    elif choice == "5":
                        self.handle_option_code_purchase(active_user)
                    elif choice == "6":
                        self.handle_family_code_purchase(active_user)
                    elif choice == "7":
                        self.handle_bulk_family_purchase()
                    elif choice == "8":
                        show_transaction_history(AuthInstance.api_key, active_user["tokens"])
                    elif choice == "9":
                        show_family_info(AuthInstance.api_key, active_user["tokens"])
                    elif choice == "10":
                        show_circle_info(AuthInstance.api_key, active_user["tokens"])
                    elif choice == "11":
                        is_enterprise = self.handle_store_menus(profile)
                        show_store_segments_menu(is_enterprise)
                    elif choice == "12":
                        is_enterprise = self.handle_store_menus(profile)
                        show_family_list_menu(profile['subscription_type'], is_enterprise)
                    elif choice == "13":
                        is_enterprise = self.handle_store_menus(profile)
                        show_store_packages_menu(profile['subscription_type'], is_enterprise)
                    elif choice == "14":
                        is_enterprise = self.handle_store_menus(profile)
                        show_redeemables_menu(is_enterprise)
                    elif choice == "00":
                        show_bookmark_menu()
                    elif choice == "99":
                        console.print("👋 Terima kasih telah menggunakan AMIFI Store!", style="bold green")
                        sys.exit(0)
                    elif choice.lower() == "r":
                        self.handle_registration()
                    elif choice.lower() == "v":
                        self.handle_validation(active_user)
                    elif choice.lower() == "n":
                        show_notification_menu()
                    elif choice == "s":
                        enter_sentry_mode()
                    else:
                        console.print("❌ Pilihan tidak valid. Silakan coba lagi.", style="bold red")
                        pause()
                else:
                    # Not logged in
                    console.print("🔐 Silakan login terlebih dahulu...", style="bold yellow")
                    selected_user_number = show_account_menu()
                    if selected_user_number:
                        AuthInstance.set_active_user(selected_user_number)
                        console.print("✅ Login berhasil!", style="bold green")
                    else:
                        console.print("❌ Gagal memuat user.", style="bold red")

        except KeyboardInterrupt:
            console.print("\n👋 Aplikasi dihentikan oleh user. Sampai jumpa!", style="bold yellow")
        except Exception as e:
            console.print(f"❌ Terjadi error: {e}", style="bold red")

def main():
    """Fungsi utama"""
    app = AMIFIStore()
    app.run()

if __name__ == "__main__":
    main()
