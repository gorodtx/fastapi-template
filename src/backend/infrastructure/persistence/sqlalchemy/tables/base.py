from typing import Final

from sqlalchemy import MetaData
from sqlalchemy.orm import registry

NAMING_CONVENTION: Final[dict[str, str]] = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": (
        "fk_%(table_name)s_%(column_0_name)s__%(referred_table_name)s_%(referred_column_0_name)s"
    ),
    "pk": "pk_%(table_name)s",
}

metadata: MetaData = MetaData(naming_convention=NAMING_CONVENTION)

mapper_registry: registry = registry(metadata=metadata)
