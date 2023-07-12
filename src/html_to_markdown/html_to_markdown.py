import os
from bs4 import BeautifulSoup, Comment, Tag
import re
import yaml
from datetime import datetime
from dateutil.parser import parse

def extract_altLangPage(soup, altLang):
    altLangPage = None
    altLangPage_element = soup.find('a', {'lang': altLang})
    if altLangPage_element:
        altLangPage = altLangPage_element.get('href')
    if not altLangPage:
        script_tag = soup.find('script', string=re.compile('href:'))
        if script_tag:
            match = re.search(r'href: "(.*?)"', script_tag.string)
            if match:
                altLangPage = match.group(1)
    return altLangPage

def extract_breadcrumbs(soup):
    breadcrumbs = []
    breadcrumb_items = soup.select('nav#wb-bc ol.breadcrumb li a')
    if breadcrumb_items:
        for item in breadcrumb_items[1:]:
            breadcrumbs.append({
                'title': item.text,
                'link': item.get('href', '')
            })
    else:
        script_tag = soup.find('script', string=re.compile('breadcrumbs:'))
        if script_tag:
            matches = re.findall(r'{\s*title:\s*"([^"]*)",\s*href:\s*"([^"]*)"\s*}', script_tag.string)
            for match in matches[1:]:
                breadcrumbs.append({
                    'title': match[0],
                    'link': match[1]
                })
    return breadcrumbs

def extract_dateModified(soup):
    dateModified = None
    log_message = None
    dateModified_element = soup.find('time', {'property': 'dateModified'})
    if dateModified_element:
        try:
            date = datetime.strptime(dateModified_element.text, "%Y-%m-%d")
            dateModified = date.strftime("%Y-%m-%d")
        except ValueError:
            try:
                date = parse(dateModified_element.text)
                dateModified = date.strftime("%Y-%m-%d")
            except ValueError:
                log_message = f'- dateModified value "{dateModified_element.text}" could not be parsed.\n'
    if not dateModified:
        script_tag = soup.find('script', string=re.compile('dateModified:'))
        if script_tag:
            match = re.search(r'dateModified: "(.*?)"', script_tag.string)
            if match:
                try:
                    date = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S")
                    dateModified = date.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        date = parse(match.group(1))
                        dateModified = date.strftime("%Y-%m-%d")
                    except ValueError:
                        log_message = f'- dateModified value "{match.group(1)}" could not be parsed.\n'
    return dateModified, log_message

def extract_description(soup):
    description = None
    description_element = soup.find('meta', {'name': 'description'})
    if description_element:
        description = description_element.get('content')
    return description

def delete_discussion(soup):
    discussion = None
    discussion_element = soup.find('a', {'href': 'https://github.com/canada-ca/design-system-systeme-conception/issues'})
    if discussion_element:
        if discussion_element.parent.name == 'li':
            discussion = discussion_element.find_parent('li')
        else:
            if discussion_element.parent.name == 'p' and discussion_element.parent.sibling == 'h2':
                discussion = discussion_element.find_parent('section')
    return discussion

def extract_title_and_section_title(soup):
    title = None
    section_title = None
    title_element = soup.find('h1')
    if title_element:
        stacked_span = title_element.find('span', {'class': 'stacked'})
        if stacked_span:
            spans = stacked_span.find_all('span')
            if spans:
                title = spans[0].text
                if len(spans) > 1:
                    section_title = spans[1].text
        else:
            title = title_element.text.replace(' - Canada.ca', '')
    return title, section_title

def extract_main_content(soup):
    main_content = ''
    main_element = soup.find('main')

    if main_element:
        h1_element = main_element.find('h1')
        if h1_element:
            h1_element.extract()

        feedback_start = soup.find(string=lambda text: isinstance(text, Comment) and 'START PAGE FEEDBACK WIDGET' in text)
        feedback_end = soup.find(string=lambda text: isinstance(text, Comment) and 'END PAGE FEEDBACK WIDGET' in text)
        if feedback_start and feedback_end:
            for sibling in feedback_start.find_all_next(string=lambda text: isinstance(text, Comment)):
                if sibling == feedback_end:
                    break
                if isinstance(sibling, Tag):
                    sibling.decompose()

        feedback_tool = main_element.find('section', {'class': 'gc-pg-hlpfl'})
        if feedback_tool:
            feedback = feedback_tool.find_parent('div', {'class': 'row-no-gutters'})
            if feedback:
                feedback.decompose()

        page_details = main_element.find('div', {'class': 'pagedetails'})
        if page_details:
            page_details.extract()

        discussion = delete_discussion(main_element)
        if discussion:
            discussion.decompose()

        for script in main_element("script"):
            script.decompose()
        for comment in main_element(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        for mwsgeneric in main_element.select('.mwsgeneric-base-html'):
            mwsgeneric.unwrap()
        main_content = ''.join(item.prettify() if isinstance(item, Tag) else str(item) for item in main_element.contents)
    return main_content

def extract_date(soup):
    date = None
    date_element = soup.find('meta', {'property': 'dc:issued.term'})
    if date_element:
        try:
            date = datetime.strptime(date_element.get('content'), "%Y-%m-%d")
            date = date.strftime("%Y-%m-%d")
        except ValueError:
            try:
                date = parse(date_element.get('content'))
                date = date.strftime("%Y-%m-%d")
            except ValueError:
                pass
    return date

def extract_share(soup):
    share = False
    log_message = None
    share_element = soup.select_one('div.col-sm-3.col-sm-offset-1.col-lg-offset-3>div.wb-share')
    if share_element:
        share = True
        share_element.decompose()
        log_message = '- this page has a share sheet.\n'
    return share, log_message

def process_html_file(html_file):
    with open(html_file, 'r') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    if soup.find('meta', {'http-equiv': re.compile(r'refresh', re.I)}):
        log_file_name = f'log_{datetime.now().strftime("%Y%m%d")}.md'
        with open(log_file_name, 'a') as log_file:
            log_file.write(f'**{html_file}**:\n- redirect file.\n\n')
        return

    lang = soup.html.get('lang')
    altLang = 'fr' if lang == 'en' else 'en'
    altLangPage = extract_altLangPage(soup, altLang)
    breadcrumbs = extract_breadcrumbs(soup)
    dateModified, dateModified_log = extract_dateModified(soup)
    description = extract_description(soup)
    title, section_title = extract_title_and_section_title(soup)
    main_content = extract_main_content(soup)
    date = extract_date(soup)
    share, share_log = extract_share(soup)
    front_matter = {
        'altLangPage': altLangPage,
        'breadcrumbs': breadcrumbs,
        'date': date,
        'dateModified': dateModified,
        'description': description,
        'title': title
    }
    if section_title:
        front_matter['section-title'] = section_title

    if share:
        front_matter['share'] = share
    log_message = ''
    for key, value in front_matter.items():
        if not value:
            log_message += f'- {key} is empty.\n'
    log_message += dateModified_log if dateModified_log else ''
    log_message += share_log if share_log else ''
    if log_message:
        log_file_name = f'log_{datetime.now().strftime("%Y%m%d")}.md'
        with open(log_file_name, 'a') as log_file:
            log_file.write(f'**{html_file}**:\n{log_message}\n')
    front_matter_yaml = yaml.dump(front_matter, default_flow_style=False, sort_keys=True)
    markdown = '---\n' + front_matter_yaml + '---\n' + main_content
    md_file = os.path.splitext(html_file)[0] + '.md'
    with open(md_file, 'w') as f:
        f.write(markdown)
    directory, filename = os.path.split(html_file)
    new_filename = '_' + filename if log_message else '__' + filename
    new_path = os.path.join(directory, new_filename)
    os.rename(html_file, new_path)

html_files = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if not d[0] == '_']
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

for html_file in html_files:
    process_html_file(html_file)
