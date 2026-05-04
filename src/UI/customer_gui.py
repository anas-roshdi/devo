"""
Customer & Shop Management Window.
====================================
CRUD operations for managing customers and shops.
All database operations go through DatabaseManager methods.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from src.database.database_manager import DatabaseManager
from config import Colors, Fonts, WindowConfig, DEFAULT_CUSTOMER


class CustomerWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Customer & Shop Management")
        
        geo, min_w, min_h = WindowConfig.CUSTOMERS
        self.root.geometry(geo)
        self.root.minsize(min_w, min_h)
        
        # Initialize database manager instance
        self.db = DatabaseManager()
        
        # Initialize the UI components and load current data
        self.create_widgets()
        self.load_customers()

    def create_widgets(self):
        """Setup UI layout including entry forms and the customer table."""
        
        # --- Main container using PanedWindow for responsive layout ---
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Left Side: Input Form Frame ---
        form_frame = tk.LabelFrame(paned, text="Customer Information", padx=10, pady=10)
        paned.add(form_frame, minsize=220)

        tk.Label(form_frame, text="Shop/Customer Name:").pack(anchor="w")
        self.ent_name = tk.Entry(form_frame)
        self.ent_name.pack(fill="x", pady=5)

        tk.Label(form_frame, text="Phone Number:").pack(anchor="w")
        self.ent_phone = tk.Entry(form_frame)
        self.ent_phone.pack(fill="x", pady=5)

        tk.Label(form_frame, text="Address/Location:").pack(anchor="w")
        self.ent_address = tk.Entry(form_frame)
        self.ent_address.pack(fill="x", pady=5)

        # Action Buttons for CRUD operations
        tk.Button(form_frame, text="Add Customer", bg=Colors.GREEN_DARK, fg=Colors.TEXT_WHITE,
                  command=self.add_customer).pack(fill="x", pady=10)
        
        tk.Button(form_frame, text="Update Selected", bg=Colors.ORANGE,
                  command=self.update_customer).pack(fill="x", pady=5)
        
        tk.Button(form_frame, text="Delete Customer", bg=Colors.RED, fg=Colors.TEXT_WHITE,
                  command=self.delete_customer).pack(fill="x", pady=5)

        # --- Right Side: Customer Data Table (Treeview) ---
        table_frame = tk.Frame(paned)
        paned.add(table_frame, minsize=300)

        columns = ("ID", "Name", "Phone", "Address")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configure table headers and column widths
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Bind table selection event to form population logic
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_customers(self):
        """Retrieve all customers from the DB and refresh the Treeview."""
        # Clear existing rows in the table
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # Fetch data from customers table
        customers = self.db.get_all_customers()
        for c in customers:
            # c typically expected as: (id, name, phone, address, created_at)
            self.tree.insert("", "end", values=(c[0], c[1], c[2], c[3]))

    def add_customer(self):
        """Insert a new customer record into the database."""
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        address = self.ent_address.get().strip()

        if name:
            try:
                self.db.add_customer(name, phone, address)
                messagebox.showinfo("Success", f"Customer '{name}' added successfully.")
                self.clear_fields()
                self.load_customers()
            except Exception as e:
                messagebox.showerror("Error", f"Could not add customer: {e}")
        else:
            messagebox.showwarning("Warning", "Customer name is required.")

    def on_select(self, event):
        """Auto-fill entry fields when a row is selected in the table."""
        selected = self.tree.focus()
        if selected:
            values = self.tree.item(selected, "values")
            # Populate form with selected row values
            self.ent_name.delete(0, tk.END)
            self.ent_name.insert(0, values[1])
            self.ent_phone.delete(0, tk.END)
            self.ent_phone.insert(0, values[2])
            self.ent_address.delete(0, tk.END)
            self.ent_address.insert(0, values[3])

    def update_customer(self):
        """Apply changes from the entry fields to the selected customer record."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a customer from the table to update.")
            return

        c_id = self.tree.item(selected, "values")[0]
        try:
            self.db.update_customer(c_id, self.ent_name.get(), self.ent_phone.get(), self.ent_address.get())
            messagebox.showinfo("Updated", "Customer information has been updated.")
            self.load_customers()
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    def delete_customer(self):
        """Remove the selected customer from the database after confirmation."""
        selected = self.tree.focus()
        if not selected: return
        
        values = self.tree.item(selected, "values")
        c_id = values[0]
        name = values[1]
        
        # Safeguard: Prevent deletion of the default 'General Customer'
        if name == DEFAULT_CUSTOMER:
            messagebox.showerror("Error", f"The default '{DEFAULT_CUSTOMER}' record cannot be deleted.")
            return

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{name}'?"):
            try:
                self.db.delete_customer(c_id)
                self.load_customers()
                self.clear_fields()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete record: {e}")

    def clear_fields(self):
        """Reset all form entries to empty."""
        self.ent_name.delete(0, tk.END)
        self.ent_phone.delete(0, tk.END)
        self.ent_address.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = CustomerWindow(root)
    root.mainloop()