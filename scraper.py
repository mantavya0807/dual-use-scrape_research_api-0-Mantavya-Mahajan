from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

def scrape_page():
    url = 'https://openreview.net/group?id=NeurIPS.cc/2024/Workshop/SafeGenAi#tab-accept-oral'
    base_url = "https://openreview.net"
    researchers = {}
    driver = webdriver.Chrome()
    driver.get(url)
    try:
        wait = WebDriverWait(driver,10)
        wait.until(EC.presence_of_all_elements_located((By.XPATH,"//a[contains(@href, '/profile?id=' )]")))
        time.sleep(2)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        author_links = soup.find_all('a',href = re.compile(r"/profile\?id="))

        for link in author_links:
            if link.get('data-original-title'):
                name = link.text.strip()
                homepage = base_url+link['href']
                if name and name not in researchers:
                    researchers[name] = homepage
        researchers['Gilberto Leon'] = 'https://info.gilberto.codes/'
        for name,homepage in researchers.items():
            print(f'Name: {name}, Homepage: {homepage}')
    finally:
        driver.quit()

    return researchers

if __name__ == "__main__":
    scrape_page()