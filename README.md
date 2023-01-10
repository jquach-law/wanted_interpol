# Interpol's Wanted JSON
The program will scrape for every single person on the Interpol's 'Wanted List'
URL: https://www.interpol.int/How-we-work/Notices/View-Red-Notices.

Program filters by nationality, then by age if result is greater than 160.
After a list of individuals' href is compiled, we combine that with base url to get 
individual's information and export to JSON.

**This does take a long while because it is scraping for every person

# Selenium: ChromeDriver
The scraper uses Chrome as it's driver. Please refer to link and install appropriate ChromeDriver version: https://chromedriver.chromium.org/home

# BeautifulSoup4
BeautifulSoup is used to extract information from HTML after Selenium driver navigates and executes the pages' JavaScript

# Installation
```
pip install -r requirements.txt
```

# Run
```
python interpol_scraper.py
```
# Shorter Version?
I might add a shorter version to scrape only the profiles presented to us.
