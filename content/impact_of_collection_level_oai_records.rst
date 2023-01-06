Is the Effort Worth It: Evaluating Whether Collection-level OAI Records Generate Traffic to Repositories and Digital Collections
################################################################################################################################

:date: 2023-1-2
:tags: discovery, collections
:category: analytics
:slug: impact-of-collection-level-oai-records
:authors: Mark Baggett
:summary: A Look into Work at the University of Tennessee to Create Collection Level OAI Records and How Much Traffic these Generate Long Term.
:description: A Look into Work at the University of Tennessee to Create Collection Level OAI Records and How Much Traffic these Generate Long Term.

At the University of Tennessee, we have a long history of relying on descriptive metadata and interoperability between
systems in order to generate traffic to our many digital collections. Historically, this interoperability has focused on
`OAI_PMH <https://www.openarchives.org/pmh/>`_ and sharing of metadata to various systems including the Libraries'
discovery tool, `One Search <https://utk.primo.exlibrisgroup.com/discovery/search?vid=01UTN_KNOXVILLE:01UTK&lang=en>`_,
and the `Digital Public Library of America <https://dp.la/>`_. In recent years, we've expanded our OAI-PMH work to include
collection-level metadata records that describe our various digital collections. This work is a little non-standard. Where
most modern digital library systems generate OAI-PMH records for works, the same is not true for collections. Because of
this, a manual process must be undertaken to create these collection level records and update them as necessary. It is
also one of the reasons why we still run and maintain our own OAI-PMH provider since our current repository syste does
not provide these collection-level records out-of-the-box. Furthermore, most modern systems organize OAI-PMH records
into `sets <http://www.openarchives.org/OAI/openarchivesprotocol.html#Set>`_ typically based on the collection or
collections to which a work belongs. Since we use a manual process to create these, we typically store all records about
collections in their own set.

As we work to migrate our digital collections to a new repository system that also does not have this functionality
built-in I thought it would be a good time to look at the value these collection-level records provide in order to help
us decide whether it's worth it to recreate this functionality in our new system.

Building a Dataset with Python
------------------------------

In this project, the primary question that I aim to answer is:

    Do collection-level metadata records in our discovery tool, OneSearch, generate traffic to our digital collections?

In order to answer this question, we can use the Google Analytics API and Python. In our current repository system, we
still use `Universal Analytics <https://support.google.com/analytics/answer/2790010?hl=en>`_ to collect analytics data.
We use the same property across all of digital collections pages regardless of platform which makes it very easy to
script something around the Google Analytics API and answer this question.

To use the API, we first need to generate an `api token <https://developers.google.com/analytics/devguides/reporting/core/v4>`_
associated with our Google Analytics property. These credentials will allow us to script queries using the same tools
found in the `Google Analytics GUI <https://analytics.google.com>`_.

Next, to do this with Python, we're going to utilize two packages outside of the Python standard library to help us
authenticate and use the api: `oauth2client <https://github.com/googleapis/oauth2client>`_ and
`Google API Client <https://pypi.org/project/google-api-python-client/>`_. With these two packages, we can create a simple
class that 1. connects to the Google Analytics API using our credentials and 2. finds traffic sources to our various
collection home pages where the home page is the initial landing page. Limiting the set this way will ensure that we only
count traffic if the user goes directly to the collection home page and not from another page in the repository to the
collection home page.

To start, let's import the two packages mentioned before and initialize a class that will allow us to connect to Google
Analytics using our credentials. The class will require a credentials file and the :code:`view_id` of the view of the
analytics property you are querying. Our Google Analytics property is divided into two separate views: All Website Data
and Cross Domain.  Since we have multiple subdomains here, we will need the latter. In our class, we will also have a
private method that authenticates and connects to our Google Analytics data.

.. code-block:: python

    from oauth2client.service_account import ServiceAccountCredentials
    from googleapiclient.discovery import build


    class AnalyticsConnection:
        def __init__(
                self,
                credentials,
                view_id,
        ):
            self.credentials_location = credentials
            self.view_id = view_id
            self.results = []
            self.connection = self.__connect()

        def __connect(self):
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_location, ["https://www.googleapis.com/auth/analytics.readonly"]
            )
            return build("analyticsreporting", "v4", credentials=credentials)

Next, let's add a method to this class that will allow us to query GoogleAnalytics for unique page views to collection
home pages where the home page is the landing page. Our method will take 4 arguments:  the collection home page, a token
to get the next page of results in case the results exceed the limit, the start date of our query, and the end date. We
will then set a variable for the request that uses this data to return the number of unique page views, the page path,
the full referrer, and the source where the page exactly matches the landing page path. **Note**: this exact match isn't
quite what we need and we will see why later. Next, in case there are multiple pages of results, we will add a conditional
that converts the Google Analytics token and add it to our request dictionary in the correct property to return the
correct page of results. Finally, we will do an HTTP GET request for the data.

.. code-block:: python

    def find_pages(self, page, token=None, start_date="45daysAgo", end_date="today"):
        request = {
            "reportRequests": [
                {
                    "viewId": self.view_id,
                    "dateRanges": [
                        {"startDate": start_date, "endDate": end_date}
                    ],
                    "metrics": [{"expression": "ga:uniquePageviews"}],
                    "dimensions": [{"name": "ga:pagePath"}, {"name": "ga:fullReferrer"}, {"name": "ga:source"}],
                    "pageSize": 10000,
                    "dimensionFilterClauses": [
                        {
                            "filters": [
                                {
                                    "operator": "EXACT",
                                    "dimensionName": "ga:landingPagePath",
                                    "expressions": [
                                        page
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        if token is not None:
            request['reportRequests'][0]['pageToken'] = str(token)
        return (
            self.connection.reports()
            .batchGet(
                body=request
            )
            .execute()
        )

Finally, we will add another method that will interface with the method above and retrieve results depending on whether
its the initial request or a subsequent. We will also add an exception in case the page we're querying has no results.

.. code-block:: python

    def process_pages(self, page, initial_pages=None, start_date=None, end_date=None):
        if initial_pages is None and start_date is not None and end_date is not None:
            current_set = self.find_pages(page, start_date=start_date, end_date=end_date)
        elif initial_pages is None:
            current_set = self.find_pages()
        else:
            current_set = initial_pages
        try:
            for view in current_set['reports'][0]['data']['rows']:
                self.results.append(view)
        except KeyError:
            pass
        if 'nextPageToken' in current_set['reports'][0]:
            new_request = self.find_pages(token=current_set['reports'][0]['nextPageToken'])
            return self.process_pages(new_request)
        else:
            return

Next, let's add some code that will allow us to securely pass our credentials and keep our list of collections separate
from our code. The list of collections will be stored as an array of strings in a :code:`collections` property in a yaml
file. Then for each collection home page in our list, we will pass it to the class we defined earlier and retrieve all
data over the past year.  Then, for each result, we will add its data to to a dictionary called :code:`all_sources` if
the result page path exactly matches the inital one.  This is critical because Google Analytics exact filters do not remove
results that include HTTP parameters. The data that we add to :code:`all_sources` will be the source and total views. If
the source already exists in the dict, we will updata its value to include the new views.

.. code-block:: python

    if __name__ == "__main__":
        import yaml
        collections = yaml.safe_load(open('config.yml', 'r'))['collections']
        connection = AnalyticsConnection(
            credentials="connection.json",
            view_id="118513499",
        )
        all_sources = {}
        for collection in collections:
            page = collection
            connection.process_pages(page=page, start_date='365daysago', end_date='today',)
            results = connection.results
            for result in results:
                """
                Must ensure that the ga:pagePath is the same as what's in the config because ga:landingPagePaths do not
                ignore HTTP parameters like queries
                (e.g. digital.lib.utk.edu/collections/islandora/object/collections:volvoices?page=16).
                """
                if result['dimensions'][0] == collection:
                    x = {
                        'source': result['dimensions'][1],
                        'views': int(result['metrics'][0]['values'][0]),
                        "actual_source": result['dimensions'][2]
                    }
                    if x['actual_source'] not in all_sources:
                        all_sources[x['actual_source']] = x['views']
                    else:
                        all_sources[x['actual_source']] += x['views']

In order to help interpret results, we will create another class.  This class will do several helpful things including:
1. show the results as percentages, 2. order the results from highest to lowest unique views, and 3. combine sources that
are similar (e.g. 'search.google.com' and 'google', 'lm.facebook.com', and 'l.facebook.com', etc.).

.. code-block:: python

    class AnalyticsInterpretter:
        def __init__(self, data):
            self.original_data = self.__sort_traffic_sources(self.__combine_similar_sources(data))
            self.total_views = self.__get_total_views(data)
            self.data_as_percentages = self.__as_percentages()

        @staticmethod
        def __get_total_views(data):
            total = 0
            for k, v in data.items():
                total += v
            return total

        def __as_percentages(self):
            x = {}
            for k, v in self.original_data.items():
                x[k] = '{:.1%}'.format(v/self.total_views)
            return x

        def count_percentages(self):
            total = 0
            for k, v in self.data_as_percentages.items():
                total = total + float(v.replace('%', ''))
            return total

        @staticmethod
        def __sort_traffic_sources(sortable):
            return dict(sorted(sortable.items(), key=lambda x: x[1], reverse=True))

        @staticmethod
        def __combine_similar_sources(data):
            sources_to_replace = {
                'search.google.com': 'google',
                't.co': 'twitter',
                'lm.facebook.com': 'facebook',
                'l.facebook.com': 'facebook',
                'us13.campaign-archive.com': 'mailchimp',
            }
            values_to_pop = []
            values_to_add = []
            for k, v in data.items():
                if k in sources_to_replace:
                    values_to_pop.append(k)
                    values_to_add.append({ sources_to_replace[k]: v})
            for value in values_to_pop:
                data.pop(value)
            for value in values_to_add:
                for k, v in value.items():
                    if k in data:
                        data[k] += v
                    else:
                        data[k] = v
            return data

Finally, we can pass our data in :code:`all_sources` to our :code:`AnalyticsInterpretter` as necessary.

Findings
--------

By reviewing our findings, we see that 89.1% of traffic directly to our 101 digital collection home pages come from 2
sources: Google and users that go directly to the home page via a bookmark or by typing in the website directly. Google
traffic makes up the majority of traffic at 46.6% (9119 views) while direct traffic accounts for 42.5% (8305 views).
The next most prominent traffic source is Bing making up 2.1% (412). Right after Bing, is OneSearch that makes up 1.3%
(255 views). The remaining traffic sources all accounts for less that 1% of total traffic to our home pages.

While OneSearch may be the 4th most prominent source of traffic to our digital collection home pages, its important to
realize that 255 views equates to just 2.5 views from OneSearch per home page per year. Furthermore, while Google makes
up the largest amount of direct traffic to collection home pages, it only accounts for 90 views per home page per year.
What this reaffirms is that access to collections likely comes from our website or from individual works within our
various collections.

A closer look at the data reveals even more interesting findings. We can use this same dataset to find out which
collection landing pages are found and accessed from Primo.  To do this, we just need to make a small modification to
our code above.

.. code-block:: python
    :hl_lines: 1, 13-19

    primo_collections = {}
    for collection in collections:
        page = collection
        connection.process_pages(page=page, start_date='365daysago', end_date='today',)
        results = connection.results
        for result in results:
            if result['dimensions'][0] == collection:
                x = {
                    'source': result['dimensions'][1],
                    'views': int(result['metrics'][0]['values'][0]),
                    "actual_source": result['dimensions'][2]
                }
                if "utk.primo.exlibrisgroup.com" in x['source']:
                    if collection not in primo_collections:
                        primo_collections[collection] = x['views']
                    else:
                        primo_collections[collection] += x['views']
    print(dict(sorted(primo_collections.items(), key=lambda x: x[1], reverse=True)))
    print(len(primo_collections))

When we do this, we see that 28 collections have at least 1 click through from Primo per year, but the vast amount of
searches go to one digital collection, :code:`digital.lib.utk.edu/collections/islandora/object/collections:univcat`.
This collection makes up 159 of the 255 results to Primo.  The next highest result is a 3 way tie at 13 per year:

.. code-block:: python

    {
        'digital.lib.utk.edu/collections/islandora/object/gsmrc:adams': 13,
        'digital.lib.utk.edu/collections/islandora/object/collections:volvoices': 13,
        'digital.lib.utk.edu/collections/islandora/object/collections:yrb': 13
    }

While the 159 click-throughs is rather large, it's important to realize that the works in this one collection get no
traffic once users are in our repository. You can see more about how are works are used `here <https://datalore.jetbrains.com/notebook/AzBJPE2emhR5koAu0CCrhb/VooSnItrSX9UFC6LmGGXTS/>`_.
We have hypothesized that this is because people are looking for our current data (which is not included here), but
maybe that is wrong, and we need to investigate this more deeply. Regardless, it's clear that this traffic does not lead
to users interacting with our content.

Conclusions
-----------

In my opinion, the 2.5 views that these OAI records account for per year do not justify creating these collection records
or developing code to automate this. Instead, we should focus more energy on search engine optimization of our works
(something that we don't do currently).

Also, we should try to understand why users are coming from Primo into University Catalogs, but not interacting with any
works once there.

More Information
----------------

If you want to play with this on your own, you can find my code in this `repository <https://github.com/markpbaggett/collection_query>`_.

If you want to see the long tail of our data as it exists today, you can see it below with the source followed by the
unique views where a visit went directly to a collection home page over the past year.

.. code-block:: python

    {'google': 9119, '(direct)': 8305, 'bing': 412, 'utk.primo.exlibrisgroup.com': 255, 'blounttn.org': 162,
     'trace.tennessee.edu': 134, 'yahoo': 106, 'twitter': 106, 'utk.instructure.com': 79, 'volnation.com': 77,
     'duckduckgo': 73, 'facebook': 70, 'newsletter': 34, 'lgapi-us.libapps.com': 34, 'utk.libwizard.com': 32,
     'en.wikipedia.org': 28, 'rfta-artists.netlify.app': 21, 'samvera-labs.github.io': 21,
     'api-00a97365.duosecurity.com': 20, 'localhost:5001': 19, 'ecosia.org': 17, 'm.facebook.com': 17, 'on3.com': 17,
     'word-view.officeapps.live.com': 16, 'ragtimepiano.ca': 15, 'trello.com': 12, 'baidu': 12, 'docs.google.com': 11,
     'cnu.libguides.com': 11, 'en.m.wikipedia.org': 11, 'libguides.bgsu.edu': 11, 'arcgis.com': 11,
     'dc.utk-hyku-staging.notch8.cloud': 10, 'wbir.com': 10, 'deploy-preview-14--rfta-artists.netlify.app': 9,
     'chadblack.net': 9, 'mail.google.com': 8, 'linkedin.com': 6, 'mathewjordan.github.io': 6, 'tn.dp.la': 6,
     'youtube.com': 6, 'artshelp.com': 6, 'search.aol.com': 6, 'apnews.com': 6, 'smithsonianmag.com': 6,
     'instructure.com': 6, 'learn.sewanee.edu': 6, 'linkin.bio': 4, 'utdailybeacon.com': 4, 'wildlandfirefighter.com': 4,
     'utk-test.utk-hyku.test': 4, 'knoxlib.org': 4, 'l.messenger.com': 4, 'onlinebooks.library.upenn.edu': 4,
     'eds.s.ebscohost.com': 4, 'oldknoxvillestuff.blogspot.com': 4, 'exlibrisgroup.com': 4, 'search.tennessee.edu': 4,
     'utk-dc.utk-hyku.test': 4, 'besjournals.onlinelibrary.wiley.com': 4, 'reddit.com': 4, 'sciencedirect.com': 4,
     'search.becovi.com': 4, 'crdl.usg.edu': 4, 'tnstate.libapps.com': 4, 'ancestry.com': 4, 'nypl.org': 4,
     'cas.tennessee.edu': 2, 'groups.google.com': 2, 'hardknoxwire.com': 2, 'hellbenderpress.org': 2,
     'jirautk.atlassian.net': 2, 'ohs.org.uk': 2, 'recut.in': 2, 'alphacrawler.pro': 2, 'app.asana.com': 2,
     'utk.utk-hyku.test': 2, 'thesmokies.com': 2, 'base-search.net': 2, 'oaister.on.worldcat.org': 2, 'pinterest.com': 2,
     'media.proquest.com': 2, 'startpage.com': 2, 'gilderlehrman.talentlms.com': 2, 'portside.org': 2, 'www4.bing.com': 2,
     'd2l.ship.edu': 2, 'lens.google.com': 2, 'deploy-preview-4--rfta-artists-official.netlify.app': 2, 'dogpile.com': 2,
     'ablc.sirsi.net': 2, 'journalfinder.wtcox.com': 2, 'instagram.com': 2, 'search.xfinity.com': 2, 'm.wikidata.org': 2,
     'facebook.com': 2, 't.e2ma.net': 2, 'analytics.google.com': 2, 'app.joinhandshake.com': 2, 'app.nearpod.com': 2,
     'go.gale.com': 2, 'journals.humankinetics.com': 2, 'journals.sagepub.com': 2, 'libapps.com': 2,
     'liveutk.sharepoint.com': 2, 'localhost:8180': 2, 'onlinelibrary.wiley.com': 2, 'statics.teams.cdn.office.net': 2,
     'utk.acalogadmin.com': 2, 'utk.libapps.com': 2, 'dlgadmin.galileo.usg.edu': 2, 'godort.libguides.com': 2,
     'tnstate.libguides.com': 2, 'mysites.taboolanews.com': 2, 'na02.alma.exlibrisgroup.com': 2, 'mailchimp': 2}
