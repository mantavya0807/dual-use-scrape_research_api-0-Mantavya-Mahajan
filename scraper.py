from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import requests
import subprocess
import os
import shutil
from urllib.parse import urlparse

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
                    researchers[name] = {'profile_url': homepage, 'github': None}
        researchers['Gilberto Leon'] = {'profile_url':'https://info.gilberto.codes/', 'github':None}
        # for name,homepage in researchers.items():
        #     print(f'Name: {name}, Homepage: {homepage}')
    finally:
        driver.quit()
    return researchers

def find_github_links(researchers_data):
    session = requests.session()
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    for name,data in researchers_data.items():
        profile_url = data['profile_url']
        if 'Gilberto' in profile_url:
            pesonal_homepage_url = profile_url
        else:
            try:
                response = session.get(profile_url, headers= headers, timeout=10)
                response.raise_for_status
                soup = BeautifulSoup(response.content, 'html.parser')
                homepage_tag = soup.find('a', string='Homepage')
                if not homepage_tag:
                    print(f'no personal link for {name}')
                    continue
                personal_homepage_url = homepage_tag['href']

            except requests.exceptions.RequestException as e:
                print(f'could not process {name}')
        try:
            response = session.get(personal_homepage_url, headers=headers, timeout= 10)
            response.raise_for_status()
            soup=BeautifulSoup(response.content, 'html.parser')
            github_link = soup.find('a', href = re.compile(r"github\.com"))
            if github_link:
                found_url = github_link['href']
                researchers_data[name]['github'] = found_url
                print(f'found {found_url} for {name}')
            else:
                print(f'no github for {name}')
        except requests.exceptions.RequestException as e:
            print(f'error in {name}: {e}')
    
    return researchers_data

def scan_repository(repo_url, output_dir = "gitleaks_reports"):
    repo_name = repo_url.split('/')[-1].replace('.git','')
    try:
        print(f"scanning {repo_url}")
        subprocess.run(['git', 'clone', '--depth', '1', repo_url], check=True, capture_output=True, text=True)
        if not os.path.isdir(repo_name): return

        print(f'doing gitleaks on {repo_name}')
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, f'{repo_name}_leaks.json')
        gitleaks_command = ['gitleaks','detect', '-s','.','--report-format','json','--report-path', os.path.join('..', report_path)]
        subprocess.run(gitleaks_command, check=True, cwd = repo_name, capture_output=True, text=True)
        print('scan completed')
    except subprocess.CalledProcessError as e:
        print(f'error {e}')
    finally:
        if os.path.isdir(repo_name):
            print(f'cleaning up')
            for i in range(3):
                try:
                    shutil.rmtree(repo_name)
                    print("cleanup complete")
                    break
                except PermissionError as e:
                    if i<2:
                        print("trying again")
                        time.sleep(2)
                    else:
                        print('cleanup failed')

def process_github_url(url):
    parsed_path = urlparse(url).path.strip('/').split('/')
    if len(parsed_path)==2:
        scan_repository(url)
    elif len(parsed_path)==1:
        username = parsed_path[0]
        print('user profile detected')
        api_url = f'https://api.github.com/users/{username}/repos'
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            repos = response.json()
            for repo in repos:
                clone_url = repo['clone_url']
                scan_repository(clone_url)
        except requests.exceptions.RequestException as e:
            print('failed')
    
    else:
        print('inrecognized url')
    
if __name__ == "__main__":
    research_profiles = scrape_page()
    fianl_data = find_github_links(research_profiles)
    github_urls_to_scan = []
    for person, data in fianl_data.items():
        if data.get('github'):
            github_urls_to_scan.append(data['github'])
    for urls in github_urls_to_scan:
        process_github_url(urls)

