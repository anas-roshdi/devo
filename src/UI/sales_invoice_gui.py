import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.database.database_manager import DatabaseManager

class SalesInvoiceWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Smart Sales Invoice")
        self.root.geometry("900x600")
        
        # Initialize database connection
        self.db = DatabaseManager()
        # Temporary list to hold invoice items before database commit
        self.basket = [] 
        
        # Setup UI and load initial data (Customers/Products)
        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        """Create and arrange all UI components for the Sales Invoice."""
        
        # --- Top Frame: Customer & Invoice Info ---
        top_frame = tk.LabelFrame(self.root, text="Invoice Header", padx=10, pady=10)
        top_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(top_frame, text="Select Shop/Customer:").grid(row=0, column=0, sticky="w")
        self.combo_customer = ttk.Combobox(top_frame, state="readonly", width=30)
        self.combo_customer.grid(row=0, column=1, padx=10)

        tk.Label(top_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=2, padx=10)
        self.ent_date = tk.Entry(top_frame, width=15)
        # Set default date to the current date automatically
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d")) 
        self.ent_date.grid(row=0, column=3)

        # --- Middle Frame: Selection Area (Add Product to Basket) ---
        add_frame = tk.LabelFrame(self.root, text="Add Product", padx=10, pady=10)
        add_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(add_frame, text="Product:").grid(row=0, column=0)
        self.combo_product = ttk.Combobox(add_frame, state="readonly", width=25)
        self.combo_product.grid(row=0, column=1, padx=5)
        
        tk.Label(add_frame, text="Qty:").grid(row=0, column=2)
        self.ent_qty = tk.Entry(add_frame, width=10)
        self.ent_qty.grid(row=0, column=3, padx=5)

        tk.Label(add_frame, text="Unit Price:").grid(row=0, column=4)
        self.ent_price = tk.Entry(add_frame, width=10)
        self.ent_price.grid(row=0, column=5, padx=5)

        tk.Button(add_frame, text="Add to Basket", bg="blue", fg="white", 
                  command=self.add_to_basket).grid(row=0, column=6, padx=15)

        # --- Bottom Frame: Treeview Table for Invoice Items ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "Product Name", "Qty", "Unit Price", "Subtotal")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)

        # --- Footer Section: Total Display and Action Buttons ---
        side_panel = tk.Frame(self.root, padx=20, pady=10)
        side_panel.pack(fill="x")

        self.lbl_total = tk.Label(side_panel, text="Total: 0.00", font=("Arial", 16, "bold"), fg="darkgreen")
        self.lbl_total.pack(side="right")

        tk.Button(side_panel, text="Confirm & Save Invoice", bg="green", fg="white", font=("Arial", 12, "bold"),
                  command=self.save_invoice).pack(side="left", pady=10)
        
        tk.Button(side_panel, text="Remove Selected", bg="red", fg="white",
                  command=self.remove_from_basket).pack(side="left", padx=10)

    def load_initial_data(self):
        """Fetch and populate customers and products into the dropdowns."""
        # Load Customers
        customers = self.db.get_all_customers()
        self.customer_map = {c[1]: c[0] for c in customers} # Map Name to Customer ID
        self.combo_customer['values'] = list(self.customer_map.keys())
        self.combo_customer.set("General Customer")

        # Load Products (Sellable or Both) sorted by name
        query = "SELECT product_id, name, unit_price, category, size FROM products WHERE product_type IN ('sellable', 'both') ORDER BY name ASC"
        products = self.db.fetch_data(query)

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
        self.combo_product.bind("<<ComboboxSelected>>", self.on_product_select)
        self.combo_customer.bind("<<ComboboxSelected>>", self.on_product_select)

    def on_product_select(self, event):
        """
        Automatically pre-fill the price field. 
        If it's a shop (not General Customer), fetch the last sold price for this product.
        """
        p_name = self.combo_product.get()
        customer_name = self.combo_customer.get()
        
        if p_name not in self.product_map:
            return

        # 1. Get the base price from the product map (default price)
        default_price = self.product_map[p_name][1]
        p_id = self.product_map[p_name][0]
        final_price = default_price

        # 2. Check if the customer is a specific shop/customer (not general)
        if customer_name != "General Customer":
            customer_id = self.customer_map.get(customer_name)
            
            # Query to fetch the most recent selling price for this specific customer and product
            query = """
                SELECT si.unit_price_sold 
                FROM sale_items si
                JOIN sale_invoices s ON si.invoice_id = s.invoice_id
                WHERE s.customer_id = ? AND si.product_id = ?
                ORDER BY s.sale_date DESC, s.invoice_id DESC
                LIMIT 1
            """
            last_sale = self.db.fetch_data(query, (customer_id, p_id))

            if last_sale:
                # Use the historical price if found in the database
                final_price = last_sale[0][0]

        # 3. Populate the price entry field (remains editable for the user)
        self.ent_price.delete(0, tk.END)
        self.ent_price.insert(0, str(final_price))

    def add_to_basket(self):
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
            # Get product ID from our map
            p_id = self.product_map[p_name][0]

            # Add to memory list
            self.basket.append({'id': p_id, 'name': p_name, 'qty': qty, 'price': price, 'subtotal': subtotal})
            # Add to visual table
            self.tree.insert("", "end", values=(p_id, p_name, qty, f"{price:.2f}", f"{subtotal:.2f}"))
            
            self.update_total()
            # Reset Qty field for the next item
            self.ent_qty.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Quantity and Price must be numeric.")

    def update_total(self):
        """Sum the subtotals of all items currently in the basket."""
        total = sum(item['subtotal'] for item in self.basket)
        self.lbl_total.config(text=f"Total: {total:.2f}")

    def remove_from_basket(self):
        """Delete selected rows from both the internal list and the table UI."""
        selected = self.tree.selection()
        if selected:
            for item in selected:
                # Find index in tree to remove corresponding index from basket
                idx = self.tree.index(item)
                del self.basket[idx]
                self.tree.delete(item)
            self.update_total()

    def save_invoice(self):
        """Save the full invoice (Header and Details) to the database."""
        if not self.basket:
            messagebox.showwarning("Empty", "No items in the basket.")
            return

        customer_name = self.combo_customer.get()
        customer_id = self.customer_map[customer_name]
        total_amount = sum(item['subtotal'] for item in self.basket)
        date_str = self.ent_date.get()

        try:
            # Validate the date format
            datetime.strptime(date_str, "%Y-%m-%d")
            
            # Step 1: Save the Invoice Header (Customer, Date, Total)
            query_h = "INSERT INTO sale_invoices (customer_id, sale_date, total_amount) VALUES (?, ?, ?)"
            cursor = self.db.execute_query(query_h, (customer_id, date_str, total_amount))
            invoice_id = cursor.lastrowid # Retrieve generated Primary Key

            # Step 2: Save each individual item (Details)
            for item in self.basket:
                query_i = """INSERT INTO sale_items (invoice_id, product_id, quantity, unit_price_sold, subtotal) 
                             VALUES (?, ?, ?, ?, ?)"""
                self.db.execute_query(query_i, (invoice_id, item['id'], item['qty'], item['price'], item['subtotal']))

            messagebox.showinfo("Success", f"Invoice #{invoice_id} saved successfully for {customer_name}.")
            self.clear_invoice()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save: {e}")

    def clear_invoice(self):
        """Reset the UI and memory list to prepare for a new invoice."""
        self.basket = []
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.update_total()
        self.combo_product.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = SalesInvoiceWindow(root)
    root.mainloop()