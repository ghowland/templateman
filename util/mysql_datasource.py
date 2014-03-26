"""
MySQL Datasource Handler

Wraps all the things we need to work with MySQL queries, for a data source.
"""


from log import log


# Import MySQLdb or mysql.connector.  We wil use either.
try:
  import MySQLdb
  import MySQLdb.cursors
  
  MYSQL_MODULE = 'MySQLdb'
  MYSQL_EXCEPTION = MySQLdb.DatabaseError

except ImportError, e:
  try:
    import mysql.connector
    
    class MySQLCursorDict(mysql.connector.cursor.MySQLCursor):
        def _row_to_python(self, rowdata, desc=None):
            row = super(MySQLCursorDict, self)._row_to_python(rowdata, desc)
            if row:
                return dict(zip(self.column_names, row))
            return None
    
    MYSQL_MODULE = 'mysql.connector'
    MYSQL_EXCEPTION = mysql.connector.Error
  
  except ImportError, e:
    raise Exception('Missing both MySQLdb and mysql.connector.  You must have one of these DB libraries installed.')



class MysqlQueryFailure(Exception):
  """Failure to query the DB properly"""


def Query(datasource, filter):
  """Wrap MysqlQuery with datasource/filter interface."""
  result = MysqlQuery(filter, host=datasource['host'], user=datasource['user'], 
                      password=datasource['password'], database=datasource['database'], 
                      port=datasource.get('port', 3306))

  return result


def MysqlQuery(sql, host, user, password, database, port=3306):
  """Execute and Fetch All results, or reutns last row ID inserted if INSERT."""
  # Connect (will save connections)
  (conn, cursor) = Connect(host, user, password, database, port)

  if not sql.upper().startswith('SELECT'):
    raise MysqlQueryFailure('Only SELECT statements are allowed.  We dont want to change any data.')

  # Try to reconnect and stuff
  success = False
  tries = 0
  last_error = None
  while tries <= 3 and success == False:
    tries += 1

    try:
      #log('Query: %s' % sql)
      cursor.execute(sql)
      
      #log('Query complete, committing')
      
      # Command didnt throw an exception
      success = True
    
    except MYSQL_EXCEPTION, e:
      print(e)
      print(dir(e))
      
      try:
        # MySQLdb
        (error_code, error_text) = e
      except ValueError:
        # mysql.connector
        (error_code, error_text) = (e.errno, e.msg)
        
      
      last_error = '%s: %s (Attempt: %s): %s: %s: %s' % (error_code, error_text, tries, host, database, sql)
      
      # Connect lost, reconnect
      if error_code in (2006, '2006'):
        log('Lost connection: %s' % last_error)
        Connect(host, user, password, database, port, reset=True)
      else:
        log('Unhandled MySQL query error: %s' % last_error)

  # If we made the query, get the result
  if success:
    if sql.upper().startswith('INSERT'):
      result = cursor.lastrowid
      conn.commit()
      
    elif sql.upper().startswith('UPDATE') or sql.upper().startswith('DELETE'):
      conn.commit()
      result = None
      
    elif sql.upper().startswith('SELECT'):
      result = cursor.fetchall()
      
    else:
      result = None
 
  # We failed, no result for you
  else:
    raise MysqlQueryFailure(str(last_error))

  return result


def Connect(host, user, password, database, port, reset=False):
  """Connect to the specified MySQL DB.  Wrapped to add features if required."""
  if MYSQL_MODULE == 'MySQLdb':
    conn = MySQLdb.Connect(host, user, password, database, port=port, cursorclass=MySQLdb.cursors.DictCursor)
    cursor = conn.cursor()
  
  elif MYSQL_MODULE == 'mysql.connector':
    conn = mysql.connector.connect(user=user, password=password, host=host, database=database)
    cursor = conn.cursor(cursor_class=MySQLCursorDict)
  
  else:
    raise Exception('Unknown MYSQL_MODULE: %s' % MYSQL_MODULE)

  return (conn, cursor)

