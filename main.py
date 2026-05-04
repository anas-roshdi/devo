"""
Devo Business Management System - Main Dashboard
==================================================
Entry point for the application. Displays the main navigation menu
with buttons to access all system modules.
"""

import tkinter as tk
from tkinter import messagebox

# Import the window classes from their respective files
from src.UI.manage_products_gui import ManageProductsWindow 
from src.UI.customer_gui import CustomerWindow
from src.UI.sales_invoice_gui import SalesInvoiceWindow
from src.UI.purchase_invoice_gui import PurchaseInvoiceWindow
from src.UI.reports_gui import ReportsWindow
from config import Colors, Fonts, WindowConfig

class DevoDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo Business Management System - Dashboard")
        
        geo, min_w, min_h = WindowConfig.DASHBOARD
        self.root.geometry(geo)
        self.root.minsize(min_w, min_h)
        self.root.configure(bg=Colors.BACKGROUND)
        
        # Initialize the main dashboard layout
        self.create_widgets()

    def create_widgets(self):
        """Build the main menu interface with navigation buttons."""
        
        # --- Top Header Section ---
        header_frame = tk.Frame(self.root, bg=Colors.PRIMARY_DARK, height=100)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="DEVO MANAGEMENT SYSTEM", fg=Colors.TEXT_WHITE, 
                 bg=Colors.PRIMARY_DARK, font=Fonts.HEADER_LARGE, pady=20).pack()

        # --- Main Navigation Menu Grid ---
        menu_frame = tk.Frame(self.root, bg=Colors.BACKGROUND, pady=20)
        menu_frame.pack(expand=True)

        # Standard button style for the main menu grid
        btn_style = {"font": Fonts.BODY_BOLD, "width": 22, "height": 4, 
                     "fg": Colors.TEXT_WHITE, "bd": 0}

        # Button 1: Product Management
        tk.Button(menu_frame, text="📦\nMANAGE PRODUCTS", bg=Colors.BLUE, **btn_style,
                  command=self.open_manage_products).grid(row=0, column=0, padx=15, pady=15)

        # Button 2: Customer & Shop Management
        tk.Button(menu_frame, text="👥\nMANAGE CUSTOMERS", bg=Colors.PURPLE, **btn_style,
                  command=self.open_customers).grid(row=0, column=1, padx=15, pady=15)

        # Button 3: Sales Invoicing Module
        tk.Button(menu_frame, text="🛒\nSALES INVOICE", bg=Colors.GREEN, **btn_style,
                  command=self.open_sales).grid(row=1, column=0, padx=15, pady=15)

        # Button 4: Purchase Invoicing Module
        tk.Button(menu_frame, text="📥\nPURCHASE INVOICE", bg=Colors.RED, **btn_style,
                  command=self.open_purchases).grid(row=1, column=1, padx=15, pady=15)

        # Button 5: Comprehensive Financial Reports (Spans full width)
        tk.Button(menu_frame, text="📊\nFINANCIAL REPORTS & EXCEL", bg=Colors.YELLOW, 
                  fg=Colors.TEXT_BLACK, font=Fonts.BODY_BOLD, width=48, height=3, bd=0,
                  command=self.open_reports).grid(row=2, column=0, columnspan=2, pady=15)

    # --- Navigation Logic: Opening Sub-Windows ---

    def open_manage_products(self):
        """Open the product management window as a new top-level window."""
        new_win = tk.Toplevel(self.root)
        ManageProductsWindow(new_win)

    def open_customers(self):
        """Open the customer/shop management window."""
        new_win = tk.Toplevel(self.root)
        CustomerWindow(new_win)

    def open_sales(self):
        """Open the sales invoice interface."""
        new_win = tk.Toplevel(self.root)
        SalesInvoiceWindow(new_win)

    def open_purchases(self):
        """Open the purchase invoice interface."""
        new_win = tk.Toplevel(self.root)
        PurchaseInvoiceWindow(new_win)

    def open_reports(self):
        """Open the financial analytics and reporting window."""
        new_win = tk.Toplevel(self.root)
        ReportsWindow(new_win)

if __name__ == "__main__":
    # Standard application entry point
    root = tk.Tk()
    app = DevoDashboard(root)
    root.mainloop()