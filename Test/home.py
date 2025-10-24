import time
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==== CONFIG ====
CHROMEDRIVER = r"C:\Users\User\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
BASE_URL = "http://127.0.0.1:8000/"   # Your Django server URL

# ======================== Helper Functions ========================
def wait_for_server(url, timeout=30):
    """Wait until local server responds"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if 200 <= r.status < 400:
                    print("✅ Server is live.")
                    return True
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"❌ Server not reachable at {url} within {timeout}s.")

def log(ok, msg):
    print(("✅ " if ok else "❌ ") + msg)

def open_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    service = Service(CHROMEDRIVER)
    return webdriver.Chrome(service=service, options=opts)

# ======================== Navbar Test ========================
def test_navbar_links():
    print("\n🔹 Full Navbar Test Started")
    wait_for_server(BASE_URL, timeout=30)

    driver = open_driver()
    try:
        driver.get(BASE_URL)
        time.sleep(2)

        # Define navbar links and expected URL slugs
        links = {
            "Home": "",
            "Products": "products",
            "Pre-Orders": "preorder_products",
            "Rent": "rental_products",
            "Flash Sale": "flash_sale",
            "Orders": "orders",
            "Contact": "contact",
            "Login": "login",
            "Signup": "signup"
        }

        for name, slug in links.items():
            try:
                # Find the link (works for desktop navbar)
                link = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, name))
                )
                link.click()
                time.sleep(2)

                # Check if current URL contains the expected slug
                current_url = driver.current_url
                if slug == "":
                    log(BASE_URL in current_url, f"'{name}' navigates to Home → {current_url}")
                else:
                    log(slug in current_url, f"'{name}' navigates correctly → {current_url}")

                # Return to homepage before next link
                driver.get(BASE_URL)
                time.sleep(1)

            except Exception as e:
                log(False, f"'{name}' navigation failed → {e}")

        print("\n✅ Full Navbar test finished successfully\n")

    finally:
        driver.quit()

# ======================== Run ========================
if __name__ == "__main__":
    test_navbar_links()
