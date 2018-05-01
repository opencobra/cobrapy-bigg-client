.. cobrapy-bigg-client documentation master file, created by
   sphinx-quickstart on Mon Apr 30 15:22:19 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to cobrapy-bigg-client's documentation!
===============================================

This project provides a bridge between `BiGG Models <http://bigg.ucsd.edu>`_ and cobrapy. It allows you to retrieve
entities from the database as cobrapy objects.


Examples
========

List available models
---------------------

.. code-block:: python

   from cobrapy_bigg_client import client
   models = client.list_models()


Returns:

+---+-------------+-------------+-----------+-------+-------------------------------------------+
|   | bigg_id     | metabolites | reactions | genes | organism                                  |
+===+=============+=============+===========+=======+===========================================+
| 0 | e_coli_core | 72          | 95        | 137   | Escherichia coli str. K-12 substr. MG1655 |
+---+-------------+-------------+-----------+-------+-------------------------------------------+
| 1 | iAB_RBC_283 | 342         | 469       | 346   | Homo sapiens                              |
+---+-------------+-------------+-----------+-------+-------------------------------------------+
| 2 | iAF1260     | 1668        | 2382      | 1261  | Escherichia coli str. K-12 substr. MG1655 |
+---+-------------+-------------+-----------+-------+-------------------------------------------+
| 3 | iAF1260b    | 1668        | 2388      | 1261  | Escherichia coli str. K-12 substr. MG1655 |
+---+-------------+-------------+-----------+-------+-------------------------------------------+
| 4 | iAF692      | 628         | 690       | 692   | Methanosarcina barkeri str. Fusar         |
+---+-------------+-------------+-----------+-------+-------------------------------------------+
| . | ...         | ...         | ...       | ...   | ...                                       |
+---+-------------+-------------+-----------+-------+-------------------------------------------+


Retrieve a model from the database
----------------------------------

.. code-block:: python

   from cobrapy_bigg_client import client
   # save it as a file
   client.download_model("e_coli_core")  #  writes the file in the current folder
   # get a cobra model
   model = client.download_model("e_coli_core", save=False)
   type(model)  # => cobra.core.model.Model

Analyse a reaction
------------------

.. code-block:: python

   from cobrapy_bigg_client import client
   model = client.download_model("e_coli_core", save=False)

   reaction = model.reaction.ACALD

   db_reaction = client.get_reaction(reaction)
   db_reaction = client.get_reaction(reaction.id)  # it also works with id

   type(db_reaciton)  # => cobra.core.reaction.Reaction

   db_reaction.annotation

   # Returns:
   # {'models_containing_reaction': ['iJN746',
   #   'iS_1188',
   #   'iECW_1372',
   #   'iNF517',
   #   'iPC815',
   #   'iRC1080',
   #   'iEcolC_1368',
   #   'iECP_1309',
   #  ..."}

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
