Using the Borg Pattern to Cache Content in a Serverless Application
###################################################################

:date: 2022-08-25
:tags: singletons, serverless, libcal, wizzard
:category: python
:slug: libcal-borg-singleton
:authors: Mark Baggett
:summary: Why familiarizing yourself with design paterns and programming idioms is important even to novice coders.


As a librarian who occasionally writes code, my utilization of proven design patterns and programming idioms is mixed at
best. The truth is almost all of my programming and development skills were acquired on my own through trial and error
without the benefit of trainings, collaboration, or reading definitive literature such as
`Design Patterns: Elements of Reusable Object-Oriented Software <https://springframework.guru/gang-of-four-design-patterns/>`_.
Because of this, my approach to common programming problems is often convoluted or at least not the proven approach.

That being said, I was recently reminded why familiarizing myself with design patterns was well worth it (even when
I'm not consistently utilizing them). From time to time, late at night I will dive into a
`Medium article <https://medium.com/digirati-ch/progressive-enhancement-digital-objects-and-the-exploded-viewer-b0594d7bbb52>`_
or `Github repository <https://github.com/harvard-lil/warc-embed-netlify>`_ to fill in gaps in my knowledge about things
I'm curious about but not necessarily working on directly. Sometimes, that exploration may lead to deep dive in a
repository like `python-patterns <https://github.com/faif/python-patterns>`_ where contributors have collaborated to
explain how to implement common design patterns or programming idioms in Python. These deep dives may not be immediately
applicable but the introductions and explanations may plant a seed for future utilization.

In July, one of these previously planted seeds fully bloomed and helped solve a precarious programming challenging (for
me at least!). At UT Libraries, my department is responsible for maintaining the room booking system for students. Historically,
we have relied on a legacy `Sinatra <https://sinatrarb.com/>`_ application called archimedes.  Archimededs was developed
by a previous staff member who has been gone for nearly seven years.  Since he's been gone, we've worked to keep the
application going, but haven't done much to modernize or redevelop it because of lack of time and resources. In the system,
students reserve rooms via LibCal.  Each room has an attached RoomWizard from Steelcase. Archimedes sits in the middle
and queries LibCal for reservations students make every few minutes.  Each RoomWizard then makes requests to Archimedes
and is provided an XML response with its booking information formatted according to the `RoomWizard API <https://resources.steelcase.com/techsupport/TSUP/RoomWizard/Documentation/roomwizard_api.pdf>`_.

As legacy applications do, archimedes finally "broke" in late June of this year. Rather than spend a significant amount
of time refactoring the existing application, I decided to use the opportunity to rethink the original approach and
develop an application that I could more easily maintain. My primary goals were to:
1. develop something in pure Python (the language I'm most comfortable in), 2. design it to be serverless (for portability),
and 3. make sure the application did not need to interact with a database or any dynamic files on the file sytem (again
for portability).

The results of my efforts can be seen in `wizzard <https://github.com/markpbaggett/wizzard>`_ (named for Bob Odenkirk's
character on `Tom Goes to the Mayor <https://www.youtube.com/watch?v=fFtRIDad_I8>`_). Like its predecessor, wizzard
interfaces with the LibCal API and implements the RoomWizard connector API. The platform is built in
`flask <https://flask.palletsprojects.com/en/2.2.x/>`_ rather than pure Python. The application itself is quite simple.
There is a configuration file that defines LibCal authentication and how often API requests are made to LibCal. In order to be good stewards, we strive not to make unnecessary requests to LibCal.  Instead, the connector makes a
request to LibCal once every 10 minutes.  The results are cached, and each RoomWizard queries the cached results every
10 minutes.

.. image:: images/wizzard.jpeg
   :width: 600
   :alt: Bob Odenkirk as Wizzard from Tom Goes to the Mayor

.. code-block:: xml

    <kwe:result xmlns:kwe="http://www.appliancestudio.com/kwe/1.0/">
      <kwe:date>20220824</kwe:date>
      <kwe:time>094101</kwe:time>
      <kwe:result_code>0</kwe:result_code>
      <rb:bookings xmlns:rb="http://www.appliancestudio.com/rb/1.0/" room_id="LIB_605"/>
    </kwe:result>

Without question, the most complex piece of the application is handling cache. Again, for the sake of portability, I
strived to make sure there was no databases, datastores, or even the ability to write and read data from files on disks
(platforms like Heroku have dynamic disks that make this task impossible). In order to handle scheduling requests, I
planned from the beginning to use `Advanced Python Scheduler (apscheduler) <https://apscheduler.readthedocs.io/en/3.x/>`_.
With apscheduler, I planned to automate requests to the LibCal Booking API every 10 minutes and store that value in a
global variable in the controller. On init, the application would query LibCal and then update the response every 600
seconds.  If the application crashed or needed to be restarted, it would simply requery the API on startup.

While this strategy all made sense in my head, in retrospect it was naive and showed a glaring misunderstanding of
decoration, closures, and scope.  The main reason for this is that while the initial LibCal request would be done on
startup and initialization, all subsequent requests would be handled by a decorator related to the apscheduler task in
the controller. In Python, decoration is a design pattern that allows you to modify the behavior of a function. A
decorator is a function that takes in a function and returns an augmented copy of that function. With decorators, one
must keep scope in mind. In Python, functions define scope. Closures have access to the scope of the function that
returns them; the decorator’s scope. In other words, a decorator accepts a function and returns a closure. The closure
itself does not have access to global variables and cannot have a side affect that reassigns the global variable.

As I realized this problem, my mind immediately went back to reading about the Borg pattern in Python.  Also known as
the Monostate pattern, a Borg is a way to implement singleton behavior, but instead of having only one instance
of a class, there are multiple instances that share the same state. In other words, the focus is on sharing state
instead of sharing instance identity. By defining and using a Borg to handle cache, I could create an instance of the
Borg when the application starts up.  Then, I could create new instances of the Borg in the closure of the decorator
when new data is fetched. The new instance would be stored in memory just momentarily until the closure inside the
decorator was returned, but because it's a Borg the state  of the original would be updated.  In other words, I'd never
have more than two variables stored in memory, and one of those would only be there for a fraction of a second every 10
minutes or so.

The Borg itself looks magical, but conceptually it's quite simple. In Python, instance attributes are stored in a
attribute dictionary called __dict__. Usually, each instance will have its own dictionary, but the Borg pattern modifies
this so that all instances have the same dictionary. In the module I created to handle cache, the :code:`__shared_state`
attribute is a dictionary that is shared between all instances of my Borg. This is ensured by assigning
:code:`__shared_state` to the :code:`__dict__` variable when initializing new instances. Normally, other attributes
would be added to the instance's attribute dictionary, but, since the attribute dictionary itself is shared (again in
:code:`__shared_state`), all other attributes are also shared.

.. code-block:: python

    from typing import Dict


    class LibCalBorg:
        _shared_state: Dict[str, str] = {}

        def __init__(self):
            self.__dict__ = self._shared_state


    class LibCalCache(LibCalBorg):
        def __init__(self, current):
            super().__init__()
            self.current = current

Integrating the Borg into my other code is quite easy. On startup, a new instance of the Borg is created that stores API
cache from LibCal in a variable called :code:`all_current_bookings`.

.. code-block:: python

    from libcal.libcal import RoomBookings
    from cache.libcal import LibCalCache

    booking_data = RoomBookings('10024', arrow.utcnow().format('YYYYMMDD')).get_bookings()
    all_current_bookings = LibCalCache(booking_data)

Then, :code:`apscheduler` updates this every 600 seconds with an interval task. Technically, it defines a new variable
but it updates the state of the initial instance each time a new one is created.

.. code-block:: python

    @scheduler.task('interval', id='libcal', seconds=600, misfire_grace_time=900)
    def job2():
        """Updates the LibCal Cache that is passed to routes. Variable is a Borg Singleton that is garbage collected."""
        booking_data = RoomBookings('10024', arrow.utcnow().format('YYYYMMDD')).get_bookings()
        all_current_bookings_two = LibCalCache(booking_data)

Whenever the controller gets a request for an API response, that initial variable is always used.

.. code-block:: python

    @app.route('/rwconnector')
    def rw_connector():
        """Routes GET requests to /rwconnector.
        This route handles all traffic to /rwconnector. The route passes all HTTP parameters to the GetResponse in
        the commands package. Because of that, both about_connector and get_bookings routing is handled here.
        Returns:
            tuple: A tuple with the appropriate XML response from the related API at index 0, 200 at index 1, and a dict
            specifying the content type of the response at index 2.
        """
        x = GetResponse(request, all_current_bookings.current,
                        {'name': os.getenv('name'), 'version': os.getenv('version'), 'short': os.getenv('short')}
                        )
        return x.response, 200, {'Content-Type': 'text/xml; charset=utf-8'}

While there are likely countless ways the concept here could be done better, the challenge presented here and my approach
to solving it taught me a few things. First, it reiterated to me the importance of improving awareness of design patterns
and programming idioms even if you aren't using them daily.  By doing so, when you have a precarious challenge, you at
least are aware there are proven solutions. Second, you can only learn so much by reading and writing code alone. Often
when I hear librarians discuss "how to learn to code," they talk about tutorials, stack overflow, or carpentry. Occasionally,
you may hear better advice such as "write something to automate a task for you." The advice I normally give (and have
often felt is best) is to read other people's code. By doing this you are introduced to new ways of doing things which
can be critical when you are first starting out. But those things alone will only get you so far. Without awareness of
the Borg pattern, I'm not sure my code of what it attempts to solve would ever be meaningful or understood by an individual
who took my advice. This experience has convinced me that there is a definitive point where everyone who "codes" should familiarize themselves
the popular design patterns and programming idioms in the language and frameworks they use, and that time for me is now.