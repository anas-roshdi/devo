import tkinter as tk
from tkinter import messagebox

# Import the windows we created earlier
from product_gui import ProductWindow
from sales_gui import SalesWindow
from purchases_gui import PurchasesWindow
from reports_gui import ReportsWindow
from manage_products_gui import ManageProductsWindow

class DevoDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Business Management System")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f2f5") # Professional light gray background

        self.create_widgets()

    def create_widgets(self):
        """Create the central navigation hub."""
        # Header Section
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=100)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="DEVO DASHBOARD", font=("Helvetica", 24, "bold"), 
                 bg="#2c3e50", fg="white").pack(pady=30)

        # Button Container
        menu_frame = tk.Frame(self.root, bg="#f0f2f5")
        menu_frame.pack(pady=40)

        # Define buttons with their respective styles and commands
        buttons = [
            ("Add New Product", "blue", self.open_add_product),
            ("Manage Inventory", "blue", self.open_manage_inventory),
            ("Record Sale", "green", self.open_sales),
            ("Record Purchase", "orange", self.open_purchases),
            ("Financial Reports", "purple", self.open_reports)
        ]

        for text, color, cmd in buttons:
            btn = tk.Button(menu_frame, text=text, bg=color, fg="white", 
                            font=("Arial", 11, "bold"), width=25, height=2, 
                            relief="flat", command=cmd)
            btn.pack(pady=10)

        # Footer
        tk.Label(self.root, text="System Version 1.0 - Ready", bg="#f0f2f5", 
                 fg="gray", font=("Arial", 9)).pack(side="bottom", pady=10)

    # --- Navigation Functions ---
    def open_add_product(self):
        new_win = tk.Toplevel(self.root)
        ProductWindow(new_win)

    def open_manage_inventory(self):
        new_win = tk.Toplevel(self.root)
        ManageProductsWindow(new_win)

    def open_sales(self):
        new_win = tk.Toplevel(self.root)
        SalesWindow(new_win)

    def open_purchases(self):
        new_win = tk.Toplevel(self.root)
        PurchasesWindow(new_win)

    def open_reports(self):
        new_win = tk.Toplevel(self.root)
        ReportsWindow(new_win)

if __name__ == "__main__":
    app_root = tk.Tk()
    DevoDashboard(app_root)
    app_root.mainloop()