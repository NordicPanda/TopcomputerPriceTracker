import codecs
import datetime as dt
import os
import ssl
import time
import urllib.request as ur
import xml.etree.ElementTree as et


def open_url(url):
    ''' Loads webpage at provided URL address. '''

    # ignore ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE    
    
    req = ur.Request(url, headers={'User-Agent': 'Magic Browser'})
    result = ur.urlopen(req, context=ctx).read()
    html_file = codecs.decode(result, encoding='utf-8', errors='ignore')
    return html_file
    

def get_item_name(html_file):
    ''' Searches and returns item's name from HTML code. 
        Used also by LinkEditor so moved to separate function. '''

    name_string = 'class="product-title" itemprop="name">'
    name_start = html_file.find(name_string) + len(name_string)
    name_end = name_start + html_file[name_start:name_start + 100].find('</h1>')
    name = html_file[name_start:name_end].strip()
    return name


def get_item_data(html_file):
    ''' Searches through HTML code for name and price of the item. '''

    # Get requested info from provided HTML code, returns tuple with data
    name = get_item_name(html_file)

    info_string = '<title>'
    info_end_string = '</title>'
    info_start = html_file.find(info_string) + len(info_string)
    info_end = html_file.find(info_end_string)
    info = html_file[info_start:info_end]

    price_string = 'itemprop="price" content="'
    price_start = html_file.find(price_string) + len(price_string)
    price_end = price_start + html_file[price_start:price_start + 7].find('"')
    price = html_file[price_start:price_end] if price_start != 25 else 'NOT IN STOCK'

    # image may be either jpg or png, so search from right to left
    image_link_pos = html_file.find('class="fbox-product-image')
    html_part = html_file[image_link_pos - 200:image_link_pos]  # part of html containing image link
    image_link_start = html_part.rfind('upload')
    image_link_end = html_part.rfind('"')
    image_link = 'https://topcomputer.ru/' + html_part[image_link_start:image_link_end]

    return name, price, image_link, info


def parse_url(root, url, counter, urls_len):
    ''' Get one URL and write required data from it into XML. '''

    item_name, price, image_link, info = get_item_data(open_url(url))
    date = dt.datetime.now().strftime('%Y.%m.%d %H:%M')  # date format as 2021.08.24 12:00
    print(f'Parsed URL #{counter+1} of {urls_len}: {item_name}')

    item_tag = root.find(f'item[@name="{item_name}"]')  # if found, returns Element
    if item_tag == None:  # no such item, create it
                          # (item should exist because linkedit.py already created it)
        new_cpu = et.SubElement(root, 'item', name=item_name)
        et.SubElement(new_cpu, 'url').text = url
        et.SubElement(new_cpu, 'info').text = info
        et.SubElement(new_cpu, 'image').text = image_link
        et.SubElement(new_cpu, 'price', date=date).text = str(price)
    else:  # item already exists
        if item_tag.find('url') == None:  # no url (should exist because linkedit.py)
            et.SubElement(item_tag, 'url').text = url
        if item_tag.find('info') == None:  # no info
            et.SubElement(item_tag, 'info').text = info
        if item_tag.find('image') == None:  # no image
            et.SubElement(item_tag, 'image').text = image_link
        et.SubElement(item_tag, 'price', date=date).text = str(price)


def parse(xml_filename: str):
    ''' Get urls from xml file (<item><url> ... </url></item>) and run parser for each of them. '''

    if not os.path.isfile(xml_filename):      # if output file does not exist (should exist!), create it
        out_file = open(xml_filename, 'w')    # and make it a valid empty XML
        out_file.write('<root></root>')       # file is created by linkedit, so this is just in case something's wrong
        out_file.close()

    data = et.parse(xml_filename)             # open XML file as ElementTree
    root = data.getroot()                     # get root tag as Element
    
    # get urls
    urls = [element.text for element in root.findall('item/url')]

    urls_len = len(urls)   # to show how many URLs were parsed
    for counter in range(urls_len):
        parse_url(root, urls[counter], counter, urls_len)

    print('Done')
    time.sleep(0.5)

    data.write(xml_filename, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':  # test
    parse('new_pc - копия.xml')
