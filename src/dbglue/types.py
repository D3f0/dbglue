from typing import Annotated
from pydantic import AnyUrl, UrlConstraints


SAPostgresDSN = Annotated[
    AnyUrl,
    UrlConstraints(
        allowed_schemes=[
            "postgres",
            "postgresql",
            "postgresql+psycopg2",
            "postgresql+psycopg3",
            "postgresql+psycopg",
            "postgresql+asyncpsycopg",
        ]
    ),
]
