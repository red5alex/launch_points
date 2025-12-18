# Launch Points Web Application

# Initialize pymysql as MySQLdb for Django compatibility
# This allows pymysql to work as a drop-in replacement for mysqlclient
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # pymysql not installed, mysqlclient will be used instead
