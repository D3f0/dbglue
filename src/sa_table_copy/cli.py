import os
from dataclasses import dataclass
from typing import Any, List, Optional

import click
from loguru import logger
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import NoSuchModuleError, OperationalError

from .meta import get_db_engine_session_metadata
from .output import console
from .urls import ensure_schema
from .version import get_version_code, get_version_package


def validate_engine(
    ctx: click.Context, param: click.Parameter, value: Any
) -> Optional[Engine]:
    """
    Validates that the passed argument is a valid database connection.

    Args:
    ctx: Click context object.
    param: Click parameter object for the option.
    value: The value provided for the option.

    Raises:
    BadParameter: If the value is not a valid SQLAlchemy database engine.
    """
    if not value:
        if param.required:
            raise click.BadParameter("Name cannot be empty.")
        else:
            return None
    try:
        url_with_known_schema = ensure_schema(value)
        return create_engine(url=url_with_known_schema)
    except NoSuchModuleError as err:
        raise click.BadParameter(f"SQLAlchemy doesn't know how to talk to: {err}")
    except OperationalError as err:
        raise click.BadParameter(f"SQLAlchemy has issues with: {err}")

    except Exception as e:
        logger.exception(f"Error {e}: {value}")
        raise click.BadParameter(str(value))


@dataclass
class AppConfig:
    # Global configuration in case of multiple commands using the same
    global_source_engine: Optional[Engine]
    global_dest_engine: Optional[Engine]


pass_config = click.make_pass_decorator(AppConfig, ensure=True)


@click.group(chain=True)
@click.option(
    "-S",
    "--global-source",
    "source_engine",
    help="Global source database URL for the source postgres://user:pass@host:port/dbname"
    " Defaults to $SOURCE_DB if available",
    default=lambda: os.getenv("SOURCE_DB"),
    callback=validate_engine,
)
@click.option(
    "-D",
    "--global-destination",
    "dest_engine",
    help="Global destination database destination postgres://user:pass@host:port/dbname"
    "Defaults to $DEST_DB if available",
    default=lambda: os.getenv("DEST_DB"),
    callback=validate_engine,
)
@click.pass_context
def group(
    ctx: click.Context, source_engine: Optional[Engine], dest_engine: Optional[Engine]
):
    ctx.obj = AppConfig(
        global_source_engine=source_engine,
        global_dest_engine=dest_engine,
    )


@group.command()
@click.option(
    "-s",
    "--source",
    "source_engine",
    help="Database URL for the source postgres://user:pass@host:port/dbname",
    default=lambda: os.getenv("SOURCE_DB"),
    callback=validate_engine,
)
@click.option(
    "-d",
    "--destination",
    "dest_engine",
    help="Database URL for the destination postgres://user:pass@host:port/dbname",
    default=lambda: os.getenv("DEST_DB"),
    callback=validate_engine,
)
@click.option(
    "-t", "--table", "tables", multiple=True, help="Table to copy", required=True
)
@pass_config
def copy(
    config: AppConfig, source_engine: Engine, dest_engine: Engine, tables: List[str]
):
    logger.debug(f"Will be copying the table(s): {','.join(tables)}")
    logger.info("Reading structure of source DB")
    source_session, source_metadata = get_db_engine_session_metadata(
        engine=source_engine
    )
    logger.info("Reading structure of destination DB")
    dest_session, dest_metadata = get_db_engine_session_metadata(engine=dest_engine)


@group.command(name="list-tables")
@click.option(
    "-s",
    "--source",
    "source_engine",
    help="Database URL for the source postgres://user:pass@host:port/dbname",
    default=lambda: os.getenv("SOURCE_DB"),
    callback=validate_engine,
)
@click.option(
    "-C", "--count", "count_rows", is_flag=True, default=False, help="Count rows"
)
@click.option(
    "-r",
    "--with-rows",
    "with_rows",
    is_flag=True,
    default=False,
    help="Show only the tables that have 1 or more rows§",
)
@pass_config
def list_tables(
    config: AppConfig,
    source_engine: Optional[Engine],
    count_rows: bool,
    with_rows: bool,
) -> None:
    """Shows the tables defined in the database"""
    engine = source_engine or config.global_source_engine or None
    logger.debug(f"{engine=}")
    if engine is None:
        raise click.BadArgumentUsage("No connection string defined")
    session, metadata = get_db_engine_session_metadata(engine=engine)
    for table_name, Table in metadata.tables.items():
        more_info = ""
        if count_rows or with_rows:
            count = session.query(Table).count()
            if count_rows:
                more_info = f"({count})"
            if with_rows and not count:
                continue
        print(table_name, more_info)


@group.command()
def version():
    """Shows the package version"""
    console.print("Package installation version", get_version_package())
    console.print("Package code version (if editable)", get_version_code())


group()
