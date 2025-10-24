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
BASE_URL = "http://127.0.0.1:8000/"
USERNAME = "Nazmul"
PASSWORD = "123"
ADDRESS = "Tejgaon"
PHONE = "02151"

# ==== Helper Functions ====
def wait_for_server(url, timeout=30):
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

# ==== MAIN TEST ====
def test_buy_now():
    wait_for_server(BASE_URL)
    driver = open_driver()
    wait = WebDriverWait(driver, 15)

    try:
        # Step 1 — Open Home Page
        driver.get(BASE_URL)
        log(True, "Opened Home Page")

        # Step 2 — Go to Login
        login_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign in")))
        login_link.click()
        log(True, "Opened Login Page")

        # Step 3 — Fill login form
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        log(True, "Login form submitted")

        # Step 4 — Verify login success
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign out")))
        log(True, "Login successful")

        # Step 5 — Go to Products Page
        products_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Products")))
        products_link.click()
        log(True, "Opened Products Page")

        # Step 6 — Click first Buy Now link (anchor tag)
        buy_now_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(),'Buy Now')]"))
        )
        if not buy_now_buttons:
            raise Exception("No Buy Now button found!")
        buy_now_buttons[0].click()
        log(True, "Clicked first Buy Now link")

        # Step 7 — Fill Checkout Form
        address_box = wait.until(EC.presence_of_element_located((By.NAME, "address")))
        phone_box = driver.find_element(By.NAME, "phone")
        address_box.send_keys(ADDRESS)
        phone_box.send_keys(PHONE)
        log(True, "Filled address and phone")

        # Step 8 — Proceed to Payment
        proceed_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Proceed to Payment')]")))
        proceed_btn.click()
        log(True, "Clicked Proceed to Payment")

        # Step 9 — Select Mobile Banking → bKash → Success
        time.sleep(2)
        mobile_bank = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(text(),'Mobile Banking')]")))
        mobile_bank.click()
        bkash = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(text(),'bKash')]")))
        bkash.click()
        log(True, "Selected bKash option")

        success_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Success')]")))
        success_btn.click()
        log(True, "Clicked Success button")

        # Step 10 — Continue Shopping
        continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Continue Shopping')]")))
        continue_btn.click()
        log(True, "Clicked Continue Shopping")

        print("\n🎉 TEST SUCCESSFULLY COMPLETED!")

    except Exception as e:
        log(False, f"Test failed: {e}")

    finally:
        time.sleep(3)
        driver.quit()


# ==== RUN ====
if __name__ == "__main__":
    test_buy_now()


