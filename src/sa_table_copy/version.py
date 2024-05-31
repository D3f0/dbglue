from pkg_resources import DistributionNotFound, get_distribution
from dbglue import __about__


def get_version_package() -> str:
    try:
        distribution = get_distribution("dbglue")  # Replace with the module name
        return distribution.version
    except DistributionNotFound:
        return "Not installed with pip/pipx."


def get_version_code() -> str:
    return __about__.__version__
