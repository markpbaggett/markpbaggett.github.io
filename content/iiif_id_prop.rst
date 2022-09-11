Mistakes Were Made: Revisiting Our Implementation of the  IIIF Presentation id Property
#######################################################################################

:date: 2022-09-12
:status: draft
:tags: iiif, presentation-api
:category: iiif
:slug: iiif-id-property
:authors: Mark Baggett
:summary: A closer look at the id property in IIIF Presentation, how we got it wrong, and the unintended consequences of this mistake

The :code:`id` property is without a doubt one of the most prevalent properties found throughout a IIIF manifest. As the API
documentation states, `all resource types <https://iiif.io/api/presentation/3.0/#5-resource-structure>`_ :code:`MUST`
have an :code:`id` property, and because of this the property is littered across the manifest. The definition of the
:code:`id` property is simply `the URI that identifies the resource <https://iiif.io/api/presentation/3.0/#32-technical-properties>`_.
At first glance, this seems relatively trivial but deeper inspection of the API docs demonstrates the need to understand
the property with a little more care.

The API documentation specifies some important details about the use of the :code:`id` property within an embedded resource.
An embedded resource refers to a resource where the entire JSON representation of a resource is found within another resource.
According to the API docs, the value of :code:`id` for an embedded resource :code:`MAY` be the URI of the embedding resource
with a unique fragment on the end, but only in the case that the embedded resource is not a :code:`Canvas`. The API
documentation goes further to state explicitly that a :code:`Canvas` must have its own URI without a fragment.

A few years ago when we first implemented IIIF, this and other details regarding the :code:`id` property were things we
missed or flat out ignored. We did exactly what the documentation said not to do and created representative :code:`id`
properties for canvases by concatenating a unique fragment to the end:

.. code-block:: php
    :hl_lines: 3, 6

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

This results in a URI like below within the :code:`id` property of a Canvas:

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

The API docs include other pertinent details about the :code:`id` property.

    The value must be a string, and the value must be an HTTP(S) URI for resources defined in this specification. If the resource is retrievable via HTTP(S), then the URI must be the URI at which it is published.

Additionally, the API docs include other important rules for producers and consumers regarding dereferencing URIs.

    The existence of an HTTP(S) URI in the id property does not mean that the URI will always be dereferencable. If the resource with the id property is embedded, it may also be dereferenceable. If the resource is referenced (again, see the terminology section for an explanation of “referenced”), it must be dereferenceable. The definitions of the Resources give further guidance.



