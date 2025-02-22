import undetected_chromedriver as uc
import random
import time
import pandas as pd
import schedule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_driver():
    options = uc.ChromeOptions()
    options.headless = False  # Keep it visible for now
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options)
    return driver

def get_horse_names():
    driver = get_driver()
    today_date = datetime.today().strftime('%m/%d/%y')
    base_url = f"https://www.equibase.com/premium/eqpInTodayAction.cfm?DATE={today_date}&TYPE=H&VALUE="
    
    horse_names = []

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        url = base_url + letter
        driver.get(url)
        time.sleep(random.uniform(5, 12))  # Random wait time

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".table-padded tbody tr"))
            )

            rows = driver.find_elements(By.CSS_SELECTOR, ".table-padded tbody tr")
            for row in rows:
                try:
                    name = row.find_element(By.TAG_NAME, "a").text.strip()
                    if name and name not in horse_names:
                        horse_names.append(name)
                        print(f"Added horse: {name}")
                except Exception as e:
                    print(f"Error extracting horse name: {e}")
                    continue
        except Exception as e:
            print(f"No horses found for letter {letter}: {e}")

        # Scroll down a bit to look more human
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(3, 7))  # Vary the wait time

    driver.quit()
    print(f"Total horses found: {len(horse_names)}")
    return horse_names

def get_horse_stats(horse_name):
    driver = get_driver()
    
    search_url = f"https://www.equibase.com/profiles/Results.cfm?type=Horse&searchName={horse_name.replace(' ', '%20')}"
    driver.get(search_url)
    
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#data-table tbody tr")))
        
        # Find the table with stats
        table = driver.find_element(By.ID, "data-table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        # Initialize stats
        stats = {
            "Horse": horse_name,
            "Starts": "0",
            "Firsts": "0",
            "Seconds": "0",
            "Thirds": "0"
        }
        
        # Extract data from the first row (Career stats)
        if len(rows) > 1:
            career_row = rows[1]
            cols = career_row.find_elements(By.TAG_NAME, "td")
            stats["Starts"] = cols[1].text.strip()
            stats["Firsts"] = cols[2].text.strip()
            stats["Seconds"] = cols[3].text.strip()
            stats["Thirds"] = cols[4].text.strip()
        
        print(f"Stats for {horse_name}: {stats}")
        return stats
    except Exception as e:
        print(f"Failed to fetch data for {horse_name}: {e}")
        return None
    finally:
        driver.quit()

def get_horse_data():
    url = "https://www.equibase.com/premium/eqpInTodayAction.cfm?DATE=02/19/25&TYPE=H&VALUE=A"
    try:
        response = requests.get(url, timeout=30)  # Increase timeout
        response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching horse data: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", {"class": "table-padded fullwidth phone-hide desktop-show tablet-show"})
    
    if table is None:
        print("No table found on the page.")
        return []

    rows = table.find_all("tr")

    horses = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 0:  # Ensure there are columns
            horse = {
                "name": cols[0].text.strip(),
                "track": cols[1].text.strip(),
                "race": cols[2].text.strip(),
                "jockey": cols[3].text.strip(),
                "trainer": cols[4].text.strip(),
                "owner": cols[5].text.strip(),
                "pps": cols[6].text.strip()
            }
            horses.append(horse)

    return horses

def save_to_excel(data):
    df = pd.DataFrame(data)
    df.to_excel("horse_stats.xlsx", index=False)
    print("Data saved to horse_stats.xlsx")

def scrape_horses():
    horse_names = get_horse_names()
    horse_data = get_horse_data()
    all_horse_data = []
    
    for horse in horse_data:
        stats = get_horse_stats(horse["name"])
        if stats:
            horse.update(stats)
            all_horse_data.append(horse)
    
    save_to_excel(all_horse_data)

def schedule_scraper():
    schedule.every().day.at("00:00").do(scrape_horses)
    print("Scheduled scraper to run daily at midnight.")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

print("Running scraper now for testing...")
scrape_horses()
schedule_scraper()