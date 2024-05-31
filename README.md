# sa-table-copy

Copy tables with SQLAlchemy when:

- Database schemas differ between source and destination (only for additive changes on source)
- Use database URLs

[![PyPI - Version](https://img.shields.io/pypi/v/sa-table-copy.svg)](https://pypi.org/project/sa-table-copy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sa-table-copy.svg)](https://pypi.org/project/sa-table-copy)

-----

## Table of Contents

- [sa-table-copy](#sa-table-copy)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Installation as a clone (using `pipx`)](#installation-as-a-clone-using-pipx)
  - [License](#license)
  - [Development](#development)
    - [VS Code](#vs-code)

## Installation

```console
pip install sa-table-copy
```

### Installation as a clone (using `pipx`)

```bash
# clone the repo
git clone ... sa-table-copy
pipx install -e sa-table-copy
```


## License

`sa-table-copy` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


## Development


### VS Code

To enable code completion in VSCode, it's recommended to use the dev environment. To
get the interpreter path run:

```bash
hatch run which python
```

Copy the results and use the option Select Interpreter in VSCode.
