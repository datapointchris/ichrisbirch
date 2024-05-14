import sys
from collections import OrderedDict
from queue import Queue
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


class ValidateWebsite:
    def __init__(self, base_url):
        self.base_url = base_url

        self.validator = 'https://validator.w3.org/nu/?out=json'
        self.return_code = 0

    def print_title(self, title: str):
        print(f"\n{'*'*20} {title} {'*'*20}\n")

    def discover_webpages_from_local_server(self):
        pages_to_visit: Queue[str] = Queue()
        discovered_pages: set[str] = set()
        urls_with_content: dict[str, str] = {}

        self.print_title('DISCOVERY')
        print(f'Base URL: {self.base_url}')
        pages_to_visit.put(self.base_url)
        discovered_pages.add(self.base_url)

        while not pages_to_visit.empty():
            current_page = pages_to_visit.get()
            print(f'  Visiting: {current_page}')
            try:
                response = httpx.get(current_page)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('text/html'):
                    urls_with_content[current_page] = response.text
                    soup = BeautifulSoup(response.text, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        absolute_url = urljoin(current_page, link['href'])
                        if absolute_url.startswith(self.base_url) and absolute_url not in discovered_pages:
                            print(f'    Link: {absolute_url}')
                            pages_to_visit.put(absolute_url)
                            discovered_pages.add(absolute_url)

                    for form in soup.find_all('form', class_='search-form'):
                        action = form.get('action')
                        absolute_url = urljoin(current_page, action)
                        if absolute_url.startswith(self.base_url) and absolute_url not in discovered_pages:
                            print(f'    Form: {absolute_url}')
                            pages_to_visit.put(absolute_url)
                            discovered_pages.add(absolute_url)
            except Exception as e:
                print(f'Error while processing {current_page}: {e}')
        return urls_with_content

    def remove_multiple_subpages(self, pages_with_content: dict[str, str]):
        self.print_title('REMOVING ENDPOINT SUBPAGES')
        deduped_pages: dict[str, str] = {}
        endpoints_with_id_path: set[str] = set()
        for page_url, html_content in pages_with_content.items():
            parsed_url = urlparse(page_url)
            path_parts = parsed_url.path.strip('/').split('/')
            endpoint = '/'.join(path_parts[:-1])
            final_path = path_parts[-1]
            try:
                int(final_path)
                if endpoint in endpoints_with_id_path:
                    print(f'  Skipping Duplicate: {page_url}\t - /{endpoint}/ already has an ID path endpoint.')
                else:
                    print(f'ID Path Endpoint: {page_url}')
                    deduped_pages[page_url] = html_content
                    endpoints_with_id_path.add(endpoint)
            except ValueError:
                print(f'Regular Endpoint: {page_url}')
                deduped_pages[page_url] = html_content
        return OrderedDict(sorted(deduped_pages.items()))

    def validate_page(self, html_content: str):
        headers = {'Content-Type': 'text/html; charset=utf-8'}
        try:
            response = httpx.post(self.validator, content=html_content, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f'Error while validating: {e}')
            self.return_code = 1
            exit(1)

    def validate_pages(self, pages_with_content):
        self.print_title('VALIDATION')
        for page_url, html_content in pages_with_content.items():
            try:
                print(f'Validating: {page_url} {len(html_content)} bytes')
                validation_result = self.validate_page(html_content)
                if validation_result['messages']:
                    print(f'Validation errors found for {page_url}:')
                    for message in validation_result['messages']:
                        print(message['message'])
                        print(f'Line: {message["lastLine"]}, Column: {message["lastColumn"]}')
                        print(message['extract'])
                    self.return_code = 1
            except Exception as e:
                print(f'Error while validating {page_url}: {e}')
                self.return_code = 1


def main() -> int:
    v = ValidateWebsite('http://localhost:6200/')
    pages_with_content = v.discover_webpages_from_local_server()
    deduplicated_pages = v.remove_multiple_subpages(pages_with_content)
    v.validate_pages(deduplicated_pages)
    return v.return_code


if __name__ == '__main__':
    sys.exit(main())
