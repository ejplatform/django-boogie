from django.test import Client

LOGIN_REGEX = r"^/login/*.$"


class UrlChecker:
    """
    Checks the response code for specific urls in an app.
    """

    def __init__(self, urls, posts, login_regex=LOGIN_REGEX, client=None):
        self.client = client or Client()
        self.urls = urls or {}
        self.posts = posts or {}
        self.login_regex = login_regex

    #
    # Get errors from a URL list
    #
    def get_error(self, url, code):
        """
        Check if client responds to given url with the provided status code.
        """
        response = self.client.get(url)
        if response.status_code not in code:
            return url, response

    def get_url_codes(self, url, default):
        """
        Normalize an url which can be of form "string" or ("string", *codes)
        and return a pair of url string and the corresponding codes.
        """
        if isinstance(url, str):
            return url, default
        elif isinstance(url, tuple):
            url, codes = url
            return url, codes
        else:
            raise TypeError(f"invalid url spec: {url} ({type(url).__name__})")

    def collect_errors(self, urls, default_codes) -> dict:
        """
        Return a mapping from url to their respective errors without changing
        the client login state.
        """
        errors = {}
        for url in urls:
            url, codes = self.get_url_codes(url, default_codes)
            error = self.get_error(url, codes)
            if error is not None:
                errors.update([error])
        return errors

    def check_public_urls(self, urls) -> dict:
        """
        Return a mapping of url to their corresponding errors when an error
        occurs.
        """
        self.client.logout()
        return self.collect_errors(urls, (200, 301, 302))

    def check_user_access(self, urls, user) -> dict:
        """
        Return a mapping of url to their corresponding errors when an error
        occurs.
        """
        self.client.force_login(user)
        return self.collect_errors(urls, (200, 301, 302))

    def check_login_required(self, urls) -> dict:
        """
        Return a mapping of url to their corresponding errors for failed login
        redirects.
        """
        self.client.logout()
        url_map = dict(urls)
        url_map.pop(None, None)
        urls = []
        for url_list in url_map.values():
            urls.extend(url_list)
        return self.collect_errors(urls, (302, 404))

    def check_restricted_pages(self, urls, user) -> dict:
        """
        Return a mapping of url to their corresponding errors for cases that
        grant unwanted access to resources.
        """
        self.client.force_login(user)
        return self.collect_errors(urls, (302, 404))

    def check_url_errors(self, users: dict) -> dict:
        """
        Runs all checks and create a dictionary with all errors.
        """
        urls = dict(self.urls)
        errors = {}

        # Public urls
        errors.update(self.check_public_urls(urls.pop(None, ())))

        # Test each user
        for name, url_list in urls.items():
            user = users[name]
            errors.update(self.check_user_access(url_list, user))

        # Test login redirects
        errors.update(self.check_login_required(urls))

        # Test permissions
        if "user" in users:
            user = users["user"]
            url_list = []
            for other_user, other_urls in urls.items():
                if other_user not in (None, "user"):
                    url_list.extend(other_urls)
            if url_list:
                errors.update(self.check_restricted_pages(url_list, user))

        return errors
