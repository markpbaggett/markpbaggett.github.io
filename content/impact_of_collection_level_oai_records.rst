Is it Worth the Effort: Evaluating Whether Collection Level OAI Records Generate Traffic to Repositories and Digital Collections
################################################################################################################################

:date: 2023-1-2
:tags: analytics, discovery, collections, python
:category: analytics
:slug: impact-of-collection-level-oai-records
:authors: Mark Baggett
:summary: A Look into Work at the University of Tennessee to Create Collection Level OAI Records and How Much Traffic these Generate Long Term.
:description: A Look into Work at the University of Tennessee to Create Collection Level OAI Records and How Much Traffic these Generate Long Term.
:status: draft

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

Conclusions
-----------
