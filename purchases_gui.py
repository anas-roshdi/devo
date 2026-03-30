import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database_manager import DatabaseManager

class PurchasesWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Record Purchase")
        self.root.geometry("450x550")
        
        self.db = DatabaseManager()
        self.product_map = {} # Stores: name -> (id, default_price)
        
        self.create_widgets()
        self.load_suppliers_items()

    def create_widgets(self):
        """Build UI with auto-calculation and manual price override."""
        tk.Label(self.root, text="Record New Purchase", font=("Arial", 16, "bold"), fg="dark blue").pack(pady=10)

        # 1. Item Selection
        tk.Label(self.root, text="Select Item:").pack(pady=5)
        self.combo_item = ttk.Combobox(self.root, state="readonly", width=30)
        self.combo_item.pack(pady=5)
        self.combo_item.bind("<<ComboboxSelected>>", self.on_item_select)

        # 2. Unit Price (Manual Override allowed)
        tk.Label(self.root, text="Unit Price (SAR):").pack(pady=5)
        self.ent_unit_price = tk.Entry(self.root)
        self.ent_unit_price.pack(pady=5)
        self.ent_unit_price.bind("<KeyRelease>", self.auto_calculate) # Calculate on typing

        # 3. Quantity Input
        tk.Label(self.root, text="Quantity:").pack(pady=5)
        self.ent_qty = tk.Entry(self.root)
        self.ent_qty.insert(0, "1")
        self.ent_qty.pack(pady=5)
        self.ent_qty.bind("<KeyRelease>", self.auto_calculate) # Calculate on typing

        # 4. Total Cost Display (Calculated)
        tk.Label(self.root, text="Total Cost (Calculated):", font=("Arial", 9, "bold")).pack(pady=5)
        self.lbl_total = tk.Label(self.root, text="0.00 SAR", fg="red", font=("Arial", 12, "bold"))
        self.lbl_total.pack(pady=5)

        # 5. Date Input
        tk.Label(self.root, text="Purchase Date (YYYY-MM-DD):").pack(pady=5)
        self.ent_date = tk.Entry(self.root)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.pack(pady=5)

        # 6. Action Button
        tk.Button(self.root, text="Save Purchase", bg="orange", width=20, command=self.save_purchase).pack(pady=20)

    def load_suppliers_items(self):
        """Fetch buyable items with their default unit prices."""
        items = self.db.get_products_by_type('buyable')
        names = []
        for i in items:
            p_id, name, cat, price, p_type, size = i
            display_name = f"{name} ({size})"
            # Map name to ID and the default Price from database
            self.product_map[display_name] = (p_id, price)
            names.append(display_name)
        self.combo_item['values'] = names

    def on_item_select(self, event):
        """Fill unit price automatically when an item is chosen."""
        selected = self.combo_item.get()
        default_price = self.product_map[selected][1]
        self.ent_unit_price.delete(0, tk.END)
        self.ent_unit_price.insert(0, str(default_price))
        self.auto_calculate()

    def auto_calculate(self, event=None):
        """Update the Total Cost label dynamically."""
        try:
            unit_p = float(self.ent_unit_price.get())
            qty = float(self.ent_qty.get())
            total = unit_p * qty
            self.lbl_total.config(text=f"{total:.2f} SAR")
        except ValueError:
            self.lbl_total.config(text="0.00 SAR")

    def save_purchase(self):
        """Save the transaction using the potentially modified price."""
        selected = self.combo_item.get()
        unit_p_str = self.ent_unit_price.get()
        qty_str = self.ent_qty.get()
        p_date = self.ent_date.get()

        try:
            datetime.strptime(p_date, "%Y-%m-%d")
            p_id = self.product_map[selected][0]
            unit_p = float(unit_p_str)
            qty = float(qty_str)
            total_cost = unit_p * qty # We save the actual cost paid
            
            query = "INSERT INTO purchases (product_id, quantity, cost_price, purchase_date) VALUES (?, ?, ?, ?)"
            self.db.execute_query(query, (p_id, qty, total_cost, p_date))
            
            messagebox.showinfo("Success", f"Recorded purchase for {total_cost:.2f} SAR")
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("Error", "Check your inputs (Numbers and Date format)")

    def clear_fields(self):
        self.ent_unit_price.delete(0, tk.END)
        self.ent_qty.delete(0, tk.END)
        self.ent_qty.insert(0, "1")
        self.lbl_total.config(text="0.00 SAR")

if __name__ == "__main__":
    app_root = tk.Tk()
    PurchasesWindow(app_root)
    app_root.mainloop()