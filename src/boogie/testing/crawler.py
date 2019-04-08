import re
import sys
from collections import deque
from html.parser import HTMLParser

from django.test.client import Client

# Utility functions
cte = lambda x: lambda *args: x
choose = lambda cond, do, other: do if cond else other


def crawl(url="/", skip_patterns=(), skip_urls=(), errors=(), user=None, log=print):
    """
    Crawl website starting from the given base url and return a dictionary with
    all pages with invalid status codes (e.g. 404, 500, etc)

    Args:
        url (str or list):
            Starting url or lists of URLs.
        skip_patterns (list of regex strings):
            List of regular expressions with patterns that should be
            skip even if a hyperlink is found in the webpage.
        skip_urls (list or strings):
            List of URLs that should be skip.
        errors (list of regex strings):
            List of regular expressions that match links that should be
            considered instant errors.
        user:
            User used to visit the pages.
        log:
            Function used to print debug messages. Uses the builtin print()
            function by default..
    """
    # Create test client
    client = Client()
    if user:
        client.force_login(user)

    # Control urls that should be included/excluded from analysis
    skip_urls = set(skip_urls)
    skip_match = re.compile("|".join(skip_patterns)).match
    errors_re = re.compile("|".join(errors))
    keep = choose(
        skip_patterns or skip_urls,
        lambda x: (x not in skip_urls) and (not skip_match(x)),
        cte(True),
    )
    is_error = choose(errors, lambda x: errors_re.match(x), cte(False))
    log = log or cte(None)

    # Accumulation variables
    visited = {}
    pending = deque([url] if isinstance(url, str) else url)
    referrals = {}
    errors = {}

    while pending:
        url = pending.popleft()
        if url in visited:
            continue

        response = client.get(url)
        code = response.status_code
        log(f"visited: {url} (code {code})")
        visited[url] = code

        if code == 200:
            text = response.content.decode(response.charset)
            links = find_urls(text, url)
            links = list(filter(keep, links))
            referrals.update((link, url) for link in links)
            pending.extend(links)
            errors.update((x, url) for x in links if is_error(x))

        elif code in (301, 302):
            pending.append(response.url)
        else:
            errors[url] = referrals.get(url, "") + f" (status code: {code})"

    return errors, visited


def check_link_errors(*args, visit=(), user="user", **kwargs):
    """
    Craw site starting from the given base URL and raise an error if the
    resulting error dictionary is not empty.

    Notes:
        Accept the same arguments of the :func:`crawl` function.
    """
    errors, visited = crawl(*args, **kwargs)
    for url in visit:
        if url not in visited:
            errors[url] = f"URL was not visited by {user}"
    if errors:
        for url, code in errors.items():
            if isinstance(code, int):
                print(f"URL {url} returned invalid status code: {code}")
            else:
                print(f"Invalid URL {url} encountered at {code}")
        raise AssertionError(errors, visited)
    return visited


#
# Utility
#
class HTMLAnchorFinder(HTMLParser):
    SKIP_VALUE_RE = re.compile(r"http://|https://|#.*|^$")

    def __init__(self, data=None, current="/"):
        super().__init__()
        if data is None:
            data = set()
        self.data = data
        self.current = current

    def handle_starttag(self, tag, attrs):
        regex = self.SKIP_VALUE_RE

        if tag != "a":
            return

        for name, href in attrs:
            if name == "href" and regex.match(href) is None:
                if not href.startswith("/"):
                    href = self.current + href
                self.data.add(href)

    def error(self, message):
        print(message, file=sys.stdout)

    def iter_urls(self):
        return iter(self.data)


def find_urls(src, base_path="/"):
    """
    Find all internal href values in the given source code.

    Normalizes to absolute paths by using the base_url as reference.
    """
    parser = HTMLAnchorFinder(set(), base_path)
    parser.feed(src)
    return parser.iter_urls()
