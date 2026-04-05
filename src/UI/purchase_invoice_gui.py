import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.database.database_manager import DatabaseManager

class PurchaseInvoiceWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Smart Purchase Invoice")
        self.root.geometry("900x600")
        
        # Initialize database connection
        self.db = DatabaseManager()
        # Temporary list to store products before saving to database
        self.basket = []  
        
        # Build UI and load products from DB
        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        """Create and arrange all UI components for the Purchase Invoice."""
        
        # --- Top Frame: Supplier & Date Information ---
        top_frame = tk.LabelFrame(self.root, text="Purchase Header", padx=10, pady=10)
        top_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(top_frame, text="Supplier Name:").grid(row=0, column=0, sticky="w")
        self.ent_supplier = tk.Entry(top_frame, width=30)
        self.ent_supplier.grid(row=0, column=1, padx=10)

        tk.Label(top_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=2, padx=10)
        self.ent_date = tk.Entry(top_frame, width=15)
        # Set default date to today's date
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=0, column=3)

        # --- Middle Frame: Selection Area (Add Product to Basket) ---
        add_frame = tk.LabelFrame(self.root, text="Add Items to Stock", padx=10, pady=10)
        add_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(add_frame, text="Product:").grid(row=0, column=0)
        self.combo_product = ttk.Combobox(add_frame, state="readonly", width=25)
        self.combo_product.grid(row=0, column=1, padx=5)
        
        tk.Label(add_frame, text="Qty:").grid(row=0, column=2)
        self.ent_qty = tk.Entry(add_frame, width=10)
        self.ent_qty.grid(row=0, column=3, padx=5)

        tk.Label(add_frame, text="Cost Price:").grid(row=0, column=4)
        self.ent_cost = tk.Entry(add_frame, width=10)
        self.ent_cost.grid(row=0, column=5, padx=5)

        tk.Button(add_frame, text="Add to Basket", bg="#3498db", fg="white", 
                  font=("Arial", 9, "bold"), command=self.add_to_basket).grid(row=0, column=6, padx=15)

        # --- Bottom Frame: Treeview Table for Items ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "Product Name", "Qty", "Cost Price", "Subtotal")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)

        # --- Footer Section: Total and Actions ---
        footer_panel = tk.Frame(self.root, padx=20, pady=10)
        footer_panel.pack(fill="x")

        self.lbl_total = tk.Label(footer_panel, text="Total Cost: 0.00", 
                                 font=("Arial", 14, "bold"), fg="#e74c3c")
        self.lbl_total.pack(side="right")

        tk.Button(footer_panel, text="Confirm Purchase", bg="#c0392b", fg="white", 
                  font=("Arial", 12, "bold"), width=18,
                  command=self.save_purchase_invoice).pack(side="left", pady=10)

        tk.Button(footer_panel, text="Remove Selected", bg="#f39c12", fg="black",
                  font=("Arial", 10), width=15,
                  command=self.remove_from_basket).pack(side="left", padx=10)

    def load_initial_data(self):
        """Populate product list from database with dynamic text formatting."""
        # Load Products (Buyable or Both) sorted by name
        query = "SELECT product_id, name, unit_price, category, size FROM products WHERE product_type IN ('buyable', 'both') ORDER BY name ASC"
        products = self.db.fetch_data(query)

        self.product_map = {}
        display_list = []

        for p in products:
            p_id, name, price, cat, size = p
            display_text = f"{name}"

            # Only add Category/Size if they are not empty
            if cat and str(cat).strip():
                display_text += f" ({cat})"
            if size and str(size).strip():
                display_text += f" ({size})"

            # Map the display text to the actual product ID and price
            self.product_map[display_text] = (p_id, price)
            display_list.append(display_text)    

        self.combo_product['values'] = display_list
        self.combo_product.bind("<<ComboboxSelected>>", self.on_product_select)

    def on_product_select(self, event):
        """Auto-fill cost price field based on selected product."""
        p_name = self.combo_product.get()
        if p_name in self.product_map:
            default_cost = self.product_map[p_name][1]
            self.ent_cost.delete(0, tk.END)
            self.ent_cost.insert(0, str(default_cost))    

    def add_to_basket(self):
        """Add current entry fields to the temporary basket and treeview."""
        p_name = self.combo_product.get()
        qty_str = self.ent_qty.get()
        cost_str = self.ent_cost.get()

        if not p_name or not qty_str or not cost_str:
            messagebox.showwarning("Warning", "Please fill all fields.")
            return

        try:
            qty = int(qty_str)
            cost = float(cost_str)
            subtotal = qty * cost
            # Extract product ID from the map
            p_id = self.product_map[p_name][0]

            # Add to memory list
            self.basket.append({'id': p_id, 'name': p_name, 'qty': qty, 'cost': cost, 'subtotal': subtotal})
            # Add to visual table
            self.tree.insert("", "end", values=(p_id, p_name, qty, f"{cost:.2f}", f"{subtotal:.2f}"))
            
            self.update_total()
            
            # Reset input fields for the next entry
            self.ent_qty.delete(0, tk.END)
            self.ent_cost.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Quantity and Cost must be numeric.")

    def remove_from_basket(self):
        """Remove highlighted rows from both the basket list and UI table."""
        selected = self.tree.selection()
        if selected:
            for item in selected:
                idx = self.tree.index(item)
                del self.basket[idx]
                self.tree.delete(item)
            self.update_total()

    def update_total(self):
        """Calculate and display the sum of all items in the current basket."""
        total = sum(item['subtotal'] for item in self.basket)
        self.lbl_total.config(text=f"Total Cost: {total:.2f}")

    def save_purchase_invoice(self):
        """Finalize the purchase by saving the header and items to the database."""
        if not self.basket:
            messagebox.showwarning("Empty", "No items to save.")
            return
        
        supplier = self.ent_supplier.get() or "Unknown Supplier"
        date_str = self.ent_date.get()
        total_amount = sum(item['subtotal'] for item in self.basket)

        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
            
            # Step 1: Insert into purchase_invoices table (Header)
            query_h = "INSERT INTO purchase_invoices (supplier_name, purchase_date, total_amount) VALUES (?, ?, ?)"
            cursor = self.db.execute_query(query_h, (supplier, date_str, total_amount))
            p_invoice_id = cursor.lastrowid

            # Step 2: Insert each item into purchase_items table (Details)
            for item in self.basket:
                query_i = """INSERT INTO purchase_items (purchase_invoice_id, product_id, quantity, unit_cost_price, subtotal) 
                             VALUES (?, ?, ?, ?, ?)"""
                self.db.execute_query(query_i, (p_invoice_id, item['id'], item['qty'], item['cost'], item['subtotal']))

            messagebox.showinfo("Success", f"Purchase Invoice #{p_invoice_id} saved.")
            self.clear_all()
        except ValueError:
            messagebox.showerror("Date Error", "Use YYYY-MM-DD format.")

    def clear_all(self):
        """Reset the entire screen for a new invoice entry."""
        self.basket = []
        for i in self.tree.get_children(): self.tree.delete(i)
        self.ent_supplier.delete(0, tk.END)
        self.update_total()

if __name__ == "__main__":
    root = tk.Tk()
    app = PurchaseInvoiceWindow(root)
    root.mainloop()