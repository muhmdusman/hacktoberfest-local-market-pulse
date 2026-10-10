"""Tests for app/db/base.py"""

from sqlalchemy.orm import DeclarativeBase

from app.db.base import NAMING_CONVENTION, Base


def test_base_is_sqlalchemy_declarative_base():
    assert issubclass(Base, DeclarativeBase)


def test_base_metadata_uses_naming_convention():
    for key, template in NAMING_CONVENTION.items():
        assert Base.metadata.naming_convention[key] == template


def test_models_registry_exposes_same_base():
    from app.db.models import Base as RegistryBase

    assert RegistryBase is Base
