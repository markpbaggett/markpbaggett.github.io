Mistakes Were Made: Creating id Properties for Embedded Resources in IIIF Presentation v3
#########################################################################################

:date: 2022-09-13
:tags: presentation-api
:category: iiif
:slug: iiif-id-property
:authors: Mark Baggett
:summary: A closer look at the id property in IIIF Presentation, how we got it wrong, and the unintended consequences
:description: A closer look at the id property in IIIF Presentation, how we got it wrong, and the unintended consequences


The :code:`id` property is without a doubt one of the most prevalent properties found throughout a IIIF manifest. As the API
documentation states, `all resource types <https://iiif.io/api/presentation/3.0/#5-resource-structure>`_ :code:`MUST`
have an :code:`id` property, and because of this the property is littered across the manifest. In our most basic work
type, simple image, the :code:`id` property is used 13 times. The definition of the :code:`id` property is simply
`the URI that identifies the resource <https://iiif.io/api/presentation/3.0/#32-technical-properties>`_.
At first glance, this seems relatively trivial but deeper inspection of the API docs demonstrates the need to understand
the property with a little more care.

The API documentation specifies some important details about the use of the :code:`id` property within an embedded resource.
An embedded resource refers to a resource where the entire JSON representation of a resource is found within another resource.
According to the API docs, the value of :code:`id` for an embedded resource :code:`MAY` be the URI of the embedding resource
with a unique fragment on the end, but only in the case that the embedded resource is not a :code:`Canvas`. The API
documentation goes further to state explicitly that a :code:`Canvas` must have its own URI without a fragment.

It's important to understand what is meant by fragment. `Section 5.3 of the IIIF Presentation API docs <https://iiif.io/api/presentation/3.0/#53-canvas>`_
explains that the canvas must not contain a fragment (a :code:`#` followed by further characters), as this would make it
impossible to refer to a segment of the Canvas’s area using the media fragment syntax of #xywh= for spatial regions,
and/or #t= for temporal segments. It also states that canvases :code:`MAY` be able to be dereferenced separately from the
Manifest via their URIs as well as being embedded.

A few years ago when we first implemented IIIF, this and other details regarding the :code:`id` property were things we
missed or didn't fully understand. To create :code:`id` properties for canvases, we concatenated a pattern to the end of
the value of the :code:`id` property of the manifest based on the order of the Canvas within the work.

.. code-block:: php
    :hl_lines: 3

    public function buildCanvas ($index, $uri, $pid) {

        $canvasId = $uri . '/canvas/' . $index;
        $title = $this->xpath->query('titleInfo[not(@type="alternative")]')[0];
        $canvas = (object) [
                "id" => $canvasId,
                "type" => 'Canvas',
                "label" => self::getLanguageArray($title, 'label', 'none'),
                "thumbnail" => self::buildThumbnail(200, 200)
        ];
    }

This concatenation results in a URI like below within the :code:`id` property of a Canvas:

.. code-block:: json
    :hl_lines: 4

    {
        "items": [
            {
                "id": "https://digital.lib.utk.edu/assemble/manifest/rftaart/74/canvas/0",
                "type": "Canvas",
                "items": []
            }
        ]
    }


While we concatenated a pattern to the end of the manifest's :code:`id` property to represent the canvas, this is not a
problem since the concatenated value does not contain a fragment (a :code:`#` followed by further characters. The issue
instead relates to other rules regarding the :code:`id` property that we didn't fully understand. According to the docs,
the value of the :code:`id` must be a string and a URI. The API documentation has these rules about :code:`id` property
naming conventions:

    The value must be a string, and the value must be an HTTP(S) URI for resources defined in this specification. If the resource is retrievable via HTTP(S), then the URI must be the URI at which it is published.

Additionally, the API docs include other important rules for producers and consumers regarding dereferencing URIs.

    The existence of an HTTP(S) URI in the id property does not mean that the URI will always be dereferencable. If the resource with the id property is embedded, it may also be dereferenceable. If the resource is referenced, it must be dereferenceable.

As the docs state, a canvas :code:`id` :code:`MAY` be dereferenceable. It doesn't have to be, but it :code:`MAY`. The
problem is that a request on the URI for our :code:`id` on the Canvas returns the entire manifest for the work the canvas
is embedded within.

While this may seem harmless, it is not and can have unintended consequences. Recently, I decided to experiment with adding
cartographic information found within our descriptive metadata to our IIIF manifests.  The catalyst for this was the
creation of the `Research Computing Group at Saint Louis University's <https://github.com/CenterForDigitalHumanities>`_
`navPlace viewer <https://github.com/CenterForDigitalHumanities/navplace-viewer/>`_. This viewer makes use of GeoJSON
found within a IIIF manifest in a :code:`navPlace` property. The :code:`navPlace` property is available in an
`extension <https://iiif.io/api/extension/navplace/>`_ to the IIIF Presentation API.  The extension describes the
property as such:

    The navPlace property identifies a single or multiple geographic areas pertinent to a resource using a GeoJSON Feature Collection containing one or more Features. These areas should be bounded discrete areas of the map akin to extents. These areas do not imply any level of accuracy, temporality, or state of existence.

The :code:`navPlace` property is allowed on IIIF collections, manifests, ranges, and canvases. The flexibility of the
extension and property causes challenges for consuming applications as its not clear where to find the property. This is
further complicated by the fact that the resources that contain embedded :code:`navPlace` properties may themsleves be embedded
or referenced.  Because of that, `navPlace viewer <https://github.com/CenterForDigitalHumanities/navplace-viewer/>`_
assumes that it should attempt to dereference all :code:`id` properties of resources that :code:`navPlace` can be
embedded in order to ensure all :code:`navPlace` properties are found.

Adding :code:`navPlace` to our manifests caused no problems, but trying to implement `navPlace viewer <https://github.com/CenterForDigitalHumanities/navplace-viewer/>`_
to make use of that content did. For the first time that we are aware of, a consuming application started to attempt to
dereference our canvases embedded in our manifests. It does this because its not sure whether the canvas is referenced
or embedded. For us, while we treat canvases as embedded resources, each of the :code:`id` properties found within a
canvas is derefernceable. According to the API specification, this is okay.  The only problem is that it is not
dereferenceable for the canvas but instead the manifest it is embedded within. This is also an issue with our ranges.
This causes an endless loop for the viewer and makes it impossible to serve our manifests.

Since this discovery, we have fixed this dereferencing issue. Now, :code:`id` properties are only dereferenceable if they
in fact represent the resource they are embedded within. Without `navPlace viewer <https://github.com/CenterForDigitalHumanities/navplace-viewer/>`_,
I'm unsure we would have ever realized we had a problem.

The viewer has raised other questions for me. 1. How should a
consuming application know that a resource is embedded or referenced? If the :code:`id` is derferenceable, should it be
assumed that it may contain additional properties not found within the current resource? 2. What do other viewers do? Do
Mirador, Universal Viewer, Clover, or IIIF Media Viewer have methods that perform the same level of dereferncing? The
IIIF Book contains a recipe entitled, `Simplest Manifest - Image <https://iiif.io/api/cookbook/recipe/0001-mvm-image/>`_.
The recipe contains the minimal number of properties to be able to show how to serve an image.  The recipe embeds all
the resources to ensure that users can understand what must be included.  That being said, if you were building a
presentation manifest producer, you could simplify the JSON here to just this as long the canvas is derefenceable:

.. code-block:: json

    {
      "@context": "http://iiif.io/api/presentation/3/context.json",
      "id": "https://iiif.io/api/cookbook/recipe/0001-mvm-image/manifest.json",
      "type": "Manifest",
      "label": {
        "en": [
          "Image 1"
        ]
      },
      "items": [
        {
          "id": "https://iiif.io/api/cookbook/recipe/0001-mvm-image/canvas/p1",
          "type": "Canvas",
        }
      ]
    }

Finally, if these resources can all be referenced, 3. how long may it take a viewer like `navPlace viewer <https://github.com/CenterForDigitalHumanities/navplace-viewer/>`_,
to parse and render a Collection resource that references thousands of book like objects with many pages and table of contents
objects that may be dereferencable, and 4. would it not be better to add a property for specifying whether a resource is
embedded or referenced so that the consuming application doesn't have to attempt dereferencing all these resources?

These questions are things that I'm thinking about and discussing with others, but this experience has reminded me how
important it is to read and understand a specification when implementing a new application.
