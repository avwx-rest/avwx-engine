AVWX
====

Welcome to AVWX's documentation!

.. code-block:: python

  >>> import avwx
  >>> jfk_metar = avwx.Metar('KJFK')
  >>> jfk_metar.update()
  True
  >>> jfk_metar.data['Flight-Rules']
  'VFR'

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started.rst
   metar.rst
   taf.rst
   service.rst
   static.rst
   exceptions.rst

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
