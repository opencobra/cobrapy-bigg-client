# Copyright 2018 The Novo Nordisk Foundation Center for Biosustainability, DTU.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import os
import requests
import logging

from cachetools import LRUCache, cached

from pandas import DataFrame

from cobra.core.dictlist import DictList
from cobra.core.metabolite import Metabolite
from cobra.core.reaction import Reaction
from cobra.core.gene import Gene
from cobra.io import model_from_dict


API_VERSION = 'api_version'
BIGG_ID = "bigg_id"
BIGG_MODELS_VERSION = 'bigg_models_version'
CHARGE = "charge"
CHARGES = "charges"
COMPARTMENT_BIGG_ID = "compartment_bigg_id"
COMPARTMENTS_IN_MODELS = "compartments_in_models"
COPY_NUMBER = "copy_number"
COUNT = "count"
DATABASE_LINKS = "database_links"
ESCHER_MAPS = "escher_maps"
FORMULA = "formula"
FORMULAE = "formulae"
GENE_COUNT = "gene_count"
GENES = "genes"
GENE_REACTION_RULE = "gene_reaction_rule"
GENOME_NAME = "genome_name"
JSON_SIZE = "json_size"
LAST_UPDATED = 'last_updated'
MAP_NAME = "map_name"
MAT_SIZE = "mat_size"
METABOLITE_COUNT = "metabolite_count"
METABOLITES = "metabolites"
MODEL_BIGG_ID = "model_bigg_id"
MODELS = "models"
MODELS_CONTAINING_REACTION = "models_containing_reaction"
NAME = "name"
ORGANISM = "organism"
PROTEIN_SEQUENCE = "protein_sequence"
PSEUDOREACTION = "pseudoreaction"
REACTION_COUNT = "reaction_count"
RESULTS = "results"
RESULTS_COUNT = "results_count"
STOICHIOMETRY = "stoichiometry"
XML_SIZE = "xml_size"
XML_GZ_SIZE = "xml_gz_size"


LOGGER = logging.getLogger(__name__)
BASE_URL = "http://bigg.ucsd.edu/api/v2/"


METABOLITE_COMPARTMENT_REGEX = re.compile("^(.+)(_[a-z])$")


LRU_CACHE = LRUCache(maxsize=524)


class Version(object):
    """
    Version container.

    Attributes
    ----------
    version : str
        Database version.
    api_version : str
        Version of the API used.
    last_update : str
        Last update timestamp.
    """

    def __init__(self, version, api_version, last_update):
        self.version = version
        self.api_version = api_version
        self.last_update = last_update

    def __repr__(self):
        return "BiGG Database v%s (API %s). Last update: %s" % (self.version, self.api_version, self.last_update)


class ModelSummary(object):
    """
    Summary of a model in the database.

    Attributes
    ----------
    id : str
        The model id in the database.
    organism : str
        The organism name.
    genes : int
        The number of genes in the model.
    reactions : int
        The number of reactions in the model.
    metabolites : int
        The number of metabolites in the model.
    escher_maps : set
        The ids of escher maps correspoding to this model.
    file_sizes : dict
        The expected file size in different formats.
    genome : str
        The genome id.
    last_updated : str
        The timestamp.
    """

    def __init__(self, identifier, organism, genes, reactions, metabolites, escher_maps,
                 file_sizes, genome, last_updated):
        self.id = identifier
        self.organism = organism
        self.genes = genes
        self.reactions = reactions
        self.metabolites = metabolites
        self.escher_maps = escher_maps
        self.file_sizes = file_sizes
        self.genome = genome
        self.last_updated = last_updated

    def model(self):
        """
        Returns
        -------
        model : Model
            The cobra Model.

        """
        return download_model(self.id, save=False)


def database_version():
    """
    Retrieves the current version of BiGG database.

    Returns
    -------
    version : Version
        The current version information.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    response = requests.get(BASE_URL + "database_version")
    response.raise_for_status()

    data = response.json()
    return Version(data[BIGG_MODELS_VERSION], data[API_VERSION], data[LAST_UPDATED])


def download_model(model_id, file_format="json", save=True, path="."):
    """
    Download models from BiGG. You can chose to save the file or to return the JSON data.

    Parameters
    ----------
    model_id : str
        A valid id for a model in BiGG.
    file_format : str
        If you want to save the file, you can import the model in the following formats:
            1. json (JSON format)
            2. xml (SBML)
            3. xml.gz (SBML compressed)
            4. mat (MATLAB)
    save : bool
        If True, writes the model to a file with the model name (the path can be specified).
    path : str
        Specifies in which folder the model should be written if *save* is True.

    Returns
    -------
    model : Model
        If save is False, it returns the parsed model. If save is True, it saves the model in the requested format.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """

    if save:
        response = requests.get("http://bigg.ucsd.edu/static/models/%s.%s" % (model_id, file_format), stream=True)
        response.raise_for_status()
        with open(os.path.join(path, "%s.%s" % (model_id, file_format)), "wb") as model_file:
            for block in response.iter_content(1024):
                model_file.write(block)
    else:
        response = requests.get("http://bigg.ucsd.edu/static/models/%s.json" % model_id, stream=True)
        response.raise_for_status()
        return model_from_dict(response.json())


def model_details(model_id):
    """
    Summarize the model. The summary contains number of genes, reactions, and metabolites, the available escher, and
    the expected file sizes of the model in compatible formats.

    Parameters
    ----------
    model_id : str
        A valid id for a model in BiGG.

    Returns
    -------
    summary : ModelSummary
        A summary of the model content.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    response = requests.get(BASE_URL + "models/%s" % model_id)
    response.raise_for_status()
    data = response.json()
    file_sizes = {"xml": data[XML_SIZE], "json": data[JSON_SIZE], "mat": data[MAT_SIZE], "xml.gz": data[XML_GZ_SIZE]}
    escher_maps = set()
    for map_data in data[ESCHER_MAPS]:
        escher_maps.add(map_data[MAP_NAME])

    return ModelSummary(model_id, data[ORGANISM], data[GENE_COUNT], data[REACTION_COUNT], data[METABOLITE_COUNT],
                        escher_maps, file_sizes, data[GENOME_NAME], data[LAST_UPDATED])


def list_models():
    """
    Lists all models available in BiGG.

    Returns
    -------
    models : DataFrame
        A table summarizing the models.

    Raises
    ------
    requests.HTTPError
        If the request has failed.

    """
    response = requests.get(BASE_URL + "models/")
    response.raise_for_status()
    data = response.json()

    LOGGER.info("Found %i models", data[RESULTS_COUNT])

    models = DataFrame(columns=["bigg_id", "metabolites", "reactions", "genes", "organism"])
    for i, d in enumerate(data[RESULTS]):
        models.loc[i] = [d[BIGG_ID], d[METABOLITE_COUNT], d[REACTION_COUNT], d[GENE_COUNT], d[ORGANISM]]

    return models


def list_reactions():
    """
    List all reactions available in BiGG. The reactions do not contain stoichiometry.
    To retrieve the full reaction use *get_reaction*.

    Returns
    -------
    reactions : list
        A list of Reaction.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    data = _get("reactions", None, None)

    LOGGER.info("Found %i reactions", data[RESULTS_COUNT])
    reactions = DictList()
    for reaction_data in data[RESULTS]:
        reaction_id = reaction_data[BIGG_ID]
        if reaction_id in reactions:
            continue
        reaction = Reaction(id=reaction_data[BIGG_ID], name=reaction_data[NAME])
        reactions.append(reaction)

    return reactions


def list_model_reactions(model_id):
    """
    List all reactions in a model.

    Parameters
    ----------
    model_id : str
        A valid id for a model in BiGG.

    Returns
    -------
    reactions : DictList
        All model reactions.

    Raises
    ------
    requests.HTTPError
        If the request has failed.

    """
    data = _get("reactions", None, model_id)

    LOGGER.info("Found %i reactions", data[RESULTS_COUNT])
    reactions = DictList()
    for reaction_data in data[RESULTS]:
        reaction_id = reaction_data[BIGG_ID]
        if reaction_id in reactions:
            continue
        reaction = Reaction(id=reaction_id, name=reaction_data[NAME])
        reactions.append(reaction)

    return reactions


def get_reaction(reaction_or_id, metabolites=None, genes=None):
    """
    Retrieve a reaction from BiGG.

    Parameters
    ----------
    reaction_or_id : Reaction, str
        A valid id for a reaction in BiGG.
    metabolites : dict
        A cache with metabolites retrieved previously.
    genes : dict
        A cache with genes retrieved previously.

    Returns
    -------
    reaction : Reaction
        The reaction described in the result. If there are no copies, the reaction is completely described.

    Raises
    ------
    requests.HTTPError
        If the request has failed.

    """
    if genes is None:
        genes = {}
    if metabolites is None:
        metabolites = {}

    if isinstance(reaction_or_id, Reaction):
        reaction = reaction_or_id
        reaction_id = reaction.id
    elif isinstance(reaction_or_id, str):
        reaction_id = reaction_or_id
        reaction = None
    else:
        raise ValueError(reaction_or_id)

    data = _get("reactions", reaction_id, None)

    LOGGER.info("Found reaction %s", data[NAME])

    if reaction is None:
        reaction = Reaction(id=reaction_id, name=data[NAME])

    reaction = _build_reaction(data, reaction, 0, genes, None, metabolites, None)
    return reaction


def get_model_reaction(model_id, reaction_or_id, metabolites=None, genes=None):
    """
    Retrieve a reaction in the context of a model from BiGG.

    Parameters
    ----------
    model_id : str
        The identifier of the model.
    reaction_or_id : Reaction, str
        A valid id for a reaction in BiGG.
    metabolites : dict
        A cache with metabolites retrieved previously.
    genes : dict
        A cache with genes retrieved previously.

    Returns
    -------
    reaction : Reaction
        The reaction described in the result. If there are no copies, the reaction is completely described.
    copies : list
        A list of reactions with stoichiometry and GPR.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    if genes is None:
        genes = {}
    if metabolites is None:
        metabolites = {}

    if isinstance(reaction_or_id, Reaction):
        reaction = reaction_or_id
        reaction_id = reaction.id
    elif isinstance(reaction_or_id, str):
        reaction_id = reaction_or_id
        reaction = None
    else:
        raise ValueError(reaction_or_id)

    data = _get("reactions", reaction_id, model_id)

    LOGGER.info("Found reaction %s (%i copies)", data[NAME], data[COUNT])

    if reaction is None:
        reaction = Reaction(id=reaction_id, name=data[NAME])

    reaction.annotation[PSEUDOREACTION] = data[PSEUDOREACTION]
    if ESCHER_MAPS not in reaction.annotation:
        reaction.annotation[ESCHER_MAPS] = data[ESCHER_MAPS]
    else:
        reaction.annotation[ESCHER_MAPS] += data[ESCHER_MAPS]

    reaction.annotation[DATABASE_LINKS] = data[DATABASE_LINKS]

    copies_data = data[RESULTS]
    copies = []
    if data[COUNT] == 1:  # singe copy
        copy_data = copies_data[0]
        reaction = _build_reaction(copy_data, reaction, 0, genes, None, metabolites, None)
    else:
        _genes = {}
        _metabolites = {}
        for copy_data in copies_data:
            _copy = _build_reaction(copy_data, reaction, data[COPY_NUMBER], genes, _genes, metabolites, _metabolites)
            copies.append(_copy)

    return reaction, copies


def list_metabolites():
    """
    List all metabolites present in BiGG.

    Returns
    -------
    metabolites : DictList
        A list of metabolites.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    data = _get("metabolites", None, None)

    LOGGER.info("Found %i metabolites", data[RESULTS_COUNT])
    metabolites = DictList()
    for metabolites_data in data[RESULTS]:
        metabolite = Metabolite(id=metabolites_data[BIGG_ID], name=metabolites_data[NAME])
        metabolites.append(metabolite)

    return metabolites


def list_model_metabolites(model_id):
    """
    List all metabolites in a model.

    Parameters
    ----------
    model_id : str
        A model id present in BiGG.

    Returns
    -------
    metabolites : DictList
        A list of metabolites.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    data = _get("metabolites", None, model_id)

    LOGGER.info("Found %i reactions", data[RESULTS_COUNT])
    metabolites = DictList()

    for metabolites_data in data[RESULTS]:
        metabolite_id = metabolites_data[BIGG_ID] + "_" + metabolites_data[COMPARTMENT_BIGG_ID]
        if metabolite_id in metabolites:
            continue
        metabolite = Metabolite(id=metabolite_id, name=metabolites_data[NAME])
        metabolites.append(metabolite)

    return metabolites


def get_metabolite(metabolite_or_id):
    """
    Retrieve a metabolite from BiGG.

    Parameters
    ----------
    metabolite_or_id : Metabolite, str
        A valid id for a reaction in BiGG.

    Returns
    -------
    metabolites : Metabolite
        The universal metabolite (with different possible charges and formulae in annotation).
    species : dict
        The possible different metabolite species in different compartments.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """

    if isinstance(metabolite_or_id, str):
        metabolite_id = metabolite_or_id
    elif isinstance(metabolite_or_id, Metabolite):
        metabolite = metabolite_or_id
        metabolite_id = metabolite.id
    else:
        raise ValueError(metabolite_or_id)

    match = METABOLITE_COMPARTMENT_REGEX.match(metabolite_id)
    if match:
        universal_metabolite_id = match.group(1)
    else:
        universal_metabolite_id = metabolite_id

    try:
        data = _get("metabolites", universal_metabolite_id, None)
    except requests.HTTPError:
        data = _get("metabolites", metabolite_id, None)
    LOGGER.info("Found metabolite %s", metabolite_id)

    metabolite = Metabolite(id=metabolite_id, name=data[NAME])

    if data[CHARGES]:
        metabolite.charge = data[CHARGES][0]
    if data[FORMULAE]:
        metabolite.formula = data[FORMULAE][0]

    metabolite.annotation[CHARGES] = data[CHARGES]
    metabolite.annotation[FORMULAE] = data[FORMULAE]
    metabolite.annotation[DATABASE_LINKS] = data[DATABASE_LINKS]
    metabolite.annotation[MODELS] = set()

    species = {}

    for compartment_data in data[COMPARTMENTS_IN_MODELS]:
        compartment_id = compartment_data[BIGG_ID]
        if compartment_id not in species:
            metabolite_copy = metabolite.copy()
            metabolite_copy.id = metabolite_id + "_" + compartment_id
            metabolite_copy.compartment = compartment_id
            species[compartment_id] = metabolite_copy

        species[compartment_id].annotation[MODELS].add(compartment_data[MODEL_BIGG_ID])

    return metabolite, species


def get_model_metabolite(model_id, metabolite_id):
    """
    Retrieve a metabolite in the context of a model from BiGG.

    Parameters
    ----------
    metabolite_id : str
        A valid id for a reaction in BiGG.
    model_id : str
        A valid id for a model in BiGG.

    Returns
    -------
    metabolite : Metabolite
        The metabolite in the model.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    data = _get("metabolites", metabolite_id, model_id)
    LOGGER.info("Found metabolite %s", metabolite_id)

    metabolite = Metabolite(id=metabolite_id, charge=data[CHARGE],
                            formula=data[FORMULA], compartment=data[COMPARTMENT_BIGG_ID])

    metabolite.annotation[DATABASE_LINKS] = data[DATABASE_LINKS]

    return metabolite


def list_model_genes(model_id):
    """
    List all genes in a model.

    Parameters
    ----------
    model_id : str
        A valid id for a model in BiGG.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """
    data = _get("genes", None, model_id)

    LOGGER.info("Found %i genes", data[RESULTS_COUNT])
    genes = []
    for gene_data in data[RESULTS]:
        gene = Gene(id=gene_data[BIGG_ID], name=gene_data[NAME])
        gene.annotation[ORGANISM] = gene_data[ORGANISM]
        genes.append(gene)

    return genes


def get_model_gene(model_id, gene_or_id):
    """
    Retrieve a gene in the context of a model from BiGG.

    Parameters
    ----------
    model_id : str
        A valid id for a model in BiGG.
    gene_or_id : str, Gene
        A Gene or a valid id for a gene in BiGG.

    Returns
    -------
    gene : Gene
        A cobra Gene.

    Raises
    ------
    requests.HTTPError
        If the request has failed.
    """

    if isinstance(gene_or_id, str):
        gene_id = gene_or_id
    elif isinstance(gene_or_id, Gene):
        gene_id = gene_or_id.id
    else:
        raise ValueError(gene_or_id)

    data = _get("genes", gene_id, model_id)

    LOGGER.info("Found gene %s", gene_id)

    gene = Gene(id=gene_id, name=data[NAME])
    gene.annotation[DATABASE_LINKS] = data[DATABASE_LINKS]
    gene.annotation[PROTEIN_SEQUENCE] = data[PROTEIN_SEQUENCE]

    return gene


@cached(LRU_CACHE)
def _get(entry_type, entry_id, model_id):
    if entry_id is None:
        if model_id is None:
            response = requests.get(BASE_URL + "universal/%s" % entry_type)
        else:
            response = requests.get(BASE_URL + "models/%s/%s" % (model_id, entry_type))
    else:
        if model_id is None:
            response = requests.get(BASE_URL + "universal/%s/%s" % (entry_type, entry_id))
        else:
            response = requests.get(BASE_URL + "models/%s/%s/%s" % (model_id, entry_type, entry_id))

    response.raise_for_status()
    return response.json()


def _build_reaction(copy_data, reaction, copy_number=0, genes=None,
                    _genes=None, metabolites=None, _metabolites=None):
    _genes = _genes or {}
    _metabolites = _metabolites or {}
    genes = genes or _genes
    metabolites = metabolites or _metabolites

    if copy_number > 0:
        reaction_copy = reaction.copy()
        reaction_copy.id = reaction.id + "_%i" % copy_data[COPY_NUMBER]
    else:
        reaction_copy = reaction

    if GENES in copy_data:
        genes_set = set()
        for gene_data in copy_data[GENES]:
            gene_id = gene_data[BIGG_ID]
            if gene_id in genes:
                gene = genes[gene_id]
            elif gene_id in _genes:
                gene = _genes[gene_id]
            else:
                gene = Gene(gene_id, gene_data[NAME])
                _genes[gene_id] = gene

            genes_set.add(gene)
            reaction_copy._genes = frozenset(genes_set)

        reaction_copy._gene_reaction_rule = copy_data[GENE_REACTION_RULE]
    elif MODELS_CONTAINING_REACTION in copy_data:
        reaction_copy.annotation[MODELS_CONTAINING_REACTION] = [model['bigg_id'] for model
                                                                in copy_data[MODELS_CONTAINING_REACTION]]

    if METABOLITES in copy_data:
        stoichiometry = {}
        for metabolite_data in copy_data[METABOLITES]:
            universal_metabolite_id = metabolite_data[BIGG_ID]
            metabolite_id = universal_metabolite_id + "_" + metabolite_data[COMPARTMENT_BIGG_ID]
            if metabolite_id in _metabolites:
                metabolite = _metabolites[metabolite_id]
            elif universal_metabolite_id in metabolites:
                metabolite = metabolites[universal_metabolite_id].copy()
                metabolite.id = metabolite_id
                metabolite.compartment = metabolite_data[COMPARTMENT_BIGG_ID]
                _metabolites[metabolite_id] = metabolite
            else:
                metabolite = Metabolite(id=metabolite_id, name=metabolite_data[NAME],
                                        compartment=metabolite_data[COMPARTMENT_BIGG_ID])
                _metabolites[metabolite_id] = metabolite

            stoichiometry[metabolite] = metabolite_data[STOICHIOMETRY]
        reaction_copy.add_metabolites(stoichiometry, combine=False)

    return reaction_copy
