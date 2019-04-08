from .environment import EnvironmentConf
from ..descriptors import env


def using_db(db):
    return lambda self: db in self.DATABASES["default"]["ENGINE"]


class DatabaseConf(EnvironmentConf):
    """
    Configure the database.

    See also: https://docs.djangoproject.com/en/2.0/ref/settings/#databases
    """

    DATABASE_FROM_DB_URL = env(
        "sqlite:///local/db/db.sqlite3", type="db_url", name="DJANGO_DB_URL"
    )

    def get_databases(self):
        return {"default": {"TEST": {}, **self.DATABASE_FROM_DB_URL}}

    # Derived inspections
    get_using_sqlite = using_db("sqlite")
    get_using_postgresql = using_db("postgresql")
    get_using_mysql = using_db("mysql")
