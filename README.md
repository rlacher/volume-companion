# Volume Companion

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

- `YYYY-MM-DDTHH:MM`: enter a datetime to display volume bars (ISO format)
- `bars <int>`: set the number of displayed bars
- `offset <int>`: set the time zone offset
- `step`: advance to the next bar
- `verbose`: toggle verbose output
- `config`: show current session configuration (bars, offset, verbose mode)

## License

This project is licensed under the [MIT License](LICENSE).

## Author

Developed by [René Lacher](https://github.com/rlacher).

