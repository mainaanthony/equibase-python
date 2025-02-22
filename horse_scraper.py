import undetected_chromedriver as uc
import random
import time
import pandas as pd
import schedule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def get_driver():
    options = uc.ChromeOptions()
    options.headless = False  # Keep it visible for now
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options)
    return driver

def get_horse_data():
    driver = get_driver()
    today_date = datetime.today().strftime('%m/%d/%y')
    horse_data = []

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        url = f"https://www.equibase.com/premium/eqpInTodayAction.cfm?DATE={today_date}&TYPE=H&VALUE={letter}"
        driver.get(url)
        time.sleep(random.uniform(5, 12))  # Random wait time

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".table-padded tbody tr"))
            )

            rows = driver.find_elements(By.CSS_SELECTOR, ".table-padded tbody tr")
            for row in rows:
                try:
                    horse_element = row.find_element(By.TAG_NAME, "a")
                    horse_link = horse_element.get_attribute("href")
                    horse_name = horse_element.text.strip()
                    track = row.find_elements(By.TAG_NAME, "td")[1].text.strip()
                    race = row.find_elements(By.TAG_NAME, "td")[2].text.strip()
                    jockey = row.find_elements(By.TAG_NAME, "td")[3].text.strip()
                    trainer = row.find_elements(By.TAG_NAME, "td")[4].text.strip()
                    owner = row.find_elements(By.TAG_NAME, "td")[5].text.strip()
                    pps = row.find_elements(By.TAG_NAME, "td")[6].text.strip()

                    horse = {
                        "name": horse_name,
                        "link": horse_link,
                        "track": track,
                        "race": race,
                        "jockey": jockey,
                        "trainer": trainer,
                        "owner": owner,
                        "pps": pps
                    }
                    horse_data.append(horse)
                    print(f"Added horse: {horse_name}")
                    print(f"Link: {horse_link}")
                except Exception as e:
                    print(f"Error extracting horse data: {e}")
                    continue

        except Exception as e:
            print(f"Failed to fetch horse data for letter {letter}: {e}")

    driver.quit()
    return horse_data

def get_horse_stats(horse_link):
    driver = get_driver()
    driver.get(horse_link)
    
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#data-table tbody tr")))
        
        # Find the table with stats
        table = driver.find_element(By.ID, "data-table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        # Initialize stats
        stats = {
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
        
        print(f"Stats Data : {stats}")
        return stats
    except Exception as e:
        print(f"Failed to fetch data for {horse_link}: {e}")
        return None
    finally:
        driver.quit()

def save_to_excel(data):
    df = pd.DataFrame(data)
    df.to_excel("horse_stats.xlsx", index=False)
    print("Data saved to horse_stats.xlsx")

def scrape_horses():
    horse_data = get_horse_data()
    all_horse_data = []
    
    for horse in horse_data:
        stats = get_horse_stats(horse["link"])
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