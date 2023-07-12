# Shared Dependencies

This document outlines the shared dependencies required for the HTML to Markdown conversion script. These dependencies should be installed in the Python environment where the script will be run.

## Python Version

The script is compatible with Python 3.6 and above.

## Libraries

The script depends on the following Python libraries:

### BeautifulSoup

BeautifulSoup is used for parsing HTML and navigating the parse tree. It provides simple and consistent interfaces for finding and manipulating parsed data.

Installation: `pip install beautifulsoup4`

### PyYAML

PyYAML is used for generating YAML from Python data structures. It supports all YAML features and has a simple API.

Installation: `pip install pyyaml`

### python-dateutil

python-dateutil is used for parsing dates in various formats. It provides powerful extensions to the standard datetime module.

Installation: `pip install python-dateutil`

## Operating System

The script should be compatible with any operating system that supports Python, including Windows, macOS, and Linux.

## File System

The script requires read and write access to the directories containing the HTML files to be converted. It will traverse all subdirectories of the specified directory, convert all HTML files found, and save the resulting Markdown files in the same locations. It will also create a log file in the current working directory.

## Network

The script does not require network access to function. However, network access may be required to install the dependencies.

## Other Dependencies

No other dependencies are required.
