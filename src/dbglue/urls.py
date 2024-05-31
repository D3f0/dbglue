from loguru import logger

SCHEMA_TABLE = {"postgres": "postgresql"}


def ensure_schema(url_string: str) -> str:
    if "://" not in url_string:
        raise ValueError(f"Not a valid url {url_string}")
    schema, connection = url_string.split("://", maxsplit=1)
    new_schema = SCHEMA_TABLE.get(schema)
    if new_schema is not None:
        logger.debug(f"{schema} will be substituted to: {new_schema}")
        schema = new_schema

    return "://".join([schema, connection])
