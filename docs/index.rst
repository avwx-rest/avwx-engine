AVWX
====

An aviation weather parsing library.

.. code-block:: python

  >>> import avwx
  >>> jfk_metar = avwx.Metar('KJFK')
  >>> jfk_metar.update()
  True
  >>> jfk_metar.data.flight_rules
  'VFR'

These docs could use some love, and I am not a writer. You can help by making a pull request on https://github.com/flyinactor91/AVWX-Engine

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started.rst
   metar.rst
   taf.rst
   service.rst
   static.rst
   structs.rst
   exceptions.rst

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
