import os
import json
import frontmatter
import pandas as pd

# Initialize an empty list to store the rows of our Excel file
rows = []

# Ask the user for the language
lang = input("Please enter the language for pattern file [en/fr]: ")

# Validate the input
if lang not in ['en', 'fr']:
    print("Invalid language. Exiting.")
    exit()

# Dynamically read the appropriate pattern JSON file based on the user's input
with open(f'path/to/pattern-01-{lang}.json', 'r') as f:
    pattern = json.load(f)

# Ask the user for the path to the Jekyll site directory
user_input = input("Please enter the path to the Jekyll site directory (leave empty to use the current directory): ")

# Use the user input as the path, or default to the current directory if no input is provided
path = user_input if user_input else os.getcwd()

# Traverse the Jekyll site directory
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith('.md'):
            # Get the full path of the file
            full_path = os.path.join(root, file)

            # Get the date the file was last modified
            last_modified_date = os.path.getmtime(full_path)

            # Parse the front matter
            with open(full_path, 'r', encoding='utf-8') as f:
                metadata, content = frontmatter.parse(f.read())

            # Check if the page is listed in the appropriate pattern JSON
            is_listed = full_path in pattern

            # Extract meta description, title, and section title
            meta_description = metadata.get('description', '')
            title = metadata.get('title', '')
            section_title = metadata.get('section_title', '')

            # Extract the date the page was issued
            issued_date = metadata.get('date', '')

            # Check if the content contains HTML code
            has_html = '<' in content and '>' in content

            # Check if the content contains links to GCWeb/WET
            has_gcweb_links = 'gcweb' in content.lower() or 'wet' in content.lower()

            # Check if the content contains images
            has_images = '![' in content

            # Append this information to our rows list
            rows.append([
                is_listed,
                last_modified_date,
                meta_description,
                title,
                section_title,
                issued_date,
                has_html,
                has_gcweb_links,
                has_images,
                full_path
            ])

# Create a Pandas DataFrame from our rows
df = pd.DataFrame(rows, columns=[
    'Is Listed',
    'Last Modified Date',
    'Meta Description',
    'Title',
    'Section Title',
    'Issued Date',
    'Has HTML',
    'Has GCWeb/WET Links',
    'Has Images',
    'File Path'
])

# Export the DataFrame to an Excel file
df.to_excel('jekyll_site_metadata.xlsx', index=False, engine='openpyxl')
