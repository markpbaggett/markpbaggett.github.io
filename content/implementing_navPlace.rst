Implementing navPlace: Desires and Possiblities for Consuming Applications
##########################################################################

:date: 2022-10-05
:tags: presentation-api, navplace
:category: iiif
:slug: implementing-navplace
:authors: Mark Baggett
:status: draft
:summary: Describes our implementation of the navPlace extension in our IIIF manifests and desires for future consuming applications

For many years, the University of Tennessee Libraries has utilized `GeoNames <https://www.geonames.org/>`_ as a source
for dereferencing and reconciling geographic location data related to our works. The GeoNames API allows consumers to retrieve
many metadata elements about a place for free including "point" information in the form of latitude and longitude. The
relative ease of adding geographic data has encouraged us to add this data to our MODS records at
:code:`/mods/subject[geographic]/cartographics/coordinates` near its corresponding string and reference to the source
object in Geonames.

.. code-block:: xml
    :hl_lines: 4

   <mods:subject authority="geonames" valueURI="http://sws.geonames.org/4624443">
      <mods:geographic>Gatlinburg</mods:geographic>
      <mods:cartographics>
         <mods:coordinates>35.71453, -83.51189</mods:coordinates>
      </mods:cartographics>
   </mods:subject>

While we've historically mapped this data, we have never actually leveraged it to display in some sort of mapping service.
Recently, the `Center for Digital Humanities at Saint Louis University <https://github.com/CenterForDigitalHumanities/>`_
released a new `Beta viewer <https://centerfordigitalhumanities.github.io/navplace-viewer/>`_ that leverages
:code:`navPlace` properties in IIIF manifests and displays them on a map. Depending on where the data is found within the
manifest depends on how it functions in the viewer. Since we have this data easily available, I decided to add navPlace
properties to our manifests.

The :code:`navPlace` extension is not very prescriptive.  According to the specification, a :code:`navPlace` property is
allowed on a :code:`Collection`, :code:`Manifest`, :code:`Range`, or :code:`Canvas`. Rather than adding the property everywhere,
I decided to start small by adding them only to the :code:`Manifest` and the :code:`Range`. While one may argue that it
makes most sense to add this information to the :code:`Collection`, I would argue that the behavior of
`navPlace viewer <https://centerfordigitalhumanities.github.io/navplace-viewer/>`_ makes this unnecessary. That's because
the viewer attempts to dereference all :code:`id` properties for other :code:`navPlace` properties that may appear.



