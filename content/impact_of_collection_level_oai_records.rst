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


Findings
--------

Conclusions
-----------
