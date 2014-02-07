#!/usr/bin/env python2.6
"""
Template Manager

Fetches data from database, JSON or YAML file, and inserts the field results 
into one or more target template file.
"""

__author__ = 'Geoff Howland <geoff@gmail.com>'


import sys
import os
import getopt
import yaml

from util import query


def TemplateFromSpec(spec_path, datasources, options):
  """Process the templating based on the spec path and options.

  Returns: string, output of templating operation
  """
  # Get the spec data, just to test path
  spec_data = GetSpecData(spec_path, options)

  print 'Templating: %s' % spec_data['name']
  #print 'Sources: %s' % datasources

  # Select the datasource for querying
  if spec_data.get('datasource', None):
    datasource = datasources[spec_data['datasource']]
  else:
    datasource = None
  #print 'Source: %s' % datasource

  # Query the datasource for the data
  if spec_data.get('filter', None):
    data = query.Query(datasource, spec_data['filter'])
  else:
    data = []

  # Create an empty output string to append to
  output = ''

  # Fetch the template, if it exists, otherwise there is no generated templating
  if spec_data.get('template', None):
    template = open(spec_data['template']).read()
  else:
    template = ''

  # Template each item in data (rows)
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
      raise Exception('Spec data contained "template wrapper" statement, but file does not contain "%(template)s" string.  To use this without templated item generation, make template empty or do not add it, and add "%(template)s" anywhere and it will be empty.')

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
      template_specs[spec_key] = TemplateFromSpec(spec_key_path, datasources, options)

      # Template the results into our template output
      key_str = '%%(%s)s' % spec_key
      if key_str in output:
        output = output.replace(key_str, str(template_specs[spec_key]))


  return output


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
    Usage('Spec file "%s" does not exist' % command_options['datasources'])

  return spec_data


def ProcessSpecPath(spec_path, command_options):
  """Process a single specification path.  

  This could exit the program by calling Usage() in case of path errors.
  """
  try:
    datasources = yaml.load(open(command_options['datasources']))
  except Exception, e:
    Usage('Data Sources is not a YAML file or has a formatting error: %s: %s' % (datasources, e))

  # Get the spec data, just to test path
  spec_data = GetSpecData(spec_path, command_options)

  # If there is no path, then dont process this from the CLI invocation
  if spec_data.get('path', None) == None:
    print 'Skipping, no path target: %s' % spec_path
    return

  # Template All The Things: Master loop for Template Manager
  output = TemplateFromSpec(spec_path, datasources, command_options)

  # Save the master path
  open(spec_data['path'], 'w').write(output)

  print 'Output Successful: %s' % spec_data['path']


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
  print 'usage: %s [options] <spec file path>' % os.path.basename(sys.argv[0])
  print
  print 'Options:'
  print
  print '  -h, -?, --help             This usage information'
  print '  -v, --verbose              Verbose output'
  print '  -s, --datasources=[path]   Datasources YAML spec'
  print
  
  sys.exit(exit_code)


def Main(args=None):
  if not args:
    args = []
  
  long_options = ['help', 'verbose', 'datasources=']
  
  try:
    (options, args) = getopt.getopt(args, '?hvd:', long_options)
  except getopt.GetoptError, e:
    Usage(e)
  
  # Dictionary of command options, with defaults
  command_options = {}
  command_options['verbose'] = False
  command_options['datasources'] = 'conf/datasources.yaml'
  
  
  # Process out CLI options
  for (option, value) in options:
    # Help
    if option in ('-h', '-?', '--help'):
      Usage()
    
    # Verbose output information
    elif option in ('-v', '--verbose'):
      command_options['verbose'] = True
    
    # Verbose output information
    elif option in ('-s', '--datasources'):
      command_options['datasources'] = value


  # Ensure we at least have a command, it's required
  if len(args) < 1:
    Usage('No Spec file specified.  Spec file should be a YAML formatted ')
  

  # Process each of the arguments as a separate spec file
  for spec_path in args:
    ProcessSpecPath(spec_path, command_options)


if __name__ == '__main__':
  Main(sys.argv[1:])

