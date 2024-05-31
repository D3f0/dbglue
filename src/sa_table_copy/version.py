from pkg_resources import DistributionNotFound, get_distribution
from sa_table_copy import __about__


def get_version_package() -> str:
    try:
        distribution = get_distribution("sa_table_copy")  # Replace with the module name
        return distribution.version
    except DistributionNotFound:
        return "Not installed with pip/pipx."


def get_version_code() -> str:
    return __about__.__version__
