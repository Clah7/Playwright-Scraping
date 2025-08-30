from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")
STATE_FILE = os.path.join(DOWNLOAD_PATH, "state.json")

class StockbitDownloader:
    def __init__(self):
        self.p = None
        self.browser = None
        self.context = None
        self.page = None
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    def start_browser(self):
        """Buka browser dan context, pakai state jika ada"""
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False)

        if os.path.exists(STATE_FILE):
            print("State ditemukan, login otomatis...")
            self.context = self.browser.new_context(storage_state=STATE_FILE)
        else:
            print("State tidak ada, login manual dulu...")
            self.context = self.browser.new_context()
        
        self.page = self.context.new_page()

    def login_manual_if_needed(self):
        """Jika state belum ada, buka halaman login manual dan simpan state"""
        if not os.path.exists(STATE_FILE):
            self.page.goto("https://stockbit.com/#/login")
            print("Silakan login manual di browser, termasuk email verification.")
            input("Tekan Enter setelah login selesai...")
            self.context.storage_state(path=STATE_FILE)
            print(f"State berhasil disimpan di {STATE_FILE}")

    def scrape_top_stocks(self):
        """Scrape tabel Top Stock dari menu Bandar Detector"""
        print("Membuka halaman Top Stock...")
        self.page.goto("https://stockbit.com/")

        try:
            self.page.wait_for_selector('#modalnewavatar-button-skip', timeout=3000)
            self.page.click('#modalnewavatar-button-skip')
            print("Modal 'Skip' diklik.")
        except Exception:
            pass

        # klik menu "Bandar Detector"
        self.page.click('button[data-cy="right-menu-bandar_detector"]')

        # klik tab "Top Stock"
        self.page.click('#rc-tabs-0-tab-TOP_STOCKS')

        # tunggu tabel muncul
        self.page.wait_for_selector("div.top-stock-table table")

        # ambil baris tabel
        rows = self.page.query_selector_all("div.top-stock-table table tbody tr")

        data = []
        for row in rows:
            cols = [col.inner_text().strip() for col in row.query_selector_all("td")]
            if len(cols) == 6:
                data.append(cols)
            else:
                print(f"⚠️ Skip row, kolom tidak sesuai ({len(cols)}): {cols}")

        # convert ke DataFrame
        df = pd.DataFrame(data, columns=["Buy", "N.Val", "N.Lot", "N.Freq", "Avg", "N.Foreign"])

        # simpan ke CSV
        file_path = os.path.join(DOWNLOAD_PATH, "top_stocks.csv")
        df.to_csv(file_path, index=False, encoding="utf-8")
        print(f"✅ Top Stock data berhasil disimpan di {file_path}")

        return df

    def close_browser(self):
        if self.browser:
            self.browser.close()
        if self.p:
            self.p.stop()

if __name__ == "__main__":
    downloader = StockbitDownloader()
    downloader.start_browser()
    downloader.login_manual_if_needed()


    # scrape top stock
    df_top = downloader.scrape_top_stocks()
    print(df_top)

    downloader.close_browser()
    print("Selesai.")
