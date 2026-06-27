# -*- coding: utf-8 -*-
# Zetsal VPN auto register - Selenium + cached chromedriver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import random
import string
import time

TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
CHROMEDRIVER = r"C:\Users\XZXyuan\.wdm\drivers\chromedriver\win64\148.0.7778.178\chromedriver-win32\chromedriver.exe"

def nanoid(n=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

def solve_captcha(driver):
    cap = driver.find_element(By.CSS_SELECTOR, "#cap")
    cap.screenshot("captcha.png")
    for psm in ['7', '8', '13']:
        try:
            r = subprocess.run(
                [TESSERACT, "captcha.png", "-", "--psm", psm,
                 "-c", "tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"],
                capture_output=True, text=True, timeout=10
            )
            text = r.stdout.strip().replace(" ", "").replace("\n", "")
            if 4 <= len(text) <= 8:
                return text
        except:
            pass
    return None

def register():
    username = nanoid(10)
    email = nanoid(8) + "@KiNpNAk4EDbyhp5RPsBxpEisR8.com"
    password = nanoid(16)
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--proxy-server=direct://")
    options.add_argument("--disable-extensions")
    
    service = Service(CHROMEDRIVER)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    
    try:
        driver.get("https://zetsal.com/register")
        wait = WebDriverWait(driver, 15)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#username"))).send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "#email").send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "#password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "#password2").send_keys(password)
        
        for attempt in range(8):
            captcha = solve_captcha(driver)
            if not captcha:
                driver.refresh()
                time.sleep(2)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#username"))).send_keys(username)
                driver.find_element(By.CSS_SELECTOR, "#email").send_keys(email)
                driver.find_element(By.CSS_SELECTOR, "#password").send_keys(password)
                driver.find_element(By.CSS_SELECTOR, "#password2").send_keys(password)
                continue
            
            print(f"  [OCR] {captcha}")
            cap_input = driver.find_element(By.CSS_SELECTOR, "#captcha")
            cap_input.clear()
            cap_input.send_keys(captcha)
            
            btn = driver.find_element(By.CSS_SELECTOR, "#btn")
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(4)
            
            if "/register" not in driver.current_url:
                break
            
            try:
                alert = driver.find_element(By.CSS_SELECTOR, ".alert-danger")
                if "Captcha" in alert.text or "captcha" in alert.text:
                    print(f"  [RETRY] Captcha wrong: {captcha}")
                    driver.get("https://zetsal.com/register")
                    time.sleep(2)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#username"))).send_keys(username)
                    driver.find_element(By.CSS_SELECTOR, "#email").send_keys(email)
                    driver.find_element(By.CSS_SELECTOR, "#password").send_keys(password)
                    driver.find_element(By.CSS_SELECTOR, "#password2").send_keys(password)
                    continue
                else:
                    print(f"  [FAIL] {alert.text[:100]}")
                    return None
            except:
                pass
        
        if "/register" in driver.current_url:
            print(f"  [FAIL] Still on register page after 8 attempts")
            return None
        
        print(f"  [OK] Registered! URL: {driver.current_url}")
        
        try:
            driver.get("https://zetsal.com/plans")
            time.sleep(3)
            btn = driver.find_element(By.CSS_SELECTOR, "body > .slim-mainpanel > .container > .alert > .btn")
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3)
            print(f"  [OK] Free trial claimed")
        except:
            print(f"  [WARN] Could not claim trial")
        
        with open("zetsal.txt", "a", encoding="utf-8") as f:
            f.write(f"{username}:{password}\n")
        print(f"  [OK] {username}:{password}")
        return {"username": username, "password": password}
    
    except Exception as e:
        print(f"  [ERR] {e}")
        return None
    finally:
        driver.quit()

print("=== Zetsal VPN Auto Register ===")
success = 0
for i in range(3):
    print(f"\n--- Account {i+1}/3 ---")
    result = register()
    if result:
        success += 1
    time.sleep(2)
print(f"\nDone! {success} accounts registered")
