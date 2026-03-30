import tkinter as tk
from tkinter import ttk, messagebox
from database_manager import DatabaseManager

class ManageProductsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Full Product Management")
        self.root.geometry("900x700")
        
        # Initialize Database connection
        self.db = DatabaseManager()
        
        # UI Setup
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        """Build the complete UI with table and editing form."""
        tk.Label(self.root, text="Product Inventory Control", font=("Arial", 18, "bold")).pack(pady=10)

        # --- Table Section (Treeview) ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(padx=20, pady=10, fill="both", expand=True)

        columns = ("ID", "Name", "Category", "Price", "Type", "Size")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Setup table headers
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
            
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Add a scrollbar for the table
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # --- Edit Form Section ---
        edit_frame = tk.LabelFrame(self.root, text="Edit Product Details", padx=15, pady=15)
        edit_frame.pack(padx=20, pady=20, fill="x")

        # Row 0: ID (Read-only) and Name
        tk.Label(edit_frame, text="Product ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(edit_frame, state="readonly", fg="blue")
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(edit_frame, text="Name:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_name = tk.Entry(edit_frame)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)

        # Row 1: Category and Price
        tk.Label(edit_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_cat = tk.Entry(edit_frame)
        self.ent_cat.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(edit_frame, text="Unit Price:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_price = tk.Entry(edit_frame)
        self.ent_price.grid(row=1, column=3, padx=5, pady=5)

        # Row 2: Type and Size
        tk.Label(edit_frame, text="Type:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.combo_type = ttk.Combobox(edit_frame, values=["sellable", "buyable", "both"], state="readonly")
        self.combo_type.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(edit_frame, text="Size:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.ent_size = tk.Entry(edit_frame)
        self.ent_size.grid(row=2, column=3, padx=5, pady=5)

        # --- Action Buttons ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Update/Save Changes", bg="blue", fg="white", 
                  width=25, font=("Arial", 10, "bold"), command=self.update_product).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="Delete Product", bg="red", fg="white", 
                  width=25, font=("Arial", 10, "bold"), command=self.delete_product).pack(side="left", padx=10)

    def load_data(self):
        """Fetch all products from DB and refresh the table."""
        # Clear current table content
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Fetch data using the method from Task 4
        products = self.db.get_all_products()
        for p in products:
            self.tree.insert("", tk.END, values=p)

    def on_row_select(self, event):
        """Populate all entry fields when a user clicks a table row."""
        selected_item = self.tree.focus()
        if not selected_item: return
        
        v = self.tree.item(selected_item, 'values')
        
        # ID Field update (Handling Readonly state)
        self.ent_id.config(state="normal")
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, v[0])
        self.ent_id.config(state="readonly")

        # Other fields
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, v[1])
        
        self.ent_cat.delete(0, tk.END)
        self.ent_cat.insert(0, v[2])
        
        self.ent_price.delete(0, tk.END)
        self.ent_price.insert(0, v[3])
        
        self.combo_type.set(v[4])
        
        self.ent_size.delete(0, tk.END)
        self.ent_size.insert(0, v[5])

    def update_product(self):
        """Apply changes to the selected product in the database."""
        p_id = self.ent_id.get()
        if not p_id:
            messagebox.showwarning("Selection", "Please select a product from the table first!")
            return

        try:
            query = """
                UPDATE products 
                SET name = ?, category = ?, unit_price = ?, product_type = ?, size = ? 
                WHERE product_id = ?
            """
            params = (
                self.ent_name.get(),
                self.ent_cat.get(),
                float(self.ent_price.get()),
                self.combo_type.get(),
                self.ent_size.get(),
                p_id
            )
            self.db.execute_query(query, params)
            messagebox.showinfo("Success", f"Product ID {p_id} updated successfully!")
            self.load_data() # Refresh table
        except ValueError:
            messagebox.showerror("Error", "Price must be a valid numeric value.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update: {e}")

    def delete_product(self):
        """Permanently remove the selected product."""
        p_id = self.ent_id.get()
        if not p_id:
            messagebox.showwarning("Selection", "Please select a product to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Product ID {p_id}?")
        if confirm:
            try:
                self.db.execute_query("DELETE FROM products WHERE product_id = ?", (p_id,))
                messagebox.showinfo("Deleted", "Product has been removed.")
                self.load_data()
                self.clear_fields()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete: {e}")

    def clear_fields(self):
        """Reset the entry form."""
        self.ent_id.config(state="normal")
        self.ent_id.delete(0, tk.END)
        self.ent_id.config(state="readonly")
        self.ent_name.delete(0, tk.END)
        self.ent_cat.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_size.delete(0, tk.END)

if __name__ == "__main__":
    app_root = tk.Tk()
    ManageProductsWindow(app_root)
    app_root.mainloop()