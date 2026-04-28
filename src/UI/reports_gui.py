import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from src.database.database_manager import DatabaseManager
from src.utils.widgets import CalendarHelper
from src.utils.analytics import AnalyticsManager
import matplotlib.pyplot as plt
import time


class ReportsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Financial Analytics & Export")
        self.root.geometry("850x650")
        
        # Initialize database manager instance
        self.db = DatabaseManager()
        # List to hold the currently generated report data for Excel export
        self.current_report_data = [] 

        self.last_search_start = None
        self.last_search_end = None
        
        # Initialize UI and load initial filtering data
        self.create_widgets()
        self.load_filters()

    def create_widgets(self):
        """Create and arrange all UI components including filters, cards, and tables."""
        
        # --- Top Frame: Filters (Date Range & Customer Selection) ---
        filter_frame = tk.LabelFrame(self.root, text="Report Filters", padx=10, pady=10)
        filter_frame.pack(fill="x", padx=20, pady=10)

        # Create two separate containers (rows) inside the main filter frame
        row1 = tk.Frame(filter_frame)
        row1.pack(fill="x", pady=5)
        
        row2 = tk.Frame(filter_frame)
        row2.pack(fill="x", pady=5)

        tk.Label(row1, text="Shop:").grid(row=0, column=0)
        self.combo_customer = ttk.Combobox(row1, state="readonly", width=20)
        self.combo_customer.grid(row=0, column=1, padx=5)
        
        # Get the current year dynamically
        current_year = datetime.now().year

        tk.Label(row1, text="From:").grid(row=0, column=2)

        self.ent_from = tk.Entry(row1, width=10)
        # Set default to January 1st of the current year
        self.ent_from.insert(0, f"{current_year}-01-01") 
        self.ent_from.grid(row=0, column=3)

        # Button to trigger the calendar popup
        # Use a symbol like '📅' or text like 'Date'
        self.btn_from_cal = tk.Button(row1, text="📅", command=lambda: CalendarHelper.show_calendar(self.root, self.ent_from))
        self.btn_from_cal.grid(row=0, column=4, padx=5)

        tk.Label(row1, text="To:").grid(row=0, column=5)
        self.ent_to = tk.Entry(row1, width=10)
        # Set default to December 31st of the current year
        self.ent_to.insert(0, f"{current_year}-12-31") 
        self.ent_to.grid(row=0, column=6)

        # Button to trigger the calendar popup
        # Use a symbol like '📅' or text like 'Date'
        self.btn_to_cal = tk.Button(row1, text="📅", command=lambda: CalendarHelper.show_calendar(self.root, self.ent_to))
        self.btn_to_cal.grid(row=0, column=7, padx=5)

        # Action Button: Fetch and process data
        tk.Button(row1, text="Generate", bg="#2980b9", fg="white", command=self.generate_report).grid(row=0, column=8, padx=5)

        # Action Button: Save current results to a .xlsx file
        tk.Button(row1, text="Export to Excel", bg="#27ae60", fg="white", command=self.export_to_excel).grid(row=0, column=9, padx=5)
        
        # --- Chart Selection ---
        tk.Label(row2, text="Analysis:").grid(row=0, column=0, pady=5)
        self.combo_chart = ttk.Combobox(row2, state="readonly", width=18)
        self.combo_chart['values'] = ("Profit Margin", "Sales Trend", "Top Customers")
        self.combo_chart.set("Profit Margin")
        self.combo_chart.grid(row=0, column=1, padx=5)

        # --- Grouping Selection ---
        tk.Label(row2, text="Group By:").grid(row=0, column=2)
        self.combo_group = ttk.Combobox(row2, state="readonly", width=10)
        self.combo_group['values'] = ("Weekly", "Monthly")
        self.combo_group.set("Weekly")
        self.combo_group.grid(row=0, column=3, padx=5)

        # Update the button to call a 'router' function
        tk.Button(row2, text="Show Analytics", bg="#8e44ad", fg="white", 
                  command=self.analytics_router).grid(row=0, column=4, padx=5)

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

    def analytics_router(self):
        """Validates time constraints and routes to the selected chart."""
        current_start = self.ent_from.get()
        current_end = self.ent_to.get()
        try:
            start_dt = datetime.strptime(self.ent_from.get(), "%Y-%m-%d")
            end_dt = datetime.strptime(self.ent_to.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format.")
            return
        
        if not self.current_report_data: 
            print("Current data is empty, generating report now...") # English log
            self.generate_report()

        if not self.current_report_data:
            messagebox.showwarning("No Data", "No data available to analyze.")
            return    

        delta_days = (end_dt - start_dt).days
        group_type = self.combo_group.get()
        chart_type = self.combo_chart.get()
        selected_shop = self.combo_customer.get()

        if chart_type == "Profit Margin" and selected_shop != "All Customers":
            messagebox.showwarning("Logic Error", 
                "Profit Margin analysis compares total purchases vs sales. Please set Shop to 'All Customers'.")
            return
        

        # Validation Logic
        if group_type == "Weekly" and delta_days < 14:
            messagebox.showwarning("Range Error", "Weekly grouping requires at least 14 days.")
            return
        elif group_type == "Monthly" and delta_days < 60:
            messagebox.showwarning("Range Error", "Monthly grouping requires at least 60 days (2 months).")
            return
        # Check if date filters have changed since the last successful search
        if current_start != self.last_search_start or current_end != self.last_search_end:
            # Force refresh data to ensure charts match the current UI filters
            self.generate_report()

            # Update the last search timestamps to prevent redundant fetches
            self.last_search_start = current_start
            self.last_search_end = current_end

        # Routing Logic
        if chart_type == "Profit Margin":
            AnalyticsManager.display_profit_margin(self.current_report_data, group_type, start_dt, end_dt)
        # Future charts will be added here

        
    def export_to_excel(self):
        import pandas as pd # Library required for Excel file generation
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