from typing import Tuple

from sqlalchemy import Engine, MetaData
from sqlalchemy.orm import Session
from loguru import logger


def get_db_engine_session_metadata(engine: Engine) -> Tuple[Session, MetaData]:
    """
    Convenience method to get engine, session and metadata of a table
    """
    logger.debug(f"Getting metadata from {engine=}")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    session = Session(bind=engine)
    logger.debug(f"Metadata: {metadata=}")
    return session, metadata
