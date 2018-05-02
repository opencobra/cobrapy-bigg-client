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

import six

import pytest
import requests

from pandas import DataFrame

from cobra.core.gene import Gene
from cobra.core.metabolite import Metabolite
from cobra.core.reaction import Reaction
from cobra.core.model import Model

from cobrapy_bigg_client import client


COPY_REACTION = re.compile("^[A-Z1-9]+_\d+$")


def test_get_database_version():
    version = client.database_version()
    assert isinstance(version, client.Version)
    assert version.api_version == "v2"


def test_list_models():
    models = client.list_models()
    assert isinstance(models, DataFrame)
    assert "bigg_id" in models.columns
    assert "metabolites" in models.columns
    assert "reactions" in models.columns
    assert "organism" in models.columns


def test_model_details(bigg_model):
    model_summary = client.model_details(bigg_model.id)
    assert model_summary.metabolites == len(bigg_model.metabolites)
    assert model_summary.genes == len(bigg_model.genes)
    assert model_summary.reactions == len(bigg_model.reactions)
    model = model_summary.model()

    assert isinstance(model, Model)
    assert model_summary.metabolites == len(model.metabolites)
    assert model_summary.reactions == len(model.reactions)
    assert model_summary.genes == len(model.genes)


def test_download_model(model_format, bigg_model_id, tmpdir):
    path = tmpdir.mkdir("models")
    final_doc = path.join("%s.%s" % (bigg_model_id, model_format))
    client.download_model(bigg_model_id, model_format, True, path.strpath)
    assert os.path.exists(final_doc.strpath)
    assert os.path.isfile(final_doc.strpath)
    assert os.path.getsize(final_doc.strpath) > 0


def test_model_reactions(bigg_model_id):
    reactions = client.list_model_reactions(bigg_model_id)

    for i in range(10):
        basic_reaction = reactions[i]
        assert isinstance(basic_reaction, Reaction)

        reaction, copies = client.get_model_reaction(bigg_model_id, basic_reaction)

        assert isinstance(reaction, Reaction)
        assert reaction.id == basic_reaction.id
        assert reaction.name == basic_reaction.name
        assert client.DATABASE_LINKS in reaction.annotation


def test_model_metabolites(bigg_model):
    metabolites = client.list_model_metabolites(bigg_model.id)
    assert len(metabolites) == len(bigg_model.metabolites)

    for i in range(10):
        metabolite = metabolites[i]
        model_metabolite = bigg_model.metabolites.get_by_id(metabolite.id)

        full_metabolite = client.get_model_metabolite(bigg_model.id, metabolite.id)
        assert full_metabolite.id == metabolite.id
        assert full_metabolite.id == model_metabolite.id

    with pytest.raises(requests.HTTPError):
        client.get_model_metabolite(bigg_model.id, "non-existent")


def test_get_metabolite(metabolite):
    cobra_metabolite, species = client.get_metabolite(metabolite.universal_bigg_id)
    assert cobra_metabolite.id == metabolite.universal_bigg_id
    assert all(formula in metabolite.formulae for formula in cobra_metabolite.annotation["formulae"])
    assert all(charge in metabolite.charges for charge in cobra_metabolite.annotation["charges"])


def test_fail_get_metabolite():
    with pytest.raises(requests.HTTPError):
        client.get_metabolite("non-existent")

    with pytest.raises(ValueError):
        client.get_metabolite(1)


def test_get_reaction(reaction):
    model = Model()
    cobra_reaction = client.get_reaction(reaction.name)
    _reaction = Reaction(reaction.name)
    model.add_reactions([_reaction])
    _reaction.build_reaction_from_string(reaction.reaction_string)
    assert cobra_reaction.id == _reaction.id
    assert cobra_reaction.id == reaction.name
    assert cobra_reaction.name == reaction['name']

    cobra_stoichiometry = {m.id: coefficient for m, coefficient in six.iteritems(cobra_reaction.metabolites)}
    _stoichiometry = {m.id: coefficient for m, coefficient in six.iteritems(_reaction.metabolites)}

    def symmetric_difference(a, b):
        return dict((k, a[k] if k in a else b[k]) for k in set(a.keys()) ^ set(b.keys()))

    assert len(symmetric_difference(cobra_stoichiometry, _stoichiometry)) == 0


def test_fail_get_reaction():
    with pytest.raises(requests.HTTPError):
        client.get_reaction("non-existent")

    with pytest.raises(ValueError):
        client.get_reaction(1)


def test_get_gene(gene):
    cobra_gene = client.get_model_gene(gene.bigg_model_id, gene.name)
    if isinstance(gene['name'], float):  # nan
        assert cobra_gene.name is None
    else:
        assert cobra_gene.name == gene['name']
    assert cobra_gene.id == gene.name


def test_fail_get_gene(bigg_model_id):
    with pytest.raises(requests.HTTPError):
        client.get_model_gene(bigg_model_id, "non-existent")

    with pytest.raises(ValueError):
        client.get_model_gene(bigg_model_id, 1)


def test_list_reactions():
    reactions = client.list_reactions()
    for reaction in reactions[:10]:
        assert isinstance(reaction, Reaction)
        assert len(reaction.metabolites) == 0
        full_reaction = client.get_reaction(reaction)
        assert len(full_reaction.metabolites) > 0


def test_list_metabolites():
    metabolites = client.list_metabolites()
    for metabolite in metabolites[:10]:
        assert isinstance(metabolite, Metabolite)
        assert isinstance(metabolite.id, six.string_types)
        full_metabolite, species = client.get_metabolite(metabolite)
        assert isinstance(full_metabolite, Metabolite)
        assert full_metabolite.id == metabolite.id


def test_list_model_genes(bigg_model_id):
    genes = client.list_model_genes(bigg_model_id)
    for gene in genes[:10]:
        assert isinstance(gene, Gene)
        assert isinstance(gene.id, six.string_types)
        if gene.name is not None:
            assert isinstance(gene.name, six.string_types)

        full_gene = client.get_model_gene(bigg_model_id, gene)
        assert full_gene.id == gene.id
        assert full_gene.name == gene.name
