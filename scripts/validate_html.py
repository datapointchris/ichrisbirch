import sys
from collections import OrderedDict
from queue import Queue
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


class ValidateWebsite:
    def __init__(self, base_url, debug=False, dry_run=False):
        self.base_url = base_url
        self.debug = debug
        self.dry_run = dry_run
        self.discovered_pages: set[str] = set()

        self.validator = 'https://validator.w3.org/nu/?out=json'
        self.return_code = 0
        self.logs = []

    def section_title(self, title: str):
        return f"\n{'*'*20} {title} {'*'*20}\n"

    def log(self, message: str):
        self.logs.append(message)

    def logprint(self, message: str):
        if self.debug:
            print(message)
            self.log(message)

    def alwaysprint(self, message: str):
        print(message)
        self.logprint(message)

    def print_logs(self):
        for log in self.logs:
            print(log)

    def save_logs(self, filename: str):
        with open(filename, 'a') as f:
            f.writelines(log + '\n' for log in self.logs)

    def _parse_urls_from_page_content(self, page, content: str):
        urls_found = []
        soup = BeautifulSoup(content, 'html.parser')

        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(page, link['href'])
            urls_found.append(absolute_url)

        for form in soup.find_all('form', class_='search-form'):
            absolute_url = urljoin(page, form.get('action'))
            urls_found.append(absolute_url)

        valid_urls = [
            url
            for url in urls_found
            if (url.startswith(self.base_url) and url not in self.discovered_pages and 'postgres/snapshot' not in url)
        ]
        return valid_urls

    def discover_webpages_from_local_server(self):
        pages_to_visit: Queue[str] = Queue()
        urls_with_content: dict[str, str] = {}

        self.logprint(self.section_title('DISCOVERY'))
        self.logprint(f'Base URL: {self.base_url}')
        pages_to_visit.put(self.base_url)
        self.discovered_pages.add(self.base_url)

        while not pages_to_visit.empty():
            current_page = pages_to_visit.get()
            self.logprint(f'Visiting: {current_page}')
            try:
                response = httpx.get(current_page)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('text/html'):
                    urls_with_content[current_page] = response.text
                    for url in self._parse_urls_from_page_content(current_page, response.text):
                        self.logprint(f'Discovered: {current_page}')
                        pages_to_visit.put(url)
                        self.discovered_pages.add(url)
            except Exception as e:
                print(f'Error while processing {current_page}: {e}')
        return urls_with_content

    def remove_endpoints_with_query_parameters(self, pages_with_content: dict[str, str]):
        self.logprint(self.section_title('REMOVING QUERY PARAMETER ENDPOINTS'))
        valid_urls = {}
        for page_url, html_content in pages_with_content.items():
            if '?' in page_url:
                self.logprint(f'Discarding Query Parameter URL: {page_url}')
                continue
            valid_urls[page_url] = html_content
        return valid_urls

    def remove_multiple_subpages(self, pages_with_content: dict[str, str]):
        self.logprint(self.section_title('REMOVING ENDPOINT SUBPAGES'))
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
                    self.logprint(f'Skipping Duplicate: {page_url}\t - /{endpoint}/ already has an ID path endpoint.')
                else:
                    self.logprint(f'ID Path Endpoint: {page_url}')
                    deduped_pages[page_url] = html_content
                    endpoints_with_id_path.add(endpoint)
            except ValueError:
                self.logprint(f'Regular Endpoint: {page_url}')
                deduped_pages[page_url] = html_content
        return OrderedDict(sorted(deduped_pages.items()))

    def validate_page(self, html_content: str):
        headers = {'Content-Type': 'text/html; charset=utf-8'}
        try:
            response = httpx.post(self.validator, content=html_content, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.alwaysprint(f'Error while validating: {e}')
            self.return_code = 1
            exit(1)  # error from server, most likely 429 too many requests

    def validate_pages(self, pages_with_content):
        self.logprint(self.section_title('VALIDATION'))
        for page_url, html_content in pages_with_content.items():
            try:
                self.logprint(f'Validating: {page_url} {len(html_content)} bytes')
                if not self.dry_run:
                    validation_result = self.validate_page(html_content)
                    if validation_result['messages']:
                        self.alwaysprint(f'Validation errors found for {page_url}:')
                        for message in validation_result['messages']:
                            self.alwaysprint(message['message'])
                            self.alwaysprint(f'Line: {message["lastLine"]}, Column: {message["lastColumn"]}')
                            self.alwaysprint(message['extract'])
                        self.return_code = 1
            except Exception as e:
                self.alwaysprint(f'Error while validating {page_url}: {e}')
                self.return_code = 1


def main() -> int:
    v = ValidateWebsite('http://localhost:6200/')
    pages = v.discover_webpages_from_local_server()
    # pages = v.remove_endpoints_with_query_parameters(pages)
    pages = v.remove_multiple_subpages(pages)
    v.validate_pages(pages)
    v.save_logs('validate_html_logs.log')
    return v.return_code


if __name__ == '__main__':
    sys.exit(main())
