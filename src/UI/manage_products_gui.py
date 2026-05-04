"""
Product Management Window.
============================
Full CRUD operations for managing product inventory.
All database operations go through DatabaseManager methods.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from src.database.database_manager import DatabaseManager
from config import Colors, Fonts, WindowConfig, PRODUCT_TYPES, DEFAULT_PRODUCT_TYPE_INDEX


class ManageProductsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Unified Product Management")
        
        geo, min_w, min_h = WindowConfig.PRODUCTS
        self.root.geometry(geo)
        self.root.minsize(min_w, min_h)
        
        # Initialize database connection instance
        self.db = DatabaseManager()
        
        # Build the user interface and populate the table with data
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        """Build and arrange all UI components for product management."""
        
        # --- Main Title Section ---
        tk.Label(self.root, text="Product Inventory System", 
                 font=Fonts.HEADER_MEDIUM, fg=Colors.PRIMARY_DARK).pack(pady=15)

        # --- Top Section: Input/Edit Form Frame ---
        form_frame = tk.LabelFrame(self.root, text=" Product Information (Add / Edit) ", 
                                   padx=15, pady=15, font=Fonts.LABEL_FRAME)
        form_frame.pack(padx=20, pady=10, fill="x")

        # Row 0: ID (ReadOnly) and Name Entry
        tk.Label(form_frame, text="Product ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, state="readonly", fg=Colors.TEXT_BLUE, width=10)
        self.ent_id.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(form_frame, text="Name:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_name = tk.Entry(form_frame, width=30)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)

        # Row 1: Category and Unit Price Entries
        tk.Label(form_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_cat = tk.Entry(form_frame, width=20)
        self.ent_cat.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Unit Price:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_price = tk.Entry(form_frame, width=20)
        self.ent_price.grid(row=1, column=3, padx=5, pady=5)

        # Row 2: Product Type (Combo) and Size Entry
        tk.Label(form_frame, text="Type:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.combo_type = ttk.Combobox(form_frame, values=PRODUCT_TYPES, state="readonly", width=18)
        self.combo_type.grid(row=2, column=1, padx=5, pady=5)
        self.combo_type.current(DEFAULT_PRODUCT_TYPE_INDEX)

        tk.Label(form_frame, text="Size:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.ent_size = tk.Entry(form_frame, width=20)
        self.ent_size.grid(row=2, column=3, padx=5, pady=5)

        # --- Buttons Frame: Action Controls ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        # Button to add a new record
        tk.Button(btn_frame, text="➕ Add New Product", bg=Colors.GREEN_DARK, fg=Colors.TEXT_WHITE,
                  width=18, font=Fonts.BTN_MEDIUM, command=self.add_product).pack(side="left", padx=10)
        
        # Button to update existing record details
        tk.Button(btn_frame, text="💾 Update Selected", bg=Colors.BLUE_DARK, fg=Colors.TEXT_WHITE,
                  width=18, font=Fonts.BTN_MEDIUM, command=self.update_product).pack(side="left", padx=10)
        
        # Button to delete a record permanently
        tk.Button(btn_frame, text="🗑️ Delete Product", bg=Colors.RED_DARK, fg=Colors.TEXT_WHITE,
                  width=18, font=Fonts.BTN_MEDIUM, command=self.delete_product).pack(side="left", padx=10)
        
        # Button to clear all entry fields
        tk.Button(btn_frame, text="🧹 Clear Fields", bg=Colors.GRAY, fg=Colors.TEXT_WHITE,
                  width=18, font=Fonts.BTN_MEDIUM, command=self.clear_fields).pack(side="left", padx=10)

        # --- Bottom Section: Table View ---
        tk.Label(self.root, text="Current Inventory List", font=Fonts.BODY_ITALIC).pack(pady=(10, 0))

        table_frame = tk.Frame(self.root)
        table_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Define table columns
        columns = ("ID", "Name", "Category", "Price", "Type", "Size")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Set table headers and column alignment
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
            
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Add a scrollbar for navigating through products
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Bind table selection event to populate the form above
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    # --- Logic & Database Integration Methods ---

    def load_data(self):
        """Fetch all products from database and refresh the table display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        products = self.db.get_all_products()
        for p in products:
            self.tree.insert("", tk.END, values=p)

    def add_product(self):
        """Insert a new product record into the database."""
        name = self.ent_name.get()
        price = self.ent_price.get()
        
        # Validate required fields
        if not name or not price:
            messagebox.showwarning("Input Error", "Name and Price are required to add a new product!")
            return
        
        try:
            self.db.add_product(name, self.ent_cat.get(), float(price), self.combo_type.get(), self.ent_size.get())
            messagebox.showinfo("Success", f"Product '{name}' added successfully!")
            self.load_data()
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("Error", f"Could not add product: {e}")

    def update_product(self):
        """Update the selected product's information in the database."""
        p_id = self.ent_id.get()
        if not p_id:
            messagebox.showwarning("Selection", "Please select a product from the table to update!")
            return

        try:
            self.db.update_product(
                p_id, self.ent_name.get(), self.ent_cat.get(), 
                float(self.ent_price.get()), self.combo_type.get(), self.ent_size.get()
            )
            messagebox.showinfo("Success", "Product updated successfully!")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    def delete_product(self):
        """Permanently remove the selected product from the database."""
        p_id = self.ent_id.get()
        if not p_id: return
        
        if messagebox.askyesno("Confirm", "Delete this product permanently?"):
            self.db.delete_product(p_id)
            self.load_data()
            self.clear_fields()

    def on_row_select(self, event):
        """Fill input fields with details of the selected row in the table."""
        selected = self.tree.focus()
        if not selected: return
        
        values = self.tree.item(selected, 'values')
        
        # Populate ID (must temporarily enable to modify)
        self.ent_id.config(state="normal")
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, values[0])
        self.ent_id.config(state="readonly")

        # Populate other text fields
        self.ent_name.delete(0, tk.END); self.ent_name.insert(0, values[1])
        self.ent_cat.delete(0, tk.END); self.ent_cat.insert(0, values[2])
        self.ent_price.delete(0, tk.END); self.ent_price.insert(0, values[3])
        self.combo_type.set(values[4])
        self.ent_size.delete(0, tk.END); self.ent_size.insert(0, values[5])

    def clear_fields(self):
        """Reset all form fields to their default empty/initial state."""
        self.ent_id.config(state="normal")
        self.ent_id.delete(0, tk.END)
        self.ent_id.config(state="readonly")
        
        self.ent_name.delete(0, tk.END)
        self.ent_cat.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_size.delete(0, tk.END)
        self.combo_type.current(DEFAULT_PRODUCT_TYPE_INDEX)

if __name__ == "__main__":
    app_root = tk.Tk()
    ManageProductsWindow(app_root)
    app_root.mainloop()