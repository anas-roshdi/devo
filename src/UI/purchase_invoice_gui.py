"""
Purchase Invoice Window - Handles creating and saving purchase invoices.
========================================================================
Inherits from BaseInvoiceWindow for shared invoice functionality.
Adds: supplier name entry, purchase-specific pricing and saving.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.UI.base_invoice import BaseInvoiceWindow
from src.utils.widgets import CalendarHelper
from config import Colors, Fonts, WindowConfig, UNKNOWN_SUPPLIER


class PurchaseInvoiceWindow(BaseInvoiceWindow):
    """Purchase invoice window with supplier entry and cost-based pricing."""

    # =========================================================
    # CONFIGURATION OVERRIDES
    # =========================================================

    def get_window_title(self):
        return "Devo - Smart Purchase Invoice"

    def get_window_geometry(self):
        return WindowConfig.PURCHASE_INVOICE

    def get_product_type(self):
        return "buyable"

    def get_confirm_button_config(self):
        return ("Confirm Purchase", Colors.RED_DARK)

    def get_total_label_config(self):
        return ("Total Cost:", Colors.RED)

    def get_price_label(self):
        return "Cost Price"

    def get_basket_item_dict(self, p_id, p_name, qty, price, subtotal):
        """Override to use 'cost' key instead of 'price' for purchase items."""
        return {'id': p_id, 'name': p_name, 'qty': qty, 'cost': price, 'subtotal': subtotal}

    # =========================================================
    # HEADER: Supplier & Date Entry
    # =========================================================

    def create_header_frame(self):
        """Create the top frame with supplier name entry and date picker."""
        top_frame = tk.LabelFrame(self.root, text="Purchase Header", padx=10, pady=10)
        top_frame.pack(fill="x", padx=20, pady=10)

        # Supplier
        tk.Label(top_frame, text="Supplier Name:").grid(row=0, column=0, sticky="w")
        self.ent_supplier = tk.Entry(top_frame, width=30)
        self.ent_supplier.grid(row=0, column=1, padx=10)

        # Date
        tk.Label(top_frame, text="Date:").grid(row=0, column=2, padx=10)
        self.ent_date = tk.Entry(top_frame, width=15)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=0, column=3)

        # Calendar popup button
        tk.Button(top_frame, text="📅",
                  command=lambda: CalendarHelper.show_calendar(self.root, self.ent_date)
                  ).grid(row=0, column=4, padx=5)

    # =========================================================
    # SAVE INVOICE
    # =========================================================

    def save_invoice(self):
        """Finalize the purchase by saving the header and items to the database."""
        if not self.basket:
            messagebox.showwarning("Empty", "No items to save.")
            return

        date_str = self.get_validated_date()
        if not date_str:
            return

        supplier = self.ent_supplier.get() or UNKNOWN_SUPPLIER
        total_amount = sum(item['subtotal'] for item in self.basket)

        try:
            p_invoice_id = self.db.save_purchase_invoice(supplier, date_str, total_amount, self.basket)
            messagebox.showinfo("Success", f"Purchase Invoice #{p_invoice_id} saved.")
            self.clear_invoice()
            self.ent_supplier.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PurchaseInvoiceWindow(root)
    root.mainloop()