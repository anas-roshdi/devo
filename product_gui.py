import tkinter as tk
from tkinter import ttk, messagebox
from database_manager import DatabaseManager

class ProductWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Product Management")
        self.root.geometry("600x400")
        
        # Connect to DB
        self.db = DatabaseManager()

        # --- UI Labels and Entries ---
        tk.Label(root, text="Product Name:").grid(row=0, column=0, padx=10, pady=10)
        self.ent_name = tk.Entry(root)
        self.ent_name.grid(row=0, column=1)

        tk.Label(root, text="Category:").grid(row=1, column=0, padx=10, pady=10)
        self.ent_cat = tk.Entry(root)
        self.ent_cat.grid(row=1, column=1)

        tk.Label(root, text="Sale Price:").grid(row=2, column=0, padx=10, pady=10)
        self.ent_price = tk.Entry(root)
        self.ent_price.grid(row=2, column=1)

        # Dropdown Menu for Product Type (Using ttk.Combobox)
        tk.Label(root, text="Type:").grid(row=3, column=0, padx=10, pady=10)
        self.combo_type = ttk.Combobox(root, values=["sellable", "buyable", "both"])
        self.combo_type.grid(row=3, column=1)
        self.combo_type.current(0) # Default to 'sellable'

        tk.Label(root, text="Size:").grid(row=4, column=0, padx=10, pady=10)
        self.ent_size = tk.Entry(root)
        self.ent_size.grid(row=4, column=1)

        # Submit Button
        tk.Button(root, text="Add Product", command=self.submit_data, bg="blue", fg="white").grid(row=5, column=0, columnspan=2, pady=20)

    def submit_data(self):
        """Extract data from GUI and save to Database."""
        name = self.ent_name.get()
        cat = self.ent_cat.get()
        price = self.ent_price.get()
        p_type = self.combo_type.get()
        size = self.ent_size.get()

        if name and price:
            try:
                self.db.add_product(name, cat, float(price), p_type, size)
                messagebox.showinfo("Success", f"Product '{name}' added successfully!")
                self.clear_fields()
            except ValueError:
                messagebox.showerror("Error", "Price must be a number!")
        else:
            messagebox.showwarning("Input Error", "Name and Price are required!")

    def clear_fields(self):
        """Reset all input fields."""
        self.ent_name.delete(0, tk.END)
        self.ent_cat.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_size.delete(0, tk.END)

if __name__ == "__main__":
    app_root = tk.Tk()
    ProductWindow(app_root)
    app_root.mainloop()