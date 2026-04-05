import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd # Library required for Excel file generation
from src.database.database_manager import DatabaseManager

class ReportsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Financial Analytics & Export")
        self.root.geometry("850x650")
        
        # Initialize database manager instance
        self.db = DatabaseManager()
        # List to hold the currently generated report data for Excel export
        self.current_report_data = [] 
        
        # Initialize UI and load initial filtering data
        self.create_widgets()
        self.load_filters()

    def create_widgets(self):
        """Create and arrange all UI components including filters, cards, and tables."""
        
        # --- Top Frame: Filters (Date Range & Customer Selection) ---
        filter_frame = tk.LabelFrame(self.root, text="Report Filters", padx=10, pady=10)
        filter_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(filter_frame, text="Shop:").grid(row=0, column=0)
        self.combo_customer = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.combo_customer.grid(row=0, column=1, padx=5)

        tk.Label(filter_frame, text="From:").grid(row=0, column=2)
        self.ent_from = tk.Entry(filter_frame, width=10)
        self.ent_from.insert(0, "2026-01-01") # Default start date for the current year
        self.ent_from.grid(row=0, column=3)

        tk.Label(filter_frame, text="To:").grid(row=0, column=4)
        self.ent_to = tk.Entry(filter_frame, width=10)
        self.ent_to.insert(0, "2026-12-31") # Default end date for the current year
        self.ent_to.grid(row=0, column=5)

        # Action Button: Fetch and process data
        tk.Button(filter_frame, text="Generate", bg="#2980b9", fg="white", 
                  command=self.generate_report).grid(row=0, column=6, padx=5)

        # Action Button: Save current results to a .xlsx file
        tk.Button(filter_frame, text="Export to Excel", bg="#27ae60", fg="white", 
                  command=self.export_to_excel).grid(row=0, column=7, padx=5)

        # --- Middle Frame: Summary Cards (Quick Financial Overview) ---
        summary_frame = tk.Frame(self.root)
        summary_frame.pack(fill="x", padx=20, pady=10)

        self.card_sales = tk.Label(summary_frame, text="Total Sales\n0.00", bg="#2ecc71", fg="white", font=("Arial", 11, "bold"), width=22, height=3)
        self.card_sales.pack(side="left", padx=5)

        self.card_purchases = tk.Label(summary_frame, text="Total Purchases\n0.00", bg="#e74c3c", fg="white", font=("Arial", 11, "bold"), width=22, height=3)
        self.card_purchases.pack(side="left", padx=5)

        self.card_profit = tk.Label(summary_frame, text="Net Profit\n0.00", bg="#f1c40f", fg="black", font=("Arial", 11, "bold"), width=22, height=3)
        self.card_profit.pack(side="left", padx=5)

        # --- Bottom Frame: Treeview Table for Detailed Record Display ---
        self.tree = ttk.Treeview(self.root, columns=("Date", "Type", "Entity", "Amount"), show="headings")
        for col in ("Date", "Type", "Entity", "Amount"):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def generate_report(self):
        """Fetch sales and purchases from DB and calculate financial totals."""
        customer = self.combo_customer.get()
        start = self.ent_from.get()
        end = self.ent_to.get()

        # Step 1: Fetch Sales Invoices based on date and customer filter
        s_query = "SELECT sale_date, 'SALE', customers.name, total_amount FROM sale_invoices JOIN customers ON sale_invoices.customer_id = customers.customer_id WHERE sale_date BETWEEN ? AND ?"
        s_params = [start, end]
        if customer != "All Customers":
            s_query += " AND customers.name = ?"
            s_params.append(customer)
        
        sales = self.db.fetch_data(s_query, tuple(s_params))
        
        # Step 2: Fetch Purchase Invoices within the date range
        purchases = self.db.fetch_data("SELECT purchase_date, 'PURCHASE', supplier_name, total_amount FROM purchase_invoices WHERE purchase_date BETWEEN ? AND ?", (start, end))

        # Merge both datasets for display and export
        self.current_report_data = sales + purchases 
        
        # Clear existing table rows before inserting new data
        for i in self.tree.get_children(): self.tree.delete(i)
        for row in self.current_report_data: self.tree.insert("", "end", values=row)
        
        # Step 3: Calculate totals and update the visual summary cards
        ts = sum(s[3] for s in sales)
        tp = sum(p[3] for p in purchases) 
        self.card_sales.config(text=f"Total Sales\n{ts:.2f}")
        self.card_purchases.config(text=f"Total Purchases\n{tp:.2f}")
        self.card_profit.config(text=f"Net Profit\n{(ts - tp):.2f}")

    def export_to_excel(self):
        """Convert current report list into a DataFrame and export to Excel (.xlsx)."""
        if not self.current_report_data:
            messagebox.showwarning("No Data", "Please generate a report first before exporting.")
            return

        # Open file dialog for the user to choose save location
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                                filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                # Convert the data list to a pandas DataFrame with specified column headers
                df = pd.DataFrame(self.current_report_data, columns=["Date", "Type", "Client/Supplier", "Amount"])
                
                # Perform the export to Excel
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Export Success", f"Report successfully saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not save file: {e}")

    def load_filters(self):
        """Load available customer names into the dropdown filter."""
        customers = self.db.get_all_customers()
        self.combo_customer['values'] = ["All Customers"] + [c[1] for c in customers]
        self.combo_customer.set("All Customers")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReportsWindow(root)
    root.mainloop()