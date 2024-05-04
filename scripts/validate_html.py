import sys
import time
from queue import Queue
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


class ValidateWebsite:
    def __init__(self, base_url):
        self.base_url = base_url
        self.pages_to_visit = Queue()
        self.discovered_pages = set()
        self.page_content: dict[str, str] = {}
        self.validator = "https://validator.w3.org/nu/?out=json"
        self.return_code = 0

    def discover_webpages_from_local_server(self):
        self.pages_to_visit.put(self.base_url)
        self.discovered_pages.add(self.base_url)

        while not self.pages_to_visit.empty():
            current_page = self.pages_to_visit.get()
            print(f"Visiting {current_page}")

            try:
                response = httpx.get(current_page)
                if response.status_code == 200 and response.headers.get("content-type", "").startswith("text/html"):
                    self.page_content[current_page] = response.text
                    soup = BeautifulSoup(response.text, "html.parser")

                    links = soup.find_all("a", href=True)
                    for link in links:
                        absolute_url = urljoin(current_page, link["href"])
                        if absolute_url.startswith(self.base_url) and absolute_url not in self.discovered_pages:
                            print(f"Discovered from link: {absolute_url}")
                            self.pages_to_visit.put(absolute_url)
                            self.discovered_pages.add(absolute_url)

                    search_forms = soup.find_all("form", class_="search-form")
                    for form in search_forms:
                        action = form.get("action")
                        absolute_url = urljoin(current_page, action)
                        if absolute_url.startswith(self.base_url) and absolute_url not in self.discovered_pages:
                            print(f"Discovered from search form: {absolute_url}")
                            self.pages_to_visit.put(absolute_url)
                            self.discovered_pages.add(absolute_url)

                time.sleep(2)

            except Exception as e:
                print(f"Error while processing {current_page}: {e}")

    def validate_page(self, html_content: str):
        headers = {"Content-Type": "text/html; charset=utf-8"}
        return httpx.post(self.validator, content=html_content, headers=headers).json()

    def validate_pages(self):
        for page_url, html_content in sorted(self.page_content.items()):
            try:
                print(f'Validating {page_url}')
                validation_result = self.validate_page(html_content)
                if validation_result['messages']:
                    print(f"Validation errors found for {page_url}:")
                    for message in validation_result['messages']:
                        print(message['message'])
                        print(f'Line: {message["lastLine"]}, Column: {message["lastColumn"]}')
                        print(message['extract'])
                    self.return_code = 1
            except Exception as e:
                print(f"Error while validating {page_url}: {e}")
                self.return_code = 1


def main() -> int:
    v = ValidateWebsite('http://localhost:6200/')
    v.discover_webpages_from_local_server()
    v.validate_pages()
    return v.return_code


if __name__ == "__main__":
    sys.exit(main())
