"""
Query Datasources

This is the module that wraps querying from different datasources.  

Hard coded pluggables.
"""


from log import log


class UnknownDatasourceType(Exception):
  """When we dont have a handler for this type of data source."""


def Query(datasource, spec_data):
  # MySQL database
  if datasource['type'] == 'mysql':
    # Dynamic import means that we dont need installed modules if this type isnt being used
    import mysql_datasource
    
    filter = spec_data['filter']
    
    result = mysql_datasource.Query(datasource, filter)

  # YAML data file
  elif datasource['type'] == 'yaml':
    pass

  # JSON data file
  elif datasource['type'] == 'json':
    pass

  else:
    raise UnknownDatasourceType('Unknown Data Source Type: %s' % datasource['type'])

  return result

