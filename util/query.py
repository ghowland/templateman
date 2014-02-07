"""
Query Datasources

This is the module that wraps querying from different datasources.  

Hard coded pluggables.
"""


from log import Log


class UnknownDatasourceType(Exception):
  """When we dont have a handler for this type of data source."""


def Query(datasource, filter):
  if datasource['type'] == 'mysql':
    # Dynamic import means that we dont need installed modules if this type isnt being used
    import mysql_datasource

    result = mysql_datasource.Query(datasource, filter)

  else:
    raise UnknownDatasourceType('Unknown Data Source Type: %s' % datasource['type'])

  return result

