# dbglue

Copy tables with SQLAlchemy when:

- Database schemas differ between source and destination (only for additive changes on source)
- Use database URLs

[![PyPI - Version](https://img.shields.io/pypi/v/dbglue.svg)](https://pypi.org/project/dbglue)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dbglue.svg)](https://pypi.org/project/dbglue)

-----

## Table of Contents

- [dbglue](#dbglue)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Installation as a clone (using `pipx`)](#installation-as-a-clone-using-pipx)
  - [License](#license)
  - [Development](#development)
    - [VS Code](#vs-code)

## Installation

```console
pip install dbglue
```

### Installation as a clone (using `pipx`)

```bash
# clone the repo
git clone ... dbglue
pipx install -e dbglue
```


## License

`dbglue` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


## Development


### VS Code

To enable code completion in VSCode, it's recommended to use the dev environment. To
get the interpreter path run:

```bash
hatch run which python
```

Copy the results and use the option Select Interpreter in VSCode.
