from sidekick import lazy, placeholder as this
from .environment import EnvironmentConf
from ..descriptors import env


class DatabaseConf(EnvironmentConf):
    """
    Configure the database.

    See also: https://docs.djangoproject.com/en/2.0/ref/settings/#databases
    """

    DATABASE_DEFAULT = env('sqlite:///local/db/db.sqlite3',
                           type='db_url',
                           name='DJANGO_DB_URL')

    DATABASES = lazy(lambda self: {
        'default': dict(TEST={}, **self.DATABASE_DEFAULT),
    })

    # Derived inspections
    USING_SQLITE = lazy(this.is_using_db('sqlite'))
    USING_POSTGRESQL = lazy(this.is_using_db('postgresql'))
    USING_MYSQL = lazy(this.is_using_db('mysql'))

    def is_using_db(self, db, which='default'):
        return db in self.DATABASES[which]['ENGINE']
