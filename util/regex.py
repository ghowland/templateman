"""
RegEx utilities
"""

REGEX_SPECIAL_CHARS = '()[]'

def SanitizeRegex(text):
  for char in REGEX_SPECIAL_CHARS:
    text = text.replace(char, '\\' + char)
  
  return text
