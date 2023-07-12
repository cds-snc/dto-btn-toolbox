# Script Requirement Specification

## 1. Introduction

This script is required to convert HTML files to Markdown format. The script should traverse through all directories and subdirectories to find HTML files and process each one individually.

## 2. Functional Requirements

### 2.1 HTML File Processing

The script should process each HTML file as follows:

1. Extract the following information from the HTML:
   - Alternate language page link
   - Breadcrumb navigation links
   - Date the page was last modified
   - Meta description of the page
   - Title and section title of the page
   - Main content of the page
   - Date the page was issued
   - Presence of a share sheet (div with classes `col-sm-3`, `col-sm-offset-1`, `col-lg-offset-3` and a child div with class `wb-share`)

2. If any of the above information is missing, log the missing information in a log file.

3. If a share sheet is present, remove it from the page and log an error message "this page has a share sheet".

4. Convert the extracted information into YAML format and prepend it to the main content to create the Markdown file.

5. Rename the original HTML file by prepending an underscore. If there were missing information or a share sheet was present, prepend two underscores instead.

6. Save the Markdown file with the same name and location as the original HTML file, but with a '.md' extension instead of '.html'.

### 2.2 YAML Front Matter

The YAML front matter should include the following properties:

- `altLangPage`: The alternate language page link
- `breadcrumbs`: The breadcrumb navigation links
- `date`: The date the page was issued
- `dateModified`: The date the page was last modified
- `description`: The meta description of the page
- `title`: The title of the page
- `section-title`: The section title of the page (if present)
- `share`: A boolean indicating the presence of a share sheet (if present)

The properties should be listed in alphabetical order.

## 3. Non-Functional Requirements

### 3.1 Performance

The script should be able to process a large number of HTML files in a reasonable amount of time.

### 3.2 Error Handling

The script should handle errors gracefully, logging any issues encountered during the processing of an HTML file and continuing with the next file.

### 3.3 Compatibility

The script should be compatible with Python 3.6 and above.

## 4. System Features

### 4.1 HTML to Markdown Conversion

The script should convert HTML files to Markdown format, extracting relevant information and handling special cases as described in the functional requirements.

### 4.2 Error Logging

The script should log any issues encountered during the processing of an HTML file, including missing information and the presence of a share sheet.

## 5. External Interface Requirements

### 5.1 User Interfaces

The script should be a command-line application with no graphical user interface.

### 5.2 Script Interfaces

The script should use the BeautifulSoup library for parsing HTML, the PyYAML library for generating YAML, and the Python standard library for file and directory operations.

### 5.3 Communication Interfaces

The script does not require any network communication.

## 6. Other Nonfunctional Requirements

### 6.1 Security

The script does not handle any sensitive data and does not require any specific security measures.

### 6.2 Reliability

The script should be able to process a large number of HTML files without crashing or hanging.

### 6.3 Maintainability

The script should be written in a clear and modular manner to facilitate future modifications and enhancements.
