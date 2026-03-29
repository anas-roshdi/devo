import tkinter as tk
from tkinter import messagebox
from database_manager import DatabaseManager

class DevoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Management System")
        self.root.geometry("600x400")
        
        # Initialize Database
        self.db = DatabaseManager()
        
        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        """Build the main dashboard buttons."""
        tk.Label(self.root, text="Devo Control Panel", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Dashboard Buttons
        tk.Button(self.root, text="Manage Products", width=25, command=self.open_products).pack(pady=10)
        tk.Button(self.root, text="Record Sale", width=25, bg="green", fg="white").pack(pady=10)
        tk.Button(self.root, text="Record Purchase", width=25, bg="orange").pack(pady=10)
        tk.Button(self.root, text="View Reports", width=25).pack(pady=10)

    def open_products(self):
        messagebox.showinfo("System", "Product Management Window coming soon!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DevoApp(root)
    root.mainloop()