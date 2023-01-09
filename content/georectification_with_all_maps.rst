Experiments in Georectification with AllMaps: Imagining Future Possibilities for Maps in UTK Repository Systems
###############################################################################################################

:date: 2023-1-8
:tags: georectification, iiif
:category: maps
:slug: georectification_with_AllMaps
:authors: Mark Baggett
:summary: Using historic Knoxville Sanborn fire insurance maps to experiment with georectification using AllMaps and future possibilities for map-based works in our repository.
:description: Using historic Knoxville Sanborn fire insurance maps to experiment with georectification using AllMaps and future possibilities for map-based works in our repository.
:status: draft

Since graduate school in the late 2000s, I've been interested in georectification of historic maps and developing
applications where users can experience them on the web. In my role of building and delivering Digital Collections at
the University of Tennessee, I've had fleeting thoughts over the years in possibly georectifying our map content and
allowing our users to experience those in an online mapping service. Recently, I've been experimenting with
`Bert Spaan's <https://github.com/bertspaan>`_ awesome `AllMaps <https://allmaps.org/>`_.  This article details my
experiments and suggests potential ways of leveraging AllMaps or a similar technology with repository content in the
future.

What is Georectification
------------------------

According to Lincoln Mullen, georectification is:

    the process of taking an image of a map and referencing it to a spatial grid, so that the image of the map can be
    used as a layer in other maps, or so that the image of the map can in turn be used for associating points of
    interest with the spatial grid. For instance, one might georectify a map of a city, then use that georectified map
    to find the latitudes and longitudes of buildings on the map.

Great examples of georectification can be seen in Ben Schmidt's georectifed maps of the `Boston MBTA <http://benschmidt.org/mbta/>`_,
`New York MTA <http://benschmidt.org/mta/>`_, and `Washington DC Metro <http://benschmidt.org/dcmetro/>`_.

In order to georectify a map, one matches up points between a historical map and a modern method for tracking spatial
data. In most cases, this will be done algorithimically, but with AllMaps a more layman's approach is possible.

