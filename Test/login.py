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
BASE_URL = "http://127.0.0.1:8000/"  # Your Django server URL

# ======================== Helper Functions ========================
def wait_for_server(url, timeout=30):
    """Wait until local server responds (avoid net::ERR_CONNECTION_REFUSED)."""
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

def open_driver(headless=False):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    service = Service(CHROMEDRIVER)
    return webdriver.Chrome(service=service, options=opts)

# ======================== Login Test ========================
def test_login():
    print("\n🔹 Login Test Started")
    wait_for_server(BASE_URL, timeout=30)

    driver = open_driver(headless=False)
    try:
        # Load Home Page
        t0 = time.time()
        driver.get(BASE_URL)
        load_time = time.time() - t0
        log(True, f"Loaded Home page → {BASE_URL} in {load_time:.2f}s")
        time.sleep(1)

        # Click "Sign in" button in navbar
        login_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sign in"))
        )
        login_link.click()
        log(True, "Navigated to Login page")
        time.sleep(2)

        # Fill login form
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys("Nazmul")   # Your username
        password_input.send_keys("123")      # Your password

        # Click Login / Sign in button
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        log(True, "Login form submitted")
        time.sleep(3)

        # Optional: Check if login was successful by URL or presence of logout button
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Sign out"))
        )
        log(True, "Login successful, 'Sign out' found")
        print("🔹 Login Test Finished 🔹")

    finally:
        driver.quit()

# ======================== Run Test ========================
if __name__ == "__main__":
    test_login()
