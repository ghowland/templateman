"""
MySQL Datasource Handler

Wraps all the things we need to work with MySQL queries, for a data source.
"""


import MySQLdb
import MySQLdb.cursors

from log import Log


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
      #Log('Query: %s' % sql)
      cursor.execute(sql)
      
      #Log('Query complete, committing')
      
      # Force commit
      conn.commit()
      
      # Command didnt throw an exception
      success = True
    
    except MySQLdb.DatabaseError, e:
      (error_code, error_text) = e
      last_error = '%s: %s (Attempt: %s): %s: %s: %s' % (error_code, error_text, tries, host, database, sql)
      
      # Connect lost, reconnect
      if error_code in (2006, '2006'):
        Log('Lost connection: %s' % last_error)
        Connect(host, user, password, database, port, reset=True)
      else:
        Log('Unhandled MySQL query error: %s' % last_error)

  # If we made the query, get the result
  if success:
    result = cursor.fetchall()
 
  # We failed, no result for you
  else:
    raise MysqlQueryFailure(str(last_error))

  return result


def Connect(host, user, password, database, port, reset=False):
  """Connect to the specified MySQL DB.  Wrapped to add features if required."""
  conn = MySQLdb.Connect(host, user, password, database, port=port, cursorclass=MySQLdb.cursors.DictCursor)
  cursor = conn.cursor()

  return (conn, cursor)

