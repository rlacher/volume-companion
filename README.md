# Volume Companion

<!-- Badges -->
[![flake8](https://img.shields.io/github/actions/workflow/status/rlacher/volume-companion/flake8.yaml?label=flake8&style=flat)](https://github.com/rlacher/volume-companion/actions/workflows/flake8.yaml)
[![mypy](https://img.shields.io/github/actions/workflow/status/rlacher/volume-companion/mypy.yaml?label=mypy&style=flat)](https://github.com/rlacher/volume-companion/actions/workflows/mypy.yaml)
[![pytest](https://img.shields.io/github/actions/workflow/status/rlacher/volume-companion/pytest.yaml?label=pytest&style=flat)](https://github.com/rlacher/volume-companion/actions/workflows/pytest.yaml)
[![license](https://img.shields.io/badge/license-MIT-lightgrey.svg)](https://spdx.org/licenses/MIT.html)

Command-line tool displaying historical trading volume as ASCII bars from local CSV data.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [License](#license)
- [Author](#author)

## Features

- Offline processing of OHLCV CSV data.
- Fast in-memory queries with immediate response.
- ASCII-art volume bars with colour coding.
- Optional verbose output showing numeric OHLC and volume.
- Prompt-based interface with session state.
- Handles invalid input gracefully without exiting.
<!-- - Supports higher-timeframe aggregation with incomplete bar marking. -->

## Installation

Clone the repository, then install dependencies with:

```bash
poetry install
```

## Usage

Run the project using:

```bash
poetry run volume-companion path/to/data.csv
```

After startup, the tool enters an interactive prompt.
Type `help` to list available commands.

## Commands

Within the prompt you can configure the session, navigate through data, and display volume at specific points in time.

- `datetime [<YYYY-MM-DDTHH:MM>]`: Display volume bar window for previously selected datetime or jump to provided datetime (ISO format)
- `bars <number>`: Set the number of displayed bars
- `offset <hours>`: Set the time zone offset
- `step [<number>]`: Advance one or multiple bars (number optional, defaults to 1)
- `verbose`: Toggle verbose output
- `config`: Show current session configuration (bars, offset, verbose mode)

## Testing

Run the test suite locally with (requires `poetry install --with dev`):

```bash
poetry run pytest --cov=src/ tests/
```

## License

This project is licensed under the [MIT License](LICENSE).

## Author

Developed by [René Lacher](https://github.com/rlacher).

