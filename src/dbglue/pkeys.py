"""
Primary Key handling
"""

from typing import Any, Set

from loguru import logger
from sqlalchemy import Table
from sqlalchemy.orm import Session
import sqlalchemy.exc


def get_primary_key_values(*, table: Table, session: Session) -> Set[Any]:
    """Returns the list of primary keys values"""
    pk_cols = table.primary_key.columns
    if len(pk_cols) > 1:
        logger.warning(f"The table {table.name} has more than 1 primary key")
    try:
        result = session.query(
            pk_cols,
        ).all()
    except sqlalchemy.exc.InvalidRequestError:
        return set()
    return {v[0] for v in result}
