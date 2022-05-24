''' Gets XML file, returns ProductBase object that contains list of Item objects, 
    each holding info from one of <item> tags in XML. '''

import xml.etree.ElementTree as et
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    info: str
    url: str
    img_url: str
    prices: dict


class ProductBase:
    def __init__(self, xml):
        self._xml = xml   # filename
        self._items = []  # list of Item objects
        self.parse_xml()  # new ProductBase should be provided with valid XML to get data from
                          # multiple ProductBases can be created from multiple XMLs

    @property
    def items(self): return self._items
    
    @property
    def xml(self): return self._xml


    def parse_xml(self):
        self.data = et.parse(self.xml)
        self.xmlroot = self.data.getroot()
        item_names = [item.name for item in self.items]

        for entry in self.xmlroot.findall('item'):
            name = entry.attrib['name'].strip()
            
            if name in item_names:  # item already added to base
                latest_price = entry.findall('price')[-1]
                for item in self.items:
                    if item.name == name:  # add only new price
                        item.prices[f'{latest_price.attrib["date"]}'] = latest_price.text

            else:  # item not in base, get all data and create Item object
                url = entry.find('url').text.strip()

                # totally new item doesn't have any info, so check it
                info_element = entry.find('info')
                img_url_element = entry.find('image')

                info = info_element.text.strip() if info_element != None else ''
                img_url = img_url_element.text.strip() if img_url_element != None else ''

                prices = dict()
                for subentry in entry.findall('price'):
                    prices[f'{subentry.attrib["date"]}'] = subentry.text
    
                self._items.append(Item(name, info, url, img_url, prices))


    def delete_item(self, item_name):
        for entry in self.items:
            if item_name == entry.name:
                self.items.remove(entry)


    def delete_price(self, item_name, date_to_delete):
        ''' Search price by date and delete it. '''
        
        for entry in self.items:
            if item_name == entry.name:
                for date in entry.prices.keys():
                    if date == date_to_delete:
                        entry.prices.pop(date)
                        return
                    
                
    def apply_changes_to_xml(self):
        ''' Compare ProductBase to XML and delete all price tags which are in XML but were deleted from base. 
            Called on base update, on program exit or manually by button. '''
        for item in self.items:
            xml_tag = self.xmlroot.find(f'item[@name="{item.name}"]')
            for element in xml_tag.findall('price'):
                if element.attrib['date'] not in list(item.prices):
                    xml_tag.remove(element)

        self.data.write(self.xml)

            

if __name__ == '__main__':
    pbase = ProductBase('new_pc.xml')
    pbase.parse_xml()
    for item in pbase.items:
        print(item)
    print()
    pbase.delete_price(pbase.items[0].name, '2021.09.16 19:32')
    for item in pbase.items:
        print(item)
    
