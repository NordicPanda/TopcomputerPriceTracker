import tkinter as tk

from tkinter.ttk import Button, Label, Frame, Combobox, Treeview, Scrollbar, Style
from PIL import Image, ImageTk

from gui_methods import GUIMethods as gm  # local module


class GUI(tk.Tk):
    
    def __init__(self):
        super().__init__()

        # setup window
        self.geometry('650x585')
        self.resizable(False, False)
        self.title('TopComputer.Ru Parser')

        # buttons at the top
        self.buttons_frame = Frame()
        self.buttons_frame.pack(fill='both', pady=10)

        self.btn_parse = Button(self.buttons_frame, text='Update database',
                                command=lambda: gm.update_db(self), width=18)
        self.btn_parse.pack(side='left', padx=10)

        self.btn_open_urls_file = Button(self.buttons_frame, text='Load XML',
                                         command=lambda: gm.open_xml_file(self), width=15)
        self.btn_open_urls_file.pack(side='left')
        
        self.btn_edit_urls = Button(self.buttons_frame, text='Edit XML', 
                                    command=lambda: gm.call_linkedit(self), width=15)
        self.btn_edit_urls.pack(side='left', padx=10)
        
        self.btn_exit = Button(self.buttons_frame, text='Exit', command=self.destroy, width=10)
        self.btn_exit.pack(side='right', padx=10)

        # dropdown list
        self.item_list = Combobox(state='readonly', height=20)
        self.item_list.pack(fill='both', padx=10)
        self.item_list.bind('<<ComboboxSelected>>', lambda event: gm.select_item(self, event))

        # frames for better elements alignment control
        self.info_frame_left = Frame()
        self.info_frame_left.pack(side='left', fill='both', pady=10)

        self.info_frame_right = Frame()
        self.info_frame_right.pack(side='right', fill='both', pady=10)

        self.info_frame_prices = Frame(self.info_frame_right)
        self.info_frame_prices.pack(side='top', fill='both')

        self.info_frame_price_summary = Frame(self.info_frame_right)
        self.info_frame_price_summary.pack(fill='both')

        # labels under prices table to show latest, lowest and highest price
        self.lb_price_sum_latest = Label(self.info_frame_price_summary, anchor='center', font=('Arial', 12, 'bold'))
        self.lb_price_sum_latest.pack(padx=10, fill='x')

        self.lb_price_sum_low = Label(self.info_frame_price_summary, anchor='center', font=('Arial', 10))
        self.lb_price_sum_low.pack(padx=10, fill='x')

        self.lb_price_sum_high = Label(self.info_frame_price_summary,  anchor='center', font=('Arial', 10))
        self.lb_price_sum_high.pack(padx=10, fill='x')
        
        self.lb_price_sum_average = Label(self.info_frame_price_summary, anchor='center', font=('Arial', 10))
        self.lb_price_sum_average.pack(padx=10, fill='x')

        self.lb_price_sum_moving_average = Label(self.info_frame_price_summary, anchor='center', font=('Arial', 10))
        self.lb_price_sum_moving_average.pack(padx=10, fill='x')


        # image
        self.noimg = ImageTk.PhotoImage(file='noimg.jpg')
        self.imagebox = Label(self.info_frame_left, image=self.noimg, anchor='center', background='white')
        self.imagebox.pack(anchor='center', side='top', padx=10, fill='both')

        # info label (from tk to set height parameter, which ttk label doesn't have)
        self.lb_info = tk.Label(self.info_frame_left, width=55, height=2, pady=10,
                                wraplength=380, anchor='center', justify='center')
        self.selected_item = self.item_list.get()
        self.lb_info.pack(anchor='center', side='top')

        # URL button
        self.btn_browse = Button(self.info_frame_left, width=20, text='Go to store', command=lambda: gm.browse(self))
        self.btn_browse.pack(anchor='center', side='top')

        # table with dates and prices
        self.prices = Treeview(self.info_frame_prices, height=18, show='headings', columns=('col1', 'col2'))
        self.prices.heading('col1', text='Date')
        self.prices.heading('col2', text='Price')
        self.prices.column('col1', anchor='w', width=110)
        self.prices.column('col2', anchor='center', width=110)
        self.prices.bind('<Delete>', lambda event: gm.delete_price(self, event))

        # scroll for table
        self.vscroll = Scrollbar(self.info_frame_prices, orient='vertical', command=self.prices.yview)
        self.prices.config(yscrollcommand=self.vscroll.set)

        self.vscroll.pack(side='right', fill='y')
        self.prices.pack(side='top')

        # no xml file selected on start
        self.xml_file = ''
        self.current_url = ''
        self.selected = ''


GUI().mainloop()