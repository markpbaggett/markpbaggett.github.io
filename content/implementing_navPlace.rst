Implementing navPlace: Desires and Possibilities for Consuming Applications
###########################################################################

:date: 2022-10-10
:tags: presentation-api, navplace
:category: iiif
:slug: implementing-navplace
:authors: Mark Baggett
:status: published
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

For our manifests, if a work has a MODS record with one or more matches for the XPATH query
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

navPlace on a Range
-------------------

In our IIIF manifests, ranges are added when we have structural metadata that describes the aboutness or specific parts of
an audio or video work. The range is based on pbcore data available in our MODS records. This is described in great detail
`in our cookbook <https://utk-iiif-cookbook.readthedocs.io/en/latest/contents/video.html#iiif-manifest>`_.

If a manifest has ranges and has cartographic coordinates as described above, any Ranges that relate to geographic places
are given a :code:`navPlace` property similar to what appears on the manifest. The :code:`navPlace` property is only added
if there is a match between its label and a :code:`subject[@authority]/geographic`. The one difference is that the label
will be the value of :code:`subject[@authority]/geographic` concatenated with " discussed in " and the title of the
manifest.

When the property is generated and added, it looks like this:

.. code-block:: json

    {
      "type": "Range",
      "id": "https:\/\/digital.lib.utk.edu\/notdereferenceable\/assemble\/manifest\/rfta\/8\/range\/places_mentioned\/1",
      "label": {
        "en": [
          "Chalet Village"
        ]
      },
      "navPlace": {
        "id": "https:\/\/digital.lib.utk.edu\/notdereferenceable\/featurecollection\/ChaletVillage\/1",
        "type": "FeatureCollection",
        "features": [
          {
            "id": "https:\/\/digital.lib.utk.edu\/notdereferenceable\/feature\/ChaletVillage\/1",
            "type": "Feature",
            "properties": {
              "label": {
                "en": [
                  "Chalet Village discussed in Interview with Seemona and Daniel Whaley, 2019-09-20"
                ]
              }
            },
            "geometry": {
              "type": "Point",
              "coordinates": [
                -83.5277175,
                35.7232049
              ]
            }
          }
        ]
      },
      "items": [
        {
          "type": "Canvas",
          "id": "https:\/\/digital.lib.utk.edu\/notdereferenceable\/assemble\/manifest\/rfta\/8\/canvas\/0#t=00:12:35,00:26:30"
        }
      ]
    }

Rendering navPlace Data in navPlace Viewer
------------------------------------------

The navPlace viewer provides different experiences for navPlace properties on the Manifest and the Range. When the
property is placed on Manifest, the :code:`label` of the Feature, the :code:`summary`, and links to open the manifest
in Universal Viewer and Mirador are associated with the marker associated with the geographic point. When a user clicks
on the point, a bubble expands with this information prominent. According to the README, it should also render the
thumbnail of the first canvas.

.. image:: https://utk-iiif-cookbook.readthedocs.io/en/latest/_images/navPlace_manifest.png
   :alt: Display of navPlace on Manifest

Properties on a range are rendered differently. The :code:`label` of the Feature is associated with the marker with a
similar user experience. Unfortunately, links to the viewers aren't present.

.. image:: https://utk-iiif-cookbook.readthedocs.io/en/latest/_images/navPlace_range.png
   :alt: Display of navPlace on Range

This makes sense. The range has an :code:`items` property that includes a canvas that targets the primary canvas in the
manifest with a temporal media fragment attached to the end. The URI for the part of the Canvas in the Range is not
dereferenceable. In order for a viewer to make use of the range, it would need to convert the :code:`id` to a
`content state URI <https://iiif.io/api/content-state/1.0/>`_ and the viewer would need to dereference it. Unfortunately,
navPlace viewer doesn't do this, and neither Univeral Viewer nor Mirador would dereference it currently if it did.

Content State and Desires for Consuming Applications
----------------------------------------------------

While the delivery of :code:`navPlace` data on manifests in navPlace viewer meets our needs, the delivery of the property
on range leaves a lot to be desired. The temporal data associated with the canvas inside the range is used to provide
navigation to specific points in an audio or video work in viewers such as Universal Viewer and our own RFTA canopy. For
instance, in our `Rising from the Ashes oral history portal <https://rfta.lib.utk.edu>`_, the range data is leveraged to
provide users a way to navigate to specific interview questions or geographic locations discussed within an oral history
work. When a user clicks a temporal based part, it causes the viewer to update to that specific point.

.. image:: images/becky_jackson_places.png
   :alt: Geographic Navigation in Becky Jackson Interview

In my opinion, this navigation experience would be better if it were a map with navigable points rather than the list
you see above. Furthermore, this could be enhanced even further by allowing the map to represent an entire collection of
manifests and rendering the navPlace properties on each. Then, users could start at the map and navigate to specific points
in works without starting at the work.

In order for this to happen, this will require two things. First, the map viewer or initial consuming application must
translate the range to a IIIF content state URI. `Content state <https://iiif.io/api/content-state/1.0/>`_ provides a
way to refer to a IIIF Presentation API resource, or a part of a resource, in a compact format that can be used to
initialize the view of that resource in any client. The :code:`id` associated with the range is not intended to be passed
to a viewer in the same form that its found in the manifest. Instead, it must be transformed into a content state URI. To
do this, the viewer needs to take the range and convert it to an annotation body like this:

.. code-block:: json

   {
     "@context": "http://iiif.io/api/presentation/3/context.json",
     "id": "https://digital.lib.utk.edu/assemble/content-states/1",
     "type": "Annotation",
     "motivation": ["contentState"],
     "target": {
       "id": "https://digital.lib.utk.edu/notderferenceable/assemble/manifest/rfta/8/range/places_mentioned/1",
       "type": "Range",
       "partOf": [
         {
           "id": "https://digital.lib.utk.edu/assemble/manifest/rfta/8",
           "type": "Manifest"
         }
       ]
     }
   }

Then, this JSON needs to be encoded according to the `IIIF Content State Specification <https://iiif.io/api/content-state/0.9/#6-content-state-encoding>`_
to ensure it is not vulnerable to corruption. The specification defines a two step process for doing this that uses both
the encodeURIComponent function available in web browsers, followed by Base 64 Encoding with URL and Filename Safe
Alphabet (“base64url”) encoding, with padding characters removed. The initial encodeURIComponent step allows any UTF-16
string in JavaScript to then be safely encoded to base64url in a web browser. The final step of removing padding removes
the “=” character which might be subject to further percent-encoding as part of a URL.

With Python, the JSON body above can be encoded into a content state URL like so:

.. code-block:: python

   import base64
   from urllib import parse
   import json

   def encode_content_state(plain_content_state):
       uri_encoded = parse.quote(plain_content_state, safe='')  # equivalent of encodeURIComponent
       utf8_encoded = uri_encoded.encode("UTF-8")
       base64url = base64.urlsafe_b64encode(utf8_encoded)
       utf8_decoded = base64url.decode("UTF-8")
       base64url_no_padding = utf8_decoded.replace("=", "")
       return base64url_no_padding

   if __name__ == "__main__":
       my_file = open('sample_range.json')
       x = json.load(my_file)
       encode_content_state(json.dumps(x))


This will return an encoded string that can decoded by a viewer that supports the specification.  An anchor can be built
that passes this string following content state convention:

.. code-block:: html

   <a href="https://link_to_viewer?iiif_content=JTdCJTIyJTQwY29udGV4dCUyMiUzQSUyMCUyMmh0dHAlM0ElMkYlMkZpaWlmLmlvJTJGYXBpJTJGcHJlc2VudGF0aW9uJTJGMyUyRmNvbnRleHQuanNvbiUyMiUyQyUyMCUyMmlkJTIyJTNBJTIwJTIyaHR0cHMlM0ElMkYlMkZkaWdpdGFsLmxpYi51dGsuZWR1JTJGYXNzZW1ibGUlMkZjb250ZW50LXN0YXRlcyUyRjElMjIlMkMlMjAlMjJ0eXBlJTIyJTNBJTIwJTIyQW5ub3RhdGlvbiUyMiUyQyUyMCUyMm1vdGl2YXRpb24lMjIlM0ElMjAlNUIlMjJjb250ZW50U3RhdGUlMjIlNUQlMkMlMjAlMjJ0YXJnZXQlMjIlM0ElMjAlN0IlMjJpZCUyMiUzQSUyMCUyMmh0dHBzJTNBJTJGJTJGZGlnaXRhbC5saWIudXRrLmVkdSUyRm5vdGRlcmZlcmVuY2VhYmxlJTJGYXNzZW1ibGUlMkZtYW5pZmVzdCUyRnJmdGElMkY4JTJGcmFuZ2UlMkZwbGFjZXNfbWVudGlvbmVkJTJGMSUyMiUyQyUyMCUyMnR5cGUlMjIlM0ElMjAlMjJSYW5nZSUyMiUyQyUyMCUyMnBhcnRPZiUyMiUzQSUyMCU1QiU3QiUyMmlkJTIyJTNBJTIwJTIyaHR0cHMlM0ElMkYlMkZkaWdpdGFsLmxpYi51dGsuZWR1JTJGYXNzZW1ibGUlMkZtYW5pZmVzdCUyRnJmdGElMkY4JTIyJTJDJTIwJTIydHlwZSUyMiUzQSUyMCUyMk1hbmlmZXN0JTIyJTdEJTVEJTdEJTdE">
      Link to Viewer
   </a>

Then, the consuming application can decode this URI according to the specification like so:

.. code-block:: python

   import base64
   from urllib import parse
   import json

   def decode_content_state(encoded_content_state):
       padded_content_state = restore_padding(encoded_content_state)
       base64url_decoded = base64.urlsafe_b64decode(padded_content_state)
       utf8_decoded = base64url_decoded.decode("UTF-8")
       uri_decoded = parse.unquote(utf8_decoded)
       return uri_decoded


   if __name__ == "__main__":
      content_state = "JTdCJTIyJTQwY29udGV4dCUyMiUzQSUyMCUyMmh0dHAlM0ElMkYlMkZpaWlmLmlvJTJGYXBpJTJGcHJlc2VudGF0aW9uJTJGMyUyRmNvbnRleHQuanNvbiUyMiUyQyUyMCUyMmlkJTIyJTNBJTIwJTIyaHR0cHMlM0ElMkYlMkZkaWdpdGFsLmxpYi51dGsuZWR1JTJGYXNzZW1ibGUlMkZjb250ZW50LXN0YXRlcyUyRjElMjIlMkMlMjAlMjJ0eXBlJTIyJTNBJTIwJTIyQW5ub3RhdGlvbiUyMiUyQyUyMCUyMm1vdGl2YXRpb24lMjIlM0ElMjAlNUIlMjJjb250ZW50U3RhdGUlMjIlNUQlMkMlMjAlMjJ0YXJnZXQlMjIlM0ElMjAlN0IlMjJpZCUyMiUzQSUyMCUyMmh0dHBzJTNBJTJGJTJGZGlnaXRhbC5saWIudXRrLmVkdSUyRm5vdGRlcmZlcmVuY2VhYmxlJTJGYXNzZW1ibGUlMkZtYW5pZmVzdCUyRnJmdGElMkY4JTJGcmFuZ2UlMkZwbGFjZXNfbWVudGlvbmVkJTJGMSUyMiUyQyUyMCUyMnR5cGUlMjIlM0ElMjAlMjJSYW5nZSUyMiUyQyUyMCUyMnBhcnRPZiUyMiUzQSUyMCU1QiU3QiUyMmlkJTIyJTNBJTIwJTIyaHR0cHMlM0ElMkYlMkZkaWdpdGFsLmxpYi51dGsuZWR1JTJGYXNzZW1ibGUlMkZtYW5pZmVzdCUyRnJmdGElMkY4JTIyJTJDJTIwJTIydHlwZSUyMiUzQSUyMCUyMk1hbmlmZXN0JTIyJTdEJTVEJTdEJTdE"
      decode_content_state(content_state)


Assuming the viewer supports content state, the video can then start at the same temporal media fragment as in the Beck
Jackson example above.

While this may all seem like a big ask, I personally want to IIIF and its various APIs to power our future repositories.
In order to make this happen, consuming applications must be able to recognize, encode, and decode content state. While
we aren't there yet, I am hopeful we will see this support in the future.