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

While we historically mapped this data, we never actually leveraged it and used it for display or navigation.
Recently, the `Center for Digital Humanities at Saint Louis University <https://github.com/CenterForDigitalHumanities/>`_
released a new `Beta viewer <https://centerfordigitalhumanities.github.io/navplace-viewer/>`_ that leverages
:code:`navPlace` properties in IIIF manifests and displays them on a map. Depending on where the data is found within the
manifest depends on how it functions in the viewer. Since we already had this data easily available, I decided to add
code to add :code:`navPlace` properties to our manifests via our `IIIF Presentation v3 service <https://github.com/utkdigitalinitiatives/iiif_assemble>`_.

The `IIIF Presentation Specification <https://iiif.io/api/presentation/3.0/>`_ does not provide a resource property
designed specifically for geographic location. Because of this, the `navPlace extension <https://iiif.io/api/extension/navplace/>`_
exists. The :code:`navPlace` `extension <https://iiif.io/api/extension/navplace/>`_ is not very prescriptive. The
property is allowed in most classes defined by the `IIIF presentation v3 specification <https://iiif.io/api/presentation/3.0/>`_.
According to the extension, a :code:`navPlace` property is allowed on a IIIF :code:`Collection`, :code:`Manifest`,
:code:`Range`, and / or :code:`Canvas`.

Rather than adding the property everywhere, I decided to start small by adding the properties only to :code:`Manifests`
and :code:`Ranges`. While one may argue that it makes most sense to add this information to the :code:`Collection`, I
would argue that the behavior of `navPlace viewer <https://centerfordigitalhumanities.github.io/navplace-viewer/>`_
makes this unnecessary. That's because the viewer attempts to dereference all :code:`id` properties in search of other
:code:`navPlace` properties that may appear in embedded classes. Because of this, a :code:`Collection` that references a
:code:`Manifest` with an :code:`navPlace` property will render those if the :code:`Collection` is passed to the viewer.

In the next few sections, I will describe our implementation, how the viewer consumes and makes use of them, and personal
desires for future consuming applications.

navPlace on Manifests
---------------------

For our manifests, if a work has a MODS record with a match for the XPATH query
:code:`subject[@authority="geonames"]/cartographics/coordinates`, it will get a :code:`navPlace` property on the
:code:`Manifest`. The :code:`navPlace` property always has three properties: :code:`id`, :code:`type`, and :code:`features`.
The value of the :code:`type` property is :code:`FeatureCollection`. The :code:`id` property is unique for the
:code:`FeatureCollection` and is equal to the base manifest :code:`id` concatenated with the value :code:`/feature-collection/1`.

.. code-block:: json

    {
        "navPlace":
            "id": "https://digital.lib.utk.edu/notdereferenceable/assemble/manifest/rfta/8/feature-collection/1",
            "type": "FeatureCollection",
            "features": []
    }

The :code:`features` property is an array. In the array are :code:`Feature` bodies for each matching value of
:code:`mods:subject[@authority="geonames"]/mods:cartographics/mods:coordinates`.  Each :code:`Feature` has the following
properties: :code:`id`, :code:`type`, :code:`properties`, and :code:`geometry`.

The :code:`type` property is always :code:`Feature`.  To ensure uniqueness, each :code:`Feature` :code:`id` is equal to
the :code:`id` of the :code:`id` of the Manifest concatenated with :code:`/feature/1`. The :code:`properties` property
is described `here <https://iiif.io/api/extension/navplace/#32-context-considerations-for-geojson-ld-properties>`_.
For our implementation, the :code:`label` property is the only thing used and it is equal to a concatenation of the Manifest
label and the related geographic location from the corresponding :code:`mods:subject[@authority="geonames]/mods:geographic`.
Finally, :code:`geometry` will always be a :code:`Point` with the cartographics in the :code:`coordinates` property in
the format of "longitude, latitude". It's always :code:`Point` because our data is always point data. For many of our
geographic place names, it would be much better to have polygon data, but this information isn't freely available from
GeoNames.

.. code-block:: json

    {
        "navPlace":
            {
                "id": "https://digital.lib.utk.edu/notdereferenceable/assemble/manifest/rfta/8/feature-collection/1",
                "type": "FeatureCollection",
                "features": [
                    {
                        "id":"https://digital.lib.utk.edu/notdereferenceable/assemble/manifest/rfta/8/feature/1",
                        "type":"Feature",
                        "properties":{
                           "label":{
                              "en":[
                                 "Interview with Seemona -- Gatlinburg"
                              ]
                           }
                        },
                        "geometry":{
                           "type":"Point",
                           "coordinates":[
                              -83.51189,
                              35.71453
                           ]
                        }
                    }
                ]
        }
    }

