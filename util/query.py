"""
Query Datasources

This is the module that wraps querying from different datasources.  

Hard coded pluggables.
"""


from log import log


# If run from a command line, this will be set, and we will known whether ['verbose'] == True, etc
OPTIONS = None


class UnknownDatasourceType(Exception):
  """When we dont have a handler for this type of data source."""


def Query(datasource, spec_data, query_key='filter'):
  # MySQL database
  if datasource['type'] == 'mysql':
    # Dynamic import means that we dont need installed modules if this type isnt being used
    import mysql_datasource
    
    sql = spec_data[query_key]
    
    if OPTIONS and OPTIONS.get('verbose', False):
      log('Query: MySQL: SQL: %s' % sql)
    
    result = mysql_datasource.Query(datasource, sql)
    
    if OPTIONS and OPTIONS.get('verbose', False):
      log('Query: MySQL: Result: %s' % result)

  # YAML data file
  elif datasource['type'] == 'yaml':
    pass

  # JSON data file
  elif datasource['type'] == 'json':
    pass

  else:
    raise UnknownDatasourceType('Unknown Data Source Type: %s' % datasource['type'])

  return result

