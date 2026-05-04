"""
Sales Invoice Window - Handles creating and saving sales invoices.
==================================================================
Inherits from BaseInvoiceWindow for shared invoice functionality.
Adds: customer selection, smart pricing based on last sale history.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.UI.base_invoice import BaseInvoiceWindow
from src.utils.widgets import CalendarHelper
from config import Colors, Fonts, WindowConfig, DEFAULT_CUSTOMER


class SalesInvoiceWindow(BaseInvoiceWindow):
    """Sales invoice window with customer selection and historical price lookup."""

    # =========================================================
    # CONFIGURATION OVERRIDES
    # =========================================================

    def get_window_title(self):
        return "Devo - Smart Sales Invoice"

    def get_window_geometry(self):
        return WindowConfig.SALES_INVOICE

    def get_product_type(self):
        return "sellable"

    def get_confirm_button_config(self):
        return ("Confirm & Save Invoice", Colors.GREEN_DARK)

    def get_total_label_config(self):
        return ("Total:", Colors.TEXT_DARK_GREEN)

    def get_price_label(self):
        return "Unit Price"

    # =========================================================
    # HEADER: Customer & Date Selection
    # =========================================================

    def create_header_frame(self):
        """Create the top frame with customer selection and date picker."""
        top_frame = tk.LabelFrame(self.root, text="Invoice Header", padx=10, pady=10)
        top_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(top_frame, text="Select Shop/Customer:").grid(row=0, column=0, sticky="w")
        self.combo_customer = ttk.Combobox(top_frame, state="readonly", width=30)
        self.combo_customer.grid(row=0, column=1, padx=10)

        tk.Label(top_frame, text="Date:").grid(row=0, column=2, padx=10)
        
        # Date field
        self.ent_date = tk.Entry(top_frame, width=15)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=0, column=3)

        # Calendar popup button
        tk.Button(top_frame, text="📅", 
                  command=lambda: CalendarHelper.show_calendar(self.root, self.ent_date)
                  ).grid(row=0, column=4, padx=5)

    # =========================================================
    # DATA LOADING (extends base)
    # =========================================================

    def load_initial_data(self):
        """Load customers and products into their respective dropdowns."""
        # Load Customers
        customers = self.db.get_all_customers()
        self.customer_map = {c[1]: c[0] for c in customers}
        self.combo_customer['values'] = list(self.customer_map.keys())
        self.combo_customer.set(DEFAULT_CUSTOMER)

        # Bind customer change to re-check pricing
        self.combo_customer.bind("<<ComboboxSelected>>", self.on_product_select)

        # Load Products (from base class)
        super().load_initial_data()

    # =========================================================
    # SMART PRICING: Fetch last sold price for this customer
    # =========================================================

    def on_product_select(self, event):
        """
        Auto-fill the price field with smart pricing logic.
        If a specific shop is selected (not General Customer), 
        fetch the last sold price for this product to that customer.
        """
        p_name = self.combo_product.get()
        customer_name = self.combo_customer.get()
        
        if p_name not in self.product_map:
            return

        # Get the base price from the product map (default price)
        default_price = self.product_map[p_name][1]
        p_id = self.product_map[p_name][0]
        final_price = default_price

        # Check if the customer is a specific shop (not general)
        if customer_name != DEFAULT_CUSTOMER:
            customer_id = self.customer_map.get(customer_name)
            last_price = self.db.get_last_sale_price(customer_id, p_id)
            if last_price is not None:
                final_price = last_price

        # Populate the price entry field (remains editable for the user)
        self.ent_price.delete(0, tk.END)
        self.ent_price.insert(0, str(final_price))

        # Move the cursor to the Quantity field automatically
        self.ent_qty.focus_set()

    # =========================================================
    # SAVE INVOICE
    # =========================================================

    def save_invoice(self):
        """Save the full invoice (Header and Details) to the database."""
        if not self.basket:
            messagebox.showwarning("Empty", "No items in the basket.")
            return

        date_str = self.get_validated_date()
        if not date_str:
            return

        customer_name = self.combo_customer.get()
        customer_id = self.customer_map[customer_name]
        total_amount = sum(item['subtotal'] for item in self.basket)

        try:
            invoice_id = self.db.save_sale_invoice(customer_id, date_str, total_amount, self.basket)
            messagebox.showinfo("Success", f"Invoice #{invoice_id} saved successfully for {customer_name}.")
            self.clear_invoice()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SalesInvoiceWindow(root)
    root.mainloop()