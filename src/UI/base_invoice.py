"""
Base Invoice Window - Shared logic for Sales and Purchase invoices.
===================================================================
Contains common functionality: basket management, product combo loading,
table display, keyboard shortcuts, and total calculation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.database.database_manager import DatabaseManager
from src.utils.widgets import CalendarHelper
from config import Colors, Fonts, DATE_FORMAT


class BaseInvoiceWindow:
    """
    Abstract base class for invoice windows (Sales & Purchase).
    Subclasses must implement:
        - get_window_title() -> str
        - get_window_geometry() -> tuple (geometry, min_w, min_h)
        - get_product_type() -> str ('sellable' or 'buyable')
        - create_header_frame() -> None
        - get_price_from_item(item) -> float
        - save_invoice() -> None
    """

    def __init__(self, root):
        self.root = root
        title = self.get_window_title()
        geometry, min_w, min_h = self.get_window_geometry()
        
        self.root.title(title)
        self.root.geometry(geometry)
        self.root.minsize(min_w, min_h)
        
        # Initialize database connection
        self.db = DatabaseManager()
        # Temporary list to hold invoice items before database commit
        self.basket = []
        
        # Build UI and load initial data
        self.create_widgets()
        self.load_initial_data()

    # =========================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # =========================================================

    def get_window_title(self):
        raise NotImplementedError

    def get_window_geometry(self):
        raise NotImplementedError

    def get_product_type(self):
        raise NotImplementedError

    def create_header_frame(self):
        """Create the top frame (customer/supplier info). Implemented by subclass."""
        raise NotImplementedError

    def save_invoice(self):
        """Save the complete invoice to database. Implemented by subclass."""
        raise NotImplementedError

    def get_basket_item_dict(self, p_id, p_name, qty, price, subtotal):
        """Build the basket item dict. Subclass can override key names (price vs cost)."""
        return {'id': p_id, 'name': p_name, 'qty': qty, 'price': price, 'subtotal': subtotal}

    def get_confirm_button_config(self):
        """Return (text, bg_color) for the confirm button. Override in subclass."""
        return ("Confirm & Save Invoice", Colors.GREEN_DARK)

    def get_total_label_config(self):
        """Return (prefix_text, fg_color) for the total label. Override in subclass."""
        return ("Total:", Colors.TEXT_DARK_GREEN)

    def get_price_label(self):
        """Return the label text for the price column. Override in subclass."""
        return "Unit Price"

    # =========================================================
    # UI CONSTRUCTION
    # =========================================================

    def create_widgets(self):
        """Create and arrange all shared UI components."""
        
        # --- Top Frame: Invoice Header (Customer/Supplier specific) ---
        self.create_header_frame()

        # --- Middle Frame: Add Product to Basket ---
        add_frame = tk.LabelFrame(self.root, text="Add Product", padx=10, pady=10)
        add_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(add_frame, text="Product:").grid(row=0, column=0)
        self.combo_product = ttk.Combobox(add_frame, state="readonly", width=25)
        self.combo_product.grid(row=0, column=1, padx=5)
        
        tk.Label(add_frame, text="Qty:").grid(row=0, column=2)
        self.ent_qty = tk.Entry(add_frame, width=10)
        self.ent_qty.grid(row=0, column=3, padx=5)

        tk.Label(add_frame, text=f"{self.get_price_label()}:").grid(row=0, column=4)
        self.ent_price = tk.Entry(add_frame, width=10)
        self.ent_price.grid(row=0, column=5, padx=5)

        tk.Button(add_frame, text="Add to Basket", bg=Colors.BLUE, fg=Colors.TEXT_WHITE,
                  font=Fonts.BTN_SMALL, command=self.add_to_basket).grid(row=0, column=6, padx=15)

        # --- Bottom Frame: Treeview Table for Invoice Items ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "Product Name", "Qty", self.get_price_label(), "Subtotal")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)

        # Scrollbar for the table
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # --- Footer Section: Total Display and Action Buttons ---
        footer_panel = tk.Frame(self.root, padx=20, pady=10)
        footer_panel.pack(fill="x")

        total_prefix, total_color = self.get_total_label_config()
        self.lbl_total = tk.Label(footer_panel, text=f"{total_prefix} 0.00", 
                                  font=Fonts.HEADER_SMALL, fg=total_color)
        self.lbl_total.pack(side="right")

        confirm_text, confirm_color = self.get_confirm_button_config()
        tk.Button(footer_panel, text=confirm_text, bg=confirm_color, fg=Colors.TEXT_WHITE,
                  font=Fonts.BTN_LARGE, command=self.save_invoice).pack(side="left", pady=10)
        
        tk.Button(footer_panel, text="Remove Selected", bg=Colors.RED, fg=Colors.TEXT_WHITE,
                  command=self.remove_from_basket).pack(side="left", padx=10)

        # --- Event Bindings ---
        self.combo_product.bind("<<ComboboxSelected>>", self.on_product_select)
        
        # Keyboard shortcuts (Enter key to add item)
        self.ent_qty.bind("<Return>", lambda event: self.add_to_basket())
        self.ent_price.bind("<Return>", lambda event: self.add_to_basket())

        # Select all text automatically when the price field gains focus
        self.ent_price.bind("<FocusIn>", self.select_all_price)

    # =========================================================
    # DATA LOADING
    # =========================================================

    def load_initial_data(self):
        """Fetch and populate products into the dropdown."""
        product_type = self.get_product_type()
        products = self.db.get_products_for_combo(product_type)

        self.product_map = {}
        display_list = []

        for p in products:
            p_id, name, price, cat, size = p
            display_text = f"{name}"

            # Only include Category/Size in display if they have values
            if cat and str(cat).strip():
                display_text += f" ({cat})"
            if size and str(size).strip():
                display_text += f" ({size})"

            # Map the formatted text to its ID and price
            self.product_map[display_text] = (p_id, price)
            display_list.append(display_text)

        self.combo_product['values'] = display_list

    # =========================================================
    # EVENT HANDLERS
    # =========================================================

    def on_product_select(self, event):
        """Auto-fill price field based on selected product. Override for custom behavior."""
        p_name = self.combo_product.get()
        if p_name in self.product_map:
            default_price = self.product_map[p_name][1]
            self.ent_price.delete(0, tk.END)
            self.ent_price.insert(0, str(default_price))
            # Move cursor to Quantity field automatically
            self.ent_qty.focus_set()

    def select_all_price(self, event):
        """Select the entire content of the price entry field for easy editing."""
        self.root.after_idle(lambda: self.ent_price.selection_range(0, tk.END))
        self.root.after_idle(lambda: self.ent_price.icursor(tk.END))

    # =========================================================
    # BASKET OPERATIONS
    # =========================================================

    def add_to_basket(self, event=None):
        """Process and add the selected product to the temporary list and UI table."""
        p_name = self.combo_product.get()
        qty_str = self.ent_qty.get()
        price_str = self.ent_price.get()

        if not p_name or not qty_str or not price_str:
            messagebox.showwarning("Input Error", "Please fill all product details.")
            return

        try:
            qty = int(qty_str)
            price = float(price_str)
            subtotal = qty * price
            p_id = self.product_map[p_name][0]

            # Add to memory list
            item_dict = self.get_basket_item_dict(p_id, p_name, qty, price, subtotal)
            self.basket.append(item_dict)
            
            # Add to visual table
            self.tree.insert("", "end", values=(p_id, p_name, qty, f"{price:.2f}", f"{subtotal:.2f}"))
            
            self.update_total()
            # Reset Qty field for the next item
            self.ent_qty.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Quantity and Price must be numeric.")

        # After adding, move focus back to the product combo for the next item
        self.combo_product.focus_set()

    def remove_from_basket(self):
        """Delete selected rows from both the internal list and the table UI."""
        selected = self.tree.selection()
        if selected:
            for item in selected:
                idx = self.tree.index(item)
                del self.basket[idx]
                self.tree.delete(item)
            self.update_total()

    def update_total(self):
        """Sum the subtotals of all items currently in the basket."""
        total = sum(item['subtotal'] for item in self.basket)
        total_prefix, _ = self.get_total_label_config()
        self.lbl_total.config(text=f"{total_prefix} {total:.2f}")

    def clear_invoice(self):
        """Reset the UI and memory list to prepare for a new invoice."""
        self.basket = []
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.update_total()
        self.combo_product.set("")

    # =========================================================
    # HELPER: Date validation
    # =========================================================

    def get_validated_date(self):
        """Validate and return the date string, or None if invalid."""
        date_str = self.ent_date.get()
        try:
            datetime.strptime(date_str, DATE_FORMAT)
            return date_str
        except ValueError:
            messagebox.showerror("Date Error", "Please use YYYY-MM-DD format for the date.")
            return None
