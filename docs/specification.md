# Volume Companion CLI Tool Requirements

## 1. Execution Environment
1.1 The tool shall run in Termux on Android and Bash on Linux without modification.  
1.2 The tool shall operate fully offline, using only locally stored CSV data.

## 2. Performance
2.1 The tool shall load the CSV file once at startup, store it fully in memory, and respond to user queries within 0.5 seconds.

## 3. Data Input and Parsing
3.1 The tool shall accept a CSV file containing OHLCV data using the fixed format: *YYYY.MM.DD,HH:MM,open,high,low,close,volume*.  
3.2 The tool shall parse timestamps exclusively in this CSV format.  
3.3 User-entered datetimes shall use the fixed ISO-8601-like format: *YYYY-MM-DDTHH:MM*.  
3.4 If the user inputs an invalid datetime, the tool shall fail gracefully with a concise error message.  
3.5 If the user inputs a datetime not present in the CSV, the tool shall select the latest bar strictly earlier than the entered timestamp.

## 4. Time Zone Handling
4.1 The tool shall allow setting a numerical time zone offset via the *offset <int>* command.  
4.2 The offset shall be applied only to user-entered datetimes.  
4.3 After applying the offset, the tool shall match the resulting datetime to the CSV (per rule 3.5).

## 5. Backtesting Constraints
5.1 When a datetime is provided (after timezone adjustment), the tool shall display volume data only up to and including the selected bar.  
5.2 The tool shall never display data newer than the selected bar.

## 6. Volume Display (ASCII Art Representation)
6.1 The tool shall display the most recent N bars’ volumes as ASCII-art bars, one per price bar, left-to-right, with a space delimiter.  
6.2 Each bar shall be drawn using Unicode block characters *▁▂▃▄▅▆▇█* (u2581–u2588), aligned vertically across 5 terminal rows, achieving 40 levels of granularity.
6.3 Bar heights shall be scaled relative to the maximum volume among the currently displayed N bars (local scaling) and mapped to an integer range [1, 40] for any volume greater than zero, ensuring all non-zero volumes produce a visible bar.  
6.4 Unused vertical bar height shall be rendered as whitespace, preserving vertical alignment across all displayed bars.  
6.5 Colour coding shall reflect price direction:  
- Green = close ≥ open  
- Red = close < open  

6.6 Display shall remain minimal and readable, with consistent spacing between bars.  
6.7 Stepping or datetime selection shall update the ASCII volume display immediately.  

## 7. Verbose Output (Numeric OHLC + Volume)
7.1 Verbose mode shall be toggled exclusively via the *verbose* command.  
7.2 When enabled, each displayed bar shall print full OHLC values and precise numeric volume as textual output.  
7.3 Example format: *2025-12-19 13:00 | O:1.1390 H:1.1400 L:1.1385 C:1.1395 | Vol:12345 | ↑*.  
7.4 Verbose output shall not affect ASCII volume display, scaling, or navigation.  
7.5 Verbose mode shall be part of session state and visible via the *config* command.

## 8. Navigation and Interaction
8.1 After loading the CSV, the tool shall provide a prompt-based interactive interface.  
8.2 At the prompt, the user shall be able to issue the following commands:  
- *datetime YYYY-MM-DDTHH:MM* to select a datetime  
- *bars <int>* to set the number of displayed bars  
- *offset <int>* to set the time zone offset  
- *step* to advance to the next bar  
- *verbose* to toggle verbose output  
- *config* to display current session configuration  

8.3 The tool shall maintain session state including current datetime, number of bars, time zone offset, and verbose mode.  
8.4 The *config* command shall print the active session configuration in a concise, readable format.

## 9. Error Handling
9.1 The tool shall handle invalid input gracefully with concise, clear error messages.  
9.2 The tool shall not exit unexpectedly due to malformed commands or missing timestamp matches.  
9.3 If a timestamp falls before the start of the CSV data, the tool shall request a valid input.
