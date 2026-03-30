import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime  # For handling dates
from database_manager import DatabaseManager

class SalesWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Record Sale")
        self.root.geometry("450x500") # Increased height for the date field
        
        self.db = DatabaseManager()
        self.product_map = {}
        
        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        """Create UI elements including a manual date override."""
        tk.Label(self.root, text="Record New Sale", font=("Arial", 16, "bold")).pack(pady=10)

        # 1. Product Selection
        tk.Label(self.root, text="Select Product:").pack(pady=5)
        self.combo_product = ttk.Combobox(self.root, state="readonly", width=30)
        self.combo_product.pack(pady=5)
        self.combo_product.bind("<<ComboboxSelected>>", self.update_price_label)

        # 2. Quantity Input
        tk.Label(self.root, text="Quantity:").pack(pady=5)
        self.ent_qty = tk.Entry(self.root)
        self.ent_qty.insert(0, "1")
        self.ent_qty.pack(pady=5)

        # 3. Date Input (New Feature)
        tk.Label(self.root, text="Date (YYYY-MM-DD):").pack(pady=5)
        self.ent_date = tk.Entry(self.root)
        # Set default value to TODAY'S date
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.ent_date.insert(0, today_str)
        self.ent_date.pack(pady=5)

        # 4. Price Display
        self.lbl_total = tk.Label(self.root, text="Total Price: 0.00 SAR", font=("Arial", 10, "italic"))
        self.lbl_total.pack(pady=10)

        # 5. Action Buttons
        tk.Button(self.root, text="Save Sale", bg="green", fg="white", 
                  width=20, command=self.save_sale).pack(pady=20)

    def load_products(self):
        """Load only sellable products."""
        products = self.db.get_products_by_type('sellable')
        names = []
        for p in products:
            p_id, name, cat, price, p_type, size = p
            display_name = f"{name} ({size})"
            self.product_map[display_name] = (p_id, price)
            names.append(display_name)
        self.combo_product['values'] = names

    def update_price_label(self, event):
        """Live price calculation."""
        try:
            selected = self.combo_product.get()
            qty = int(self.ent_qty.get())
            unit_price = self.product_map[selected][1]
            total = qty * unit_price
            self.lbl_total.config(text=f"Total Price: {total:.2f} SAR")
        except:
            pass

    def save_sale(self):
        """Record the transaction with the provided date."""
        selected = self.combo_product.get()
        qty_str = self.ent_qty.get()
        manual_date = self.ent_date.get() # Get date from entry

        if not selected or not qty_str or not manual_date:
            messagebox.showwarning("Error", "All fields including date are required.")
            return

        try:
            # Basic date validation
            datetime.strptime(manual_date, "%Y-%m-%d")
            
            qty = int(qty_str)
            p_id, unit_price = self.product_map[selected]
            total_price = qty * unit_price
            
            # Query updated to include sale_date manually
            query = "INSERT INTO sales (product_id, quantity, total_price, sale_date) VALUES (?, ?, ?, ?)"
            self.db.execute_query(query, (p_id, qty, total_price, manual_date))
            
            messagebox.showinfo("Success", f"Sale saved for date: {manual_date}")
            
        except ValueError as e:
            messagebox.showerror("Error", "Invalid Input: Ensure Quantity is a number and Date is YYYY-MM-DD")

if __name__ == "__main__":
    app_root = tk.Tk()
    SalesWindow(app_root)
    app_root.mainloop()