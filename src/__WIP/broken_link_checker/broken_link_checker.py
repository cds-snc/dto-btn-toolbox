from selenium import webdriver
from bs4 import BeautifulSoup
import urllib.parse
import time
import requests


def get_links_from_html(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = [urllib.parse.urljoin(base_url, link.get('href'))
             for link in soup.find_all('a')]
    return links


def check_links(links):
    working_links = []
    broken_links = []

    for link in links:
        try:
            response = requests.get(link)
            if response.status_code == 200:
                working_links.append(link)
            else:
                broken_links.append(link)
        except requests.exceptions.RequestException:
            broken_links.append(link)
    return working_links, broken_links


def recursive_link_check(url, base_site, driver, depth=3):
    if depth < 0:
        return [], []

    driver.get(url)

    # Sleep to allow JavaScript to load the dynamic content
    time.sleep(5)

    html = driver.page_source

    # Extract main and table tags content
    soup = BeautifulSoup(html, 'html.parser')
    main_content = str(soup.find('main', {'property': 'mainContentOfPage'}))
    tables = soup.find_all('table')
    table_contents = [str(table) for table in tables]

    links_main = get_links_from_html(main_content, url)
    links_tables = [get_links_from_html(
        table_content, url) for table_content in table_contents]
    links = links_main + [link for sublist in links_tables for link in sublist]

    all_working_links = []
    all_broken_links = []
    working_links, broken_links = check_links(links)
    all_working_links.extend(working_links)
    all_broken_links.extend(broken_links)

    allowed_sites = ['blog.canada.ca', 'canada-content-style-guide',
                     'canada-content-information-architecture-specification', 'design.canada.ca']
    print("working links: ")
    print(working_links)
    for link in working_links:
        if any(allowed_site in link for allowed_site in allowed_sites):
            wl, bl = recursive_link_check(link, base_site, driver, depth-1)
            all_working_links.extend(wl)
            all_broken_links.extend(bl)

    return all_working_links, all_broken_links


def main():
    url = 'https://www.canada.ca/en/government/about/design-system.html'
    parsed_url = urllib.parse.urlparse(url)
    base_site = parsed_url.netloc

    # Provide the path to your Chromedriver
    driver = webdriver.Chrome('/Users/hamza/Desktop/keys/chromedriver')

    working_links, broken_links = recursive_link_check(url, base_site, driver)

    driver.quit()

    print("Working Links:")
    for link in working_links:
        print(link)

    print("\nBroken Links:")
    for link in broken_links:
        print(link)


if __name__ == "__main__":
    main()
