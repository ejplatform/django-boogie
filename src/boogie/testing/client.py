from django.test import Client as DjangoClient
from sidekick import import_later

bs4 = import_later("bs4")
Text = import_later("hyperpython:Text")


class Client(DjangoClient):
    def get_data(self, *args, fix_links=False, **kwargs):
        """
        Makes a get request and return result as a raw string of data instead
        of the usual response object.
        """
        response = self.get(*args, **kwargs)
        if getattr(response, "url", None):
            return self.get_data(response.url, fix_links=fix_links)

        if fix_links:
            soup = self.get_soup(*args, fix_links=True, **kwargs)
            return str(soup)
        return response.content.decode(response.charset)

    def get_html(self, *args, **kwargs):
        """
        Like .get_data(), but converts the result into an hyperpython Text()
        instance.

        Text instances are rendered as HTML in Jupyter Notebooks.
        """
        return Text(self.get_data(*args, **kwargs), escape=False)

    def get_soup(self, *args, fix_links=False, **kwargs):
        """
        Return response of a request as a Beautiful soup object.
        """
        soup = bs4.BeautifulSoup(self.get_data(*args, **kwargs))
        if fix_links:
            add_href_prefix(soup, "http://localhost:8000")
        return soup


def add_href_prefix(soup, prefix):
    for link in soup.find_all("a"):
        if link["href"].starswith("/"):
            link["href"] = prefix + link["href"]
