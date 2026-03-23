import time
import requests
from io import BytesIO
from PIL import Image
import pytesseract

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TESSERACT_PATH = r"D:\Program Files\Tesseract-OCR\tesseract.exe"
EDGE_DRIVER_PATH = r"C:\Users\kisho\Downloads\edgedriver_win64\msedgedriver.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ------------------
# Create Browser
# ------------------
def get_browser():
    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1920,1080")
    service = EdgeService(EDGE_DRIVER_PATH)
    browser = webdriver.Edge(service=service, options=opts)
    browser.implicitly_wait(5)
    return browser


# ------------------
# Amazon
# ------------------
def scrape_amazon(browser, query):
    browser.get("https://www.amazon.in")
    box = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
    )
    box.send_keys(query + Keys.RETURN)
    time.sleep(2)

    items = browser.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
    if not items:
        return {}

    item = items[0]
    name = item.find_element(By.TAG_NAME, "h2").text
    try:
        price = item.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
    except:
        price = "No price"
    link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
    try:
        image = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")
    except:
        image = None
    return {"Name": name, "Price": price, "Link": link, "Image": image}


# ------------------
# Flipkart
# ------------------
def scrape_flipkart(browser, query):
    browser.get("https://www.flipkart.com")
    time.sleep(2)

    # close popup
    try:
        close_btn = browser.find_element(By.XPATH, "//button[text()='x']")
        close_btn.click()
    except:
        pass

    box = WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    box.send_keys(query + Keys.RETURN)
    time.sleep(2)

    items = browser.find_elements(By.XPATH, "//a[contains(@href,'/p/')]")
    if not items:
        return {}

    item = items[0]
    name = item.text
    link = item.get_attribute("href")
    try:
        price = item.find_element(By.XPATH, ".//div[contains(@class,'_30jeq3')]").text
    except:
        price = "No price"
    try:
        image = item.find_element(By.XPATH, ".//img").get_attribute("src")
    except:
        image = None
    return {"Name": name, "Price": price, "Link": link, "Image": image}


# ------------------
# Myntra
# ------------------
def scrape_myntra(browser, query):
    browser.get("https://www.myntra.com")
    box = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.desktop-searchBar"))
    )
    box.send_keys(query + Keys.RETURN)
    time.sleep(2)

    items = browser.find_elements(By.CSS_SELECTOR, "li.product-base")
    if not items:
        return {}

    p = items[0]

    try:
        brand = p.find_element(By.CSS_SELECTOR, "h3.product-brand").text
        title = p.find_element(By.CSS_SELECTOR, "h4.product-product").text
        price = p.find_element(By.CSS_SELECTOR, "div.product-price span").text
        link = p.find_element(By.TAG_NAME, "a").get_attribute("href")
        image = p.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
    except:
        return {}
    return {
        "Name": f"{brand} {title}",
        "Price": price,
        "Link": link,
        "Image": image
    }
