import pymysql

pymysql.install_as_MySQLdb()

# Django 6.1+ expects MySQL 8.4+, this allows MySQL 8.0 compatibility
try:
    from django.db.backends.mysql.features import DatabaseFeatures

    DatabaseFeatures.minimum_database_version = property(
        lambda self: (10, 11) if self.connection.mysql_is_mariadb else (8, 0)
    )
except ImportError:
    pass

