from __future__ import division

import io
import optparse
import os

import requests

from bs4 import BeautifulSoup

parser = optparse.OptionParser()
parser.add_option('-f', '--format',
                  action="store", dest="format",
                  help="Format to output file [txt/html]", default="txt")
parser.add_option('-s', '--size',
                  action="store", dest="size",
                  help="Set the max size of the file in MB", default="2")

options, args = parser.parse_args()

substring_list_filter = ['comment', 'javascript', 'replytocom', '/support/', '/gallery/', '/f-a-q/',
                         '/cast-spoiler-free/']
must_contain_substring = ['https://parahumans.wordpress.com/']
url_filter = ['https://parahumans.wordpress.com/', 'https://parahumans.wordpress.com/table-of-contents/']


def filter_links(toc_links):
    filtered_links = []
    for link in toc_links:
        link_value = link.get('href')
        if any(substring in link_value for substring in substring_list_filter):
            continue
        elif any(substring not in link_value for substring in must_contain_substring):
            continue
        elif any(substring == link_value for substring in url_filter):
            continue
        else:
            filtered_links = filtered_links + [link_value]
    return filtered_links


def scrape_toc_for_links():
    toc_page = requests.get('https://parahumans.wordpress.com/table-of-contents/', timeout=5)
    toc_page_content = BeautifulSoup(toc_page.content, "html.parser")
    toc_links = filter_links(toc_page_content.find_all('a'))
    return toc_links


def create_full_chapter_content(chapter_pieces, format):
    if format == 'html':
        return ''.join(piece.prettify() for piece in chapter_pieces)
    else:
        return '\n'.join(piece.text for piece in chapter_pieces)


def scrape_and_save_chapter(file_name, chapter_link, format):
    with io.open(file_name, "a", encoding="utf-8") as worm_file:
        print('Opening ' + chapter_link)
        chapter_page = requests.get(chapter_link, timeout=5)
        chapter_soup = BeautifulSoup(chapter_page.content, "html.parser")
        chapter_pieces = []
        content_div = chapter_soup.find(id='content').article
        title = content_div.header.h1
        chapter_pieces.append(title)
        date = content_div.header.div
        chapter_pieces.append(date)
        chapter_text = content_div.select('.entry-content')[0]
        chapter_pieces.append(chapter_text)
        full_chapter_content = create_full_chapter_content(chapter_pieces, format)
        print('Writing to ' + file_name)
        worm_file.write(full_chapter_content)
        return os.path.getsize(file_name)


def main():
    max_file_mb = int(options.size)
    format = options.format
    chapter_links = scrape_toc_for_links()
    chunk = 0
    file_name = 'worm-part-' + str(chunk) + '.' + format

    if os.path.exists(file_name):
        os.remove(file_name)
    for i, chapter_link in enumerate(chapter_links):
        chapter_link = chapter_links[i]
        file_size = scrape_and_save_chapter(file_name, chapter_link, format)
        file_size_in_mb = file_size / 1000000
        # print('Current file size: ' + str(file_size_in_mb) + 'MB')
        if file_size_in_mb >= max_file_mb:
            print('File limit reached, chunking...')
            chunk += 1
            file_name = 'worm-part-' + str(chunk) + '.' + format
            if os.path.exists(file_name):
                os.remove(file_name)
        percent_complete = (i + 1) / len(chapter_links) * 100
        print(str(percent_complete) + '% complete')


main()
