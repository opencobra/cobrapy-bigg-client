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

import pytest
import importlib_resources

from pandas import read_csv

from cobra.io import load_json_model


FIXTURES = "cobrapy_bigg_client.tests.fixtures"
MODELS_FIXTURES = "cobrapy_bigg_client.tests.fixtures.models"


@pytest.fixture(params=["iJO1366", "iMM904", "iAF987", "STM_v1_0"])
def bigg_model_id(request):
    return request.param


@pytest.fixture()
def bigg_model(bigg_model_id):
    with importlib_resources.open_text(MODELS_FIXTURES, "%s.json" % bigg_model_id) as handle:
        return load_json_model(handle)


with importlib_resources.open_text(FIXTURES, "metabolites.tsv") as handle:
    metabolites = read_csv(handle, sep="\t", index_col=0)
    metabolites['formulae'] = metabolites.formulae.apply(str.split, args=("; ", ))
    metabolites['charges'] = metabolites.charges.apply(
        lambda charges: charges.split("; ") if isinstance(charges, str) else [charges]).apply(
        lambda charges: [int(c) for c in charges])


@pytest.fixture(params=metabolites.index)
def metabolite(request):
    return metabolites.loc[request.param]


with importlib_resources.open_text(FIXTURES, "reactions.tsv") as handle:
    reactions = read_csv(handle, sep="\t", index_col=0)


@pytest.fixture(params=reactions.index)
def reaction(request):
    return reactions.loc[request.param]


with importlib_resources.open_text(FIXTURES, "genes.tsv") as handle:
    genes = read_csv(handle, sep="\t", index_col=0)


@pytest.fixture(params=genes.index)
def gene(request):
    return genes.loc[request.param]


@pytest.fixture(params=["xml", "xml.gz", "mat", "json"])
def model_format(request):
    return request.param

