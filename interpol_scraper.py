import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

MAX_NUM_RESCRAPE = 4
JAVASCRIPT_LOAD_TIME = 0.75
MIN_AGE_RANGE = 8
MAX_AGE_RANGE = 120

class ScrapeInterpol:
    """
    Program filters by nationality, then by age if results is greater than 160.

    After a list of individuals' href is compiled, we combine that with base url to get 
    individual's information and export to JSON.
    """

    def __init__(self): 
        self.url = "https://www.interpol.int/How-we-work/Notices/View-Red-Notices"
        self.driver = None
        self.soup = None
        self.href_set = set()
        self.individual_details = dict()
        self.json_list = list()

    def set_up_chrome(self, options):
        chrome_options = webdriver.ChromeOptions()
        # Selecting Chrome Driver's options
        for option in options:
            chrome_options.add_argument(option)

        self.driver = webdriver.Chrome(service=ChromeService(
            ChromeDriverManager().install()), options=chrome_options)
        self.driver.get(self.url)
        time.sleep(JAVASCRIPT_LOAD_TIME)
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

    def _click_submit(self):
        submit = self.driver.find_element(By.ID, 'submit')
        self.driver.execute_script("arguments[0].click();", submit)
        time.sleep(JAVASCRIPT_LOAD_TIME)
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

    def _click_next_page(self):
        arrow = self.driver.find_element(By.CLASS_NAME, 'nextElement')
        button = arrow.find_element(By.TAG_NAME, 'a')
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(JAVASCRIPT_LOAD_TIME)
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

    def _filter_by_age(self):
        min_age_input = self.driver.find_element(By.ID, 'ageMin')
        max_age_input = self.driver.find_element(By.ID, 'ageMax')
        for age in range(MIN_AGE_RANGE, MAX_AGE_RANGE):
            max_age_input.send_keys(age)
            min_age_input.send_keys(age)
            self._click_submit()
            max_age_input.clear()
            min_age_input.clear()
            self._grab_all_href()

    def _results_greater_160(self):
        search_total = self.soup.find(id='searchResults').string
        return True if int(search_total) > 160 else False

    def _next_page_available(self):
        arrow_href = self.soup.find(
            'a', class_='nextIndex right-arrow')['href']
        return False if len(arrow_href) < 3 else True

    def _grab_all_href(self):
        result = self.soup.find_all("a", class_="redNoticeItem__labelLink")
        for person in result[:-2]:
            entity_id = person.get('href')
            self.href_set.add(entity_id)

        if self._next_page_available():
            self._click_next_page()
            self._grab_all_href()

    def filter_by_nationality(self):
        nationality_input = self.driver.find_element(By.ID, 'nationality')
        all_options = nationality_input.find_elements(By.TAG_NAME, 'option')
        for option in all_options[1:]:
            option.click()
            self._click_submit()
            # also filter by age if result is 160+
            if self._results_greater_160():
                self._filter_by_age()
            else:
                self._grab_all_href()

    def _reset_browser(self):
        # Use google as resetter
        self.driver.get('https://www.google.com/')
    
    def _load_individual_profile(self, href):
        person_url = self.url + href
        self.driver.get(person_url)
        time.sleep(JAVASCRIPT_LOAD_TIME)
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

    def _parse_profile_sex(self, key, strong):
        all_sex = strong.find_all('span')
        for sex in all_sex:
            if 'hidden' not in sex['class']:
                self.individual_details[key] = sex.string
                break

    def _parse_individual_profile(self):
        result = self.soup.find("div", class_="wantedsingle__colright")
        all_strong = result.find_all('strong')
        for strong in all_strong:
            key = strong.get('id')
            person_info = strong.get_text()

            # Extract sexual orientation
            if key == 'sex_id':
                self._parse_profile_sex()

            # Extract weight and height
            elif key in ['height', 'weight']:
                if person_info[:2] == '0 ':
                    continue
            
            # Extract date of birth
            elif key == 'date_of_birth':
                if len(person_info) == 10:
                    person_info = list(person_info)
                    person_info[0:2], person_info[3:5] = person_info[3:5], person_info[0:2]
                    person_info = ''.join(person_info)

            if not key:
                key = strong.find(id=True)
                if key:
                    key = key.get('id')

            # Other information
            if person_info and key:
                self.individual_details[key] = person_info

    def _append_to_json_list(self):
        self.json_list.append(self.individual_details.copy())
        self.individual_details.clear()
        self._reset_browser()

    def _write_jsonlist_to_file(self):
        json_object = json.dumps(self.json_list, indent=4)
        with open("people.json", "w") as outfile:
            outfile.write(json_object)

    def scrape_individual_profile(self):
        # Prevents www.interpol.int from getting stuck
        self._reset_browser()
        # Each href ties to one person
        for href in self.href_set:
            # Attempt to re-scrape person
            for i in range(MAX_NUM_RESCRAPE):
                # Load, parse, and save individuals profile details
                self._load_individual_profile(href)
                self._parse_individual_profile()

                # if details is obtained, move to next individual
                if self.individual_details:
                    break

            # Copy details into json list
            self._append_to_json_list()

        # Writing to json file
        self._write_jsonlist_to_file()


if __name__ == '__main__':
    scrape = ScrapeInterpol()
    options = ['--no-sandbox',
                '--disable-extensions',
                '--incognito',
                '--headless',
                '--disable-gpu']
    scrape.set_up_chrome(options)
    scrape.filter_by_nationality()
    scrape.scrape_individual_profile()

