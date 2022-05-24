import codecs
import os.path
import ssl
import tkinter as tk
import tkinter.messagebox as mbox
import tkinter.filedialog as fd
import urllib.request as ur
import webbrowser as wb
import xml.etree.ElementTree as et

from tkinter.ttk import Treeview, Scrollbar, Button

import tcxml


class LinkEditor(tk.Toplevel):
    def __init__(self):
        super().__init__()
    
        # setup window
        self.geometry('650x500')
        self.minsize(300, 500)
        self.maxsize(self.winfo_screenwidth(), 500)
        self.title('Link editor')

        self.entry_frame = tk.Frame(self)
        self.entry_frame.pack(padx=10, pady=10, fill='x')
        
        self.entry = tk.Entry(self.entry_frame)
        self.entry.pack(side='left', fill='x', expand='y')
        
        self.btn_add = Button(self.entry_frame, width=10, text='Add link', command=self.add_url)
        self.btn_add.pack(side='right', padx=10)
        
        self.urls_frame = tk.Frame(self)
        self.urls_frame.pack(padx=10, pady=10, fill='x')

        self.url_list = Treeview(self.urls_frame, height=18, show='headings', columns=('col1', 'col2'))
        self.url_list.heading('col1', text='URL')
        self.url_list.heading('col2', text='Name')
        self.url_list.column('col1', anchor='w', width=150)
        self.url_list.column('col2', anchor='w', width=250)
        self.url_list.bind('<Button-3>', self.show_popup_menu)

        self.vscroll = Scrollbar(self.urls_frame, orient='vertical', command=self.url_list.yview)
        self.url_list.config(yscrollcommand=self.vscroll.set)

        self.vscroll.pack(side='right', fill='y')
        self.url_list.pack(side='right', fill='x', expand='y')

        self.buttons_frame = tk.Frame(self)
        self.buttons_frame.pack(side='top', fill='x', padx=10)
        
        self.btn_load = Button(self.buttons_frame, text='Load list', command=self.load_xml)
        self.btn_load.pack(side='left')

        self.btn_save = Button(self.buttons_frame, text='Save list', command=self.save_xml)
        self.btn_save.pack(side='left', padx=10)

        self.btn_cancel = Button(self.buttons_frame, text='Close', command=self.close)
        self.btn_cancel.pack(side='right')
        
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label='Delete', command=self.delete_sel)
        self.popup_menu.add_command(label='Open link in browser', command=self.open_url)
        
        self.bind('<Return>', self.add_url)
        self.is_saved = True  # sets to False when changes are made and to True when Save button is pressed


    def add_url(self, event=''):  # empty event if adding by button
        ''' Check entered URL for validity and if valid, add to list (Treeview). '''

        url = self.entry.get()
        self.btn_add.config(text='Checking...')
        self.btn_add.update()
        
        # url should begin in https:// and end in slash
        if 'https://' not in url:
            url = 'https://' + url
        if url[-1] != '/':
            url += '/'
            
        try:  # check if entry has valid url
            if 'topcomputer.ru/tovary' not in url:
                raise ValueError

            name = tcxml.get_item_name(tcxml.open_url(url))

        except ValueError:
            mbox.showwarning(message='Invalid URL or not a TopComputer.Ru product page URL', title='Error', parent=self)
        else:  # add url and name to table

            self.url_list.insert('', index='end', 
                                 values=(url, name if name != '' else 'Item not found, possibly wrong URL'))
            self.entry.delete(0, 'end')
        finally:
            self.btn_add.config(text='Add link')

        self.is_saved = False


    def load_xml(self):
        ''' Load URLs from file and put into TreeView list. '''
        
        # show standard Open File dialog
        xml_filename = fd.askopenfilename(title='Open XML',
                                       filetypes=[('XML documnents', '*.xml')], parent=self)
        if xml_filename == '':  # user pressed Cancel
            return
        
        for item in self.url_list.get_children():  # clear table
            self.url_list.delete(item)        

        data = et.parse(xml_filename)
        root = data.getroot()
        urls = [element.text for element in root.findall('item/url')]

        total_urls = len(urls)
        for n in range(total_urls):
            url = urls[n]
            self.title(f'Link editor - Loading URL {n+1} of {total_urls}...')  # show links counter in window title
            
            name = tcxml.get_item_name(tcxml.open_url(url))
            self.url_list.insert('', index='end',
                                 values=(url, name if name != '' else 'Item not found, possibly wrong URL'))
            self.url_list.update()
            
        self.title('Link editor')  # reset window title


    def save_xml(self):
        ''' Save current url list to XML file. This file will be used by tcxml.py to get urls from.
        a) If file exists, check if url is in there
            i)  If it is, do nothing, skip to next url
            ii) Else add new <item> block
        b) Else create XML with structure like this:
            <root>
              <item name='{name}>
                <url> {url} </url>
                  </item>
                    ...
            </root>   '''
        
        xml_filename = fd.asksaveasfilename(title='Save',
                                            filetypes=[('XML documents', '*.xml')], parent=self)

        if xml_filename[-4:] != '.xml':     # ensure file has proper extension
            xml_filename += '.xml'

        if os.path.isfile(xml_filename):    # file exists
            data = et.parse(xml_filename)
            root = data.getroot()
            for element in root.iter():
                print(element.tag)
                print('----')
            
            urls = [url.text for url in root.findall('item/url')]

            for entry in self.url_list.get_children():  # search for urls
                entry_url = self.url_list.item(entry)['values'][0]
                if entry_url not in urls:   # item was not added before
                    new_item = et.SubElement(root, 'item', name=self.url_list.item(entry)['values'][1])
                    et.SubElement(new_item, 'url').text = entry_url
                

        else:                               # file does not exist
            xml_file = open(xml_filename, 'w').close()  # create file
            root = et.Element('root')
            for entry in self.url_list.get_children():  # search for urls
                url = self.url_list.item(entry)['values'][0]
                item_name = self.url_list.item(entry)['values'][1]
                new_item = et.SubElement(root, 'item', name=item_name)
                et.SubElement(new_item, 'url').text = url

        for element in root.iter():
            print(element.tag)
        
        et.ElementTree(root).write(xml_filename, encoding='utf-8', xml_declaration=True)
        self.is_saved = True


    def close(self):
        ''' Close window. '''
        if self.is_saved:
            self.destroy()
        else:  # list was changed but not saved
            answer = mbox.askquestion('URLs list not saved', 'Close without saving?', parent=self)
            if answer == 'yes':
                self.destroy()

        
    def show_popup_menu(self, event):
        ''' Set selection to right-clicked element and show popup menu for it. '''

        # NOTE: event.x and event.y return mouse coordinates relative to widget,
        # but popup appears in coordinates relative to screen
        # so need to use event.x_root and event.y_root, which return coordinates relative to window

        tree = self.url_list  # for shortness
        # Treeview.identify_element() returns element type, .identify() returns its id
        self.current_item = tree.identify('item', event.x, event.y)
        
        tree.selection_set(self.current_item)
        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        

    def delete_sel(self):
        ''' Popup menu command. Delete selected item. '''
        self.url_list.delete(self.url_list.selection())


    def open_url(self):
        ''' Popup menu command. Open selected item's URL in default browser. '''
        wb.open(self.url_list.item(self.current_item)['values'][0])


if __name__ == '__main__':
    LinkEditor().mainloop()
