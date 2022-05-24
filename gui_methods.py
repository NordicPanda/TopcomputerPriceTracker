import os.path
import ssl
import tkinter as tk
import tkinter.filedialog as fd
import urllib.request as ur
import webbrowser as wb

from io import BytesIO
from PIL import Image, ImageTk
from tkinter.ttk import Button, Label, Frame, Combobox, Treeview, Scrollbar, Style
from tkinter import messagebox as mbox

# import local modules
import tcxml
from product_base import ProductBase
from linkedit import LinkEditor

class GUIMethods:

    def _resize_image(parent, image, new_size):
        ''' Calculate new image size and return Image object. '''

        size_x, size_y = image.size
        if size_x >= size_y:
            k = size_x / new_size
            new_size_x = new_size
            new_size_y = int(size_y // k)
        else:
            k = size_y / new_size
            new_size_y = new_size
            new_size_x = int(size_x // k)

        resized = image.resize((new_size_x, new_size_y))

        # create white background for image to exactly fit square
        bg = Image.new('RGBA', (new_size, new_size), (255, 255, 255, 255))
        offset = ((new_size - new_size_x) // 2, (new_size - new_size_y) // 2)  # paste to center
        bg.paste(resized, offset)

        return bg


    def _clear(parent, full=True):
        ''' Clear all item info. '''

        if full:  # empty combobox
            parent.item_list.config(values='')
            parent.item_list.set('')

        for item in parent.prices.get_children():  # clear table
            parent.prices.delete(item)
        parent.item_picture = ImageTk.PhotoImage(Image.open('noimg.jpg'))
        parent.imagebox.config(image=parent.item_picture)
        parent.current_url = ''
        parent.lb_info.config(text='')
        parent.lb_price_sum_low.config(text='')
        parent.lb_price_sum_high.config(text='')
        parent.lb_price_sum_latest.config(text='')
        parent.lb_price_sum_average.config(text='')
        parent.lb_price_sum_moving_average.config(text='')


    @classmethod
    def open_xml_file(cls, parent):
        ''' BUTTON: <Load URL list>
            Asks for .urls file, checks if file isn't empty, sets corresponding XML file name, 
            checks if that file exists and has data, then if yes, calls load_xml() and get_item_info(). '''

        parent.xml_file = fd.askopenfilename(title='Open XML', filetypes=[('XML documents', '*.xml')])

        if parent.xml_file:  # not empty

            try:  # check if xml file exists
                open(parent.xml_file, 'r').close()
            except FileNotFoundError:
                mbox.showwarning(title='No data',
                                 message='XML not found. Check program folder or update and reload data.')
                cls._clear(parent)  # clear every widget of item info

            else:
                cls._clear(parent)
                if os.path.getsize(parent.xml_file) > 15:  # file has more data than just <root></root>
                    parent.pbase = ProductBase(parent.xml_file)  # get all info from XML and put into one list of Item objects

                    total_price = cls.get_total(parent)
                    parent.title(f'TopComputer.Ru Parser - {os.path.basename(parent.xml_file)}, total price: {total_price}')
                    
                    cls.load_item_list(parent)


    @classmethod
    def load_item_list(cls, parent):
        ''' Get data from parent.items file and put it into ComboBox (parent.item_list). '''

        # create list of items for combobox
        parent.item_list.config(values=list(item.name for item in parent.pbase.items))
        parent.item_list.current(0)   # set default combobox item
        parent.selected = parent.item_list.get()
        cls.get_item_info(parent, parent.selected)
        

    @classmethod
    def get_total(cls, parent):
        current_prices = []  # only prices for items that are in stock
        for item in parent.pbase.items:
            all_prices = list(item.prices.values())
            total_prices = len(all_prices)
            # perhaps this should be done differently
            if total_prices == 1 and all_prices[0].isnumeric():
                current_prices.append(all_prices[0])  # in case there's only one price record
            else:
                for n in range(-1, -total_prices, -1):
                    latest_price = all_prices[n]
                    if latest_price.isnumeric():  # item is in stock
                        current_prices.append(latest_price)
                        break
                
        return sum(list(map(int, current_prices)))


    @classmethod
    def select_item(cls, parent, event):
        ''' COMBOBOX COMMAND
            Select item from ComboBox. '''

        parent.selected = event.widget.get()  # item name as plain text string
        cls.get_item_info(parent, parent.selected)


    @classmethod
    def get_item_info(cls, parent, selected):
        ''' Get selected item info and show in GUI. Item is string containing item name (from XML tag <name>)'''

        cls._clear(parent, full=False)  # do not empty combobox

        for item in parent.pbase.items:
            if item.name == selected:

                # fill prices table
                for date in item.prices:
                    parent.prices.insert('', index='end', values=(date, item.prices[date]))

                # get and process image
                if item.img_url:  # exists (item has some information)
                    # ignore ssl
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE                      
                    image_b = ur.urlopen(item.img_url, context=ctx).read()  # type == bytes
                    image = Image.open(BytesIO(image_b))
                    resized_image = cls._resize_image(cls, image, 382)  # resize to fit in 382x382 px
                    parent.item_picture = ImageTk.PhotoImage(resized_image)
                    parent.imagebox.config(image=parent.item_picture)

                parent.current_url = item.url  # url as given in .urls file

                if item.info:
                    parent.lb_info.config(text=item.info)  # info from product page title

                cls.get_price_summary(parent, item)

    @classmethod
    def get_price_summary(cls, parent, item):
        ''' Get highest, lowest, latest and average price for selected item. '''

        price_list = [int(price) for price in list(item.prices.values()) if price != 'NOT IN STOCK']

        if len(price_list) == 0:  # no values added yet, nothing to display
            latest_price = min_price = max_price = alltime_average_price = twopoint_average_price = moving_average_price = 'N/A'
        else:
            latest_price = price_list[-1]
            min_price = min(price_list)
            max_price = max(price_list)
            alltime_average_price = int(sum(price_list) / len(price_list))
            twopoint_average_price = (min_price + max_price) // 2

            if len(price_list) > 9:
                moving_average_price = sum(price_list[-10:]) // 10
            else:
                moving_average_price = sum(price_list[-len(price_list):]) // len(price_list)

        if latest_price <= moving_average_price:  # set green text color if current price is lower than average
            parent.lb_price_sum_latest.config(foreground='#009900')
        else:                                     # or red text color if higher
            parent.lb_price_sum_latest.config(foreground='#990000')

        parent.lb_price_sum_latest.config(text=f'Latest price: {latest_price}')
        parent.lb_price_sum_low.config(text=f'Lowest price: {min_price}')
        parent.lb_price_sum_high.config(text=f'Highest price: {max_price}')
        parent.lb_price_sum_average.config(text=f'Average price: {alltime_average_price} / {twopoint_average_price}')
        parent.lb_price_sum_moving_average.config(text=f'Moving average price: {moving_average_price}')


    @classmethod
    def update_db(cls, parent):
        ''' Run parser and change text on button while parsing. '''

        if parent.xml_file == '':
            cls.open_xml_file(parent)  # show Open File dialogue

        if parent.xml_file != '':  # two ifs in case user pressed Cancel in Open File dialogue; do nothing in that case

            # save changes to XML (deleted price entries)
            parent.pbase.apply_changes_to_xml()

            # run parser to update
            parent.btn_parse['text'] = 'Updating...'
            parent.update()  # update window to show changed button
            try:
                tcxml.parse(parent.xml_file)
            except FileNotFoundError:
                mbox.showwarning(title='No data',
                                 message='XML file not found. Check program folder or update data.')
            parent.btn_parse['text'] = 'Update database'  # set button text back to default
            cls.load_item_list(parent)
            parent.pbase.parse_xml()  # add new prices to internal database
            cls.get_item_info(parent, parent.item_list.get())
            parent.title(f'TopComputer.Ru Parser - {os.path.basename(parent.xml_file)}, total price: {cls.get_total(parent)}')


    def delete_price(parent, event):
        ''' Delete selected price entry from table, ProductBase and mark for deletion from XML on exit. '''

        price_to_delete = parent.prices.focus()
        price_date = parent.prices.item(price_to_delete)['values'][0]
        parent.prices.delete(price_to_delete)                   # delete from TreeView
        parent.pbase.delete_price(parent.selected, price_date)  # delete from ProductBase


    def call_linkedit(parent):
        ''' Open Link Editor window. '''
        LinkEditor()
        

    def browse(parent):
        ''' Open URL in default browser. '''
        if parent.current_url:  # not empty
            try:
                wb.open(parent.current_url)
            except AttributeError:
                mbox.showwarning(title='No URL',
                                 message='URL not found or invalid.')
