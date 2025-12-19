# Volume Companion

Command-line tool displaying historical trading volume as ASCII bars from local CSV data.

## Table of Contents

- [Features](#features)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Configuration](#configuration)  
- [Commands](#commands)  
- [Error Handling](#error-handling)  
- [License](#license)  
- [Author](#author)  

## Features

- Offline processing of OHLCV CSV data.  
- Fast in-memory queries with immediate response.  
- ASCII-art volume bars with colour coding.
- Optional verbose output showing numeric OHLC and volume.  
- Supports higher-timeframe aggregation with incomplete bar marking.  
- Prompt-based interface with session state.  

## Installation

Clone the repository and install dependencies with:  
```bash
poetry install
```

Run the project using:  
```bash
poetry run volume_companion.py
```

## Usage

Load a CSV and use the prompt to set timeframe or display options, or enter a datetime to print volume bars.

## Configuration

Set and view session settings: number of bars, timeframe, time zone, verbose mode.  
Use `config` to display current settings.

## Commands

- `YYYY-MM-DDTHH:MM`: enter a datetime in ISO format to display volume bars
- `step`: advance to the next bar  
- `verbose`: toggle verbose mode  

## Error Handling

Invalid input or unmatched timestamps produce concise error messages without crashing.

## License

This project is licensed under the [MIT License](LICENSE).

## Author

Developed by [René Lacher](https://github.com/rlacher).

