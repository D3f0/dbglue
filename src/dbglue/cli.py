import os
from dataclasses import dataclass
from typing import Any, List, Optional

import click
from loguru import logger
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.exc import (
    NoSuchModuleError,
    OperationalError,
    IntegrityError,
    InternalError,
)
from sqlalchemy import Table
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
    except ValueError as err:
        raise click.BadParameter(f"{err}")
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
    "-t",
    "--table",
    "tables",
    multiple=True,
    help="Table to copy",
    # if --all is on, this isn't needed
    # required=True
)
@click.option(
    "-w",
    "--warn-only",
    "warn",
    is_flag=True,
    default=False,
    help="Errors are non fatal",
)
@click.option("-a", "--all-tables", is_flag=True, default=False, help="Sync all tables")
@click.option("-b", "--batch-size", type=int, default=1000, help="Batch size")
@click.option(
    "-u", "--update", is_flag=True, default=True, help="Update (based on the table PK)"
)
@pass_config
def copy(
    config: AppConfig,
    source_engine: Optional[Engine],
    dest_engine: Optional[Engine],
    tables: List[str],
    warn: bool,
    all_tables: bool,
    batch_size: int,
    update: bool,
):
    source_engine = source_engine or config.global_source_engine
    if not source_engine:
        msg = "No database source detected for copy operation"
        if warn:
            logger.info(msg)
            return
        else:
            logger.warning(msg)
            raise click.Abort()
    dest_engine = dest_engine or config.global_dest_engine
    if not dest_engine:
        msg = "No database destination detected for copy operation"
        if warn:
            logger.info(msg)
            return
        else:
            logger.warning(msg)
            raise click.Abort()

    logger.debug(f"Will be copying the table(s): {','.join(tables)}")
    logger.info("Reading structure of source DB")
    source_session, source_metadata = get_db_engine_session_metadata(
        engine=source_engine
    )
    logger.info("Reading structure of destination DB")
    dest_session, dest_metadata = get_db_engine_session_metadata(engine=dest_engine)
    if all_tables:
        tables = list(source_metadata.tables.keys())
    for table in tables:
        # Get the tables from both metadatas
        TableSource: Optional[Table] = source_metadata.tables.get(table)
        if TableSource is None:
            if not warn:
                raise click.BadParameter("Table {table} not found in source")
            continue
        TableDest: Optional[Table] = dest_metadata.tables.get(table)
        if TableDest is None:
            # Should we create it?
            if not warn:
                raise click.BadParameter("Table {table} not found in destination")
            continue
        # Get the columns that match both places
        common_column_names = set(TableSource.columns.keys()) & set(
            TableDest.columns.keys()
        )
        columns = [TableSource.columns[name] for name in common_column_names]
        query_source = select(*columns)
        insert_dest = TableDest.insert()
        if not source_session.query(TableSource).count():
            logger.info(f"Skipping {table} with 0 records")
            continue
        total = 0
        errors: List[Exception] = []
        logger.info(f"Staring to copy {table}")
        while not errors:
            rows = source_session.execute(statement=query_source).fetchmany(batch_size)
            mapped_recs = [row._asdict() for row in rows]
            batch_length = len(mapped_recs)

            if batch_length:
                try:
                    dest_session.execute(insert_dest, mapped_recs)
                    dest_session.commit()
                    # Only count if insertion succeeded
                    total += batch_length
                except (InternalError, IntegrityError) as err:
                    if warn:
                        logger.info("Integrity errors while inserting in destination")
                        dest_session.rollback()
                        errors.append(err)
                        continue
                    else:
                        logger.warning(
                            "Integrity errors while inserting in destination"
                        )
                        raise click.Abort()

                logger.debug(f"Inserted {batch_length}")
            if batch_length < batch_size:
                break
        logger.info(f"Finished processing {table}: {total} ({errors})")


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
    for table_name, Table_ in metadata.tables.items():
        more_info = ""
        if count_rows or with_rows:
            count = session.query(Table_).count()
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
