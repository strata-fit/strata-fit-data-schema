"""Datavalgen factory entrypoints for STRATA-FIT schema models."""

from datavalgen.factory import BaseDataModelFactory

from config.config import settings
from strata_fit_v6_data_validator_py.datavalgen_plugin import _get_model


class PatientDataFactory(BaseDataModelFactory):
    __model__ = _get_model("PatientData")
    __allow_none_optionals__ = False


class DefaultModelFactory(BaseDataModelFactory):
    __model__ = _get_model(settings.app.data.model_name)
    __allow_none_optionals__ = False
