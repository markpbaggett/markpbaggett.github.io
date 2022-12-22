AUTHOR = 'Mark Baggett'
SITENAME = "Principia Nugae"
SITEURL = 'https://markpbaggett.github.io'

PATH = 'content'

TIMEZONE = 'US/Eastern'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = ()

# Social widget
SOCIAL = (('github', 'https://github.com/markpbaggett'),)

DEFAULT_PAGINATION = 3

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

PLUGINS = (
    'social',
)

# code blocks with line numbers
PYGMENTS_RST_OPTIONS = {'linenos': 'table'}

THEME = "themes/plumage"

# Plumage Things

DISCLAIMER = "Views expressed here are my own, but you should adopt them immediately."
SITE_THUMBNAIL = "https://avatars.githubusercontent.com/u/2692416?v=4"