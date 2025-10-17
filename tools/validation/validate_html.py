import subprocess
import sys
import time
from collections import OrderedDict
from queue import Queue
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx
import pendulum
from bs4 import BeautifulSoup


class ValidateWebsite:
    def __init__(self, base_url, debug=False, dry_run=False, scrape_delay: float | None = None):
        self.base_url = base_url
        self.debug = debug
        self.dry_run = dry_run
        self.scrape_delay = scrape_delay
        self.discovered_pages: set[str] = set()

        self.validator = 'https://validator.w3.org/nu/?out=json'
        self.return_code = 0
        self.logs: list[str] = []
        self.total_discovered_pages: set[str] = set()
        self.total_visited_pages: set[str] = set()
        self.total_path_duplicates_removed: set[str] = set()
        self.total_validated: set[str] = set()
        self.total_validation_errors: set[str] = set()

    def section_title(self, title: str):
        return f'\n{"*" * 20} {title} {"*" * 20}\n'

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
        with open(filename, 'w') as f:
            f.writelines(log + '\n' for log in self.logs)

    def print_summary(self):
        self.logprint(self.section_title(f'SUMMARY FOR {self.base_url}'))
        self.logprint(f'Total Pages Discovered: {len(self.total_discovered_pages)}')
        self.logprint(f'Total Pages Visited: {len(self.total_visited_pages)}')
        self.logprint(f'Total Path Duplicates Removed: {len(self.total_path_duplicates_removed)}')
        self.logprint(f'Total Pages Validated: {len(self.total_validated)}')
        self.logprint(f'Total Validation Errors: {len(self.total_validation_errors)}')
        if visited_not_validated := self.total_visited_pages.difference(self.total_path_duplicates_removed).difference(
            self.total_validated
        ):
            self.logprint('Pages Visited but not Validated:')
            for page in visited_not_validated:
                self.logprint(page)

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
        self.logprint(f'BASE URL: {self.base_url}')
        pages_to_visit.put(self.base_url)
        self.discovered_pages.add(self.base_url)
        self.total_discovered_pages.add(self.base_url)

        while not pages_to_visit.empty():
            current_page = pages_to_visit.get()
            self.logprint(f'Visiting: {current_page}')
            self.total_visited_pages.add(current_page)
            try:
                response = httpx.get(current_page, follow_redirects=True)
                if self.scrape_delay:
                    time.sleep(self.scrape_delay)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('text/html'):
                    urls_with_content[current_page] = response.text
                    for url in self._parse_urls_from_page_content(current_page, response.text):
                        self.logprint(f'Discovered: {url}')
                        pages_to_visit.put(url)
                        self.discovered_pages.add(url)
                        self.total_discovered_pages.add(url)
                else:
                    self.alwaysprint(f'Error with response: {response}')
            except Exception as e:
                self.alwaysprint(f'Error while processing {current_page}: {e}')
        return urls_with_content

    def remove_endpoints_with_query_parameters(self, pages_with_content: dict[str, str]):
        self.logprint(self.section_title('REMOVING QUERY PARAMETER ENDPOINTS'))
        valid_urls = {}
        for url, html_content in pages_with_content.items():
            if '?' in url:
                self.logprint(f'Discarding Query Parameter URL: {url}')
                continue
            valid_urls[url] = html_content
        return valid_urls

    def remove_multiple_subpages(self, pages_with_content: dict[str, str]):
        self.logprint(self.section_title('REMOVING ENDPOINT SUBPAGES'))
        deduped_pages: dict[str, str] = {}
        endpoints_with_id_path: set[str] = set()
        for url, html_content in pages_with_content.items():
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            endpoint = '/'.join(path_parts[:-1])
            final_path = path_parts[-1]
            try:
                int(final_path)
                if endpoint not in endpoints_with_id_path:
                    deduped_pages[url] = html_content
                    endpoints_with_id_path.add(endpoint)
                else:
                    self.logprint(f'Removing Path Duplicate: {url}')
                    self.total_path_duplicates_removed.add(url)
            except ValueError:  # not id endpoint
                deduped_pages[url] = html_content
        return OrderedDict(sorted(deduped_pages.items()))

    def validate_page(self, html_content: str):
        """Validate html pages using tidy command line."""
        command = 'tidy -q -e'
        tidy = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _stderr = tidy.communicate(input=html_content.encode())
        return stdout.decode()

    def validate_pages(self, pages_with_content):
        self.logprint(self.section_title('VALIDATION'))
        for url, html_content in pages_with_content.items():
            try:
                self.logprint(f'Validating: {url} {len(html_content)} bytes')
                self.total_validated.add(url)
                if validation_result := self.validate_page(html_content):
                    self.alwaysprint(f'Validation errors found for {url}:')
                    self.alwaysprint(validation_result)
                    self.total_validation_errors.add(url)
                    self.return_code = 1
            except Exception as e:
                self.alwaysprint(f'Error while validating {url}: {e}')
                self.return_code = 1


def main() -> int:
    start = pendulum.now()
    v = ValidateWebsite('http://localhost:6200/')
    pages = v.discover_webpages_from_local_server()
    pages = v.remove_multiple_subpages(pages)
    v.validate_pages(pages)
    v.print_summary()
    v.logprint(f'Total Elapsed Time for Validation: {(pendulum.now() - start).in_words()}')
    v.save_logs('validate_html_logs.log')
    return v.return_code


if __name__ == '__main__':
    sys.exit(main())
