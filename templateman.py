#!/usr/bin/env python2
"""
Template Manager

Fetches data from database, JSON or YAML file, and inserts the field results 
into one or more target template file.

Can embed other text files into a template file, or process a new spec in-place using Commands like %%INCLUDE%%(path)%% or
%%PROCESSS%%(spec_path)%%.

TODO:
  - Interactive command line option to create a spec (optionally save it) interactively.  Saves having to work out examples.
"""


__author__ = 'Geoff Howland <geoff@gmail.com>'


import sys
import os
import getopt
import yaml

import util
from util.log import log
from util import query


class ConfigurationError(Exception):
  """Failure of syntax or completeness of a spec files configuration."""


class NoDataSource:
  """No data source was specified for our data.  So it's not an empty data set, its no data requested."""


def GetSpecData(spec_path, options):
  """Load the spec data from the spec path.

  This function could exit the program, if there is a spec data failure.
  """
  # If the Spec File path does not exist
  if not os.path.exists(spec_path):
    Usage('Spec file "%s" does not exist' % spec_path)


  try:
    spec_data = yaml.load(open(spec_path))
    
  except Exception, e:
    Usage('Spec file is not a YAML file or has a formatting error: %s: %s' % (spec_data, e))


  if type(spec_data) != dict:
    Usage('Spec file is not formatted as a Dictionary at the top level, which is needs to be:\n\n  Spec Data: %s' % str(spec_data)[:100])

  # If the Data Source path does not exist
  if not os.path.exists(options['datasources']):
    Usage('Spec file "%s" does not exist' % options['datasources'])


  return spec_data


def GetData(spec_data, datasources, options):
  """Handle data retrieval and filtering and stuff.  Returns usable data in list of dicts."""
  # Select the datasource for querying
  if spec_data.get('datasource', None):
    datasource = datasources[spec_data['datasource']]
    
  else:
    #NOTE(geoff): Dont warn or error here, as this may be intentional.  We can complain about it later.
    datasource = None

  #log('Source: %s' % datasource)

  # Query the datasource for the data, if a data source was specified
  if datasource:
    data = query.Query(datasource, spec_data)
  
  # Else, no data, raw source templating
  else:
    data = NoDataSource
  
  return data


def TemplateFromSpecPath(spec_path, datasources, options):
  """Template this spec path, after loading it."""
  # Get the spec data, just to test path
  spec_data = GetSpecData(spec_path, options)
  
  return TemplateFromSpec(spec_path, spec_data, datasources, options)
  

def TemplateFromSpec(spec_path, spec_data, datasources, options):
  """Process the templating based on the spec path and options.

  Returns: string, output of templating operation
  """
  log('Templating: %s' % spec_data['name'])
  #log('Sources: %s' % datasources)

  # Get our data, from specified source, with specified filter
  data = GetData(spec_data, datasources, options)

  # Create an empty output string to append to
  output = ''

  # Fetch the template, if it exists, otherwise there is no generated templating
  if spec_data.get('template', None):
    template = open(spec_data['template']).read()
  else:
    log('WARN: Using empty template text')
    template = ''


  # If we dont have any data source, the template is our output to start working
  if data == NoDataSource:
    output = template
  
  # Else, Template each item in data (rows)
  else:
    for item in data:
      item_output = str(template)
      
      # Template each key in item (columns)
      for (key, value) in item.items():
        key_str = '%%(%s)s' % key
        if key_str in template:
          item_output = item_output.replace(key_str, str(value))
      
      # Output the item...
      output += item_output
  
  


  # If we have a template wrapper
  #NOTE(ghowland): This stage must be second-to-last, as it wraps the generated template results in a pre-formatted template
  if spec_data.get('template wrapper', None):
    template_wrapper = open(spec_data['template wrapper']).read()

    if '%(template)s' not in template_wrapper:
      raise ConfigurationError('Spec data contained "template wrapper" statement, but file does not contain "%(template)s" string.  To use this without templated item generation, make template empty or do not add it, and add "%(template)s" anywhere and it will be empty.')

    # Replace the output with the template wrapper, and output inside it
    output = template_wrapper.replace('%(template)s', output)


  # If we have specs to template into this spec template (Recursion!)
  #NOTE(ghowland): This must be LAST in process order, because it 
  #   operates on the finished output, and requires template wrapping
  if spec_data.get('specs', None):
    template_specs = {}
    
    # Process each of the spec template targets
    for (spec_key, spec_key_path) in spec_data['specs'].items():
      # Generate the template output for this spec file
      template_specs[spec_key] = TemplateFromSpecPath(spec_key_path, datasources, options)
      
      # Template the results into our template output
      key_str = '%%(%s)s' % spec_key
      if key_str in output:
        output = output.replace(key_str, str(template_specs[spec_key]))

  return output


def ProcessSpec(spec_path, spec_data, options):
  """Process a single specification path.  

  This could exit the program by calling Usage() in case of path errors.
  """
  try:
    datasources = yaml.load(open(options['datasources']))
  except Exception, e:
    Usage('Data Sources is not a YAML file or has a formatting error: %s: %s' % (datasources, e))

  #TODO(g): REMOVE?  Better to default to STDOUT, or complain?  M
  #
  ## If there is no path, then dont process this from the CLI invocation
  #if spec_data.get('path', None) == None:
  #  log('Skipping, no path target: %s' % spec_path)
  #  return

  # Template All The Things: Master loop for Template Manager
  output = TemplateFromSpec(spec_path, spec_data, datasources, options)

  # Save the master path
  if (spec_data.get('path', None)):
    open(spec_data['path'], 'w').write(output)
    
    log('Output Successful: %s' % spec_data['path'])
  
  # Else
  else:
    if options['stdout']:
      print output
    else:
      log('ERROR: No path for final output, and option --stdout was not used.')


def ProcessSpecPath(spec_path, options):
  """Process a single specification path.  

  This could exit the program by calling Usage() in case of path errors.
  """
  # Get the spec data, just to test path
  spec_data = GetSpecData(spec_path, options)
  
  # Pass through to ProcessSpec(), which can be called directly with data as API
  ProcessSpec(spec_path, spec_data, options)


def Usage(error=None):
  """Print usage information, any errors, and exit.  
  If errors, exit code = 1, otherwise 0.
  """
  if error:
    print '\nerror: %s' % error
    exit_code = 1
  else:
    exit_code = 0
  
  print
  print 'usage: %s [options] <spec_file_path_1> [spec_file_path_2] [spec_file_path_3] ...' % os.path.basename(sys.argv[0])
  print
  print 'Options:'
  print
  print '  -h, -?, --help             This usage information'
  print '  -v, --verbose              Verbose output'
  print '  -S, --stdout               Print any output without a path to STDOUT'
  print '  -s, --datasources=[path]   Datasources YAML spec'
  print
  
  sys.exit(exit_code)


def Main(args=None):
  if not args:
    args = []
  
  long_options = ['help', 'verbose', 'stdout', 'datasources=']
  
  try:
    (options, args) = getopt.getopt(args, '?hvSd:', long_options)
  except getopt.GetoptError, e:
    Usage(e)
  
  # Dictionary of command options, with defaults
  command_options = {}
  command_options['verbose'] = False
  command_options['stdout'] = False
  command_options['datasources'] = 'conf/datasources.yaml'
  
  
  # Process out CLI options
  for (option, value) in options:
    # Help
    if option in ('-h', '-?', '--help'):
      Usage()
    
    # Verbose output information
    elif option in ('-v', '--verbose'):
      command_options['verbose'] = True
    
    # Print output without path to STDOUT
    elif option in ('-S', '--stdout'):
      command_options['stdout'] = True
    
    # Verbose output information
    elif option in ('-s', '--datasources'):
      command_options['datasources'] = value


  # Ensure we at least have a command, it's required
  if len(args) < 1:
    Usage('No Spec file specified.  Spec file should be a YAML formatted ')
  

  # Process each of the arguments as a separate spec file
  for spec_path in args:
    try:
      ProcessSpecPath(spec_path, command_options)
      
    except ConfigurationError, e:
      log('ERROR: %s: %s' % (spec_path, e))


if __name__ == '__main__':
  Main(sys.argv[1:])

