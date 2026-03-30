import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database_manager import DatabaseManager
import pandas as pd # New Import for Excel handling
from tkinter import filedialog # To choose save location

class ReportsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Devo - Financial Reports")
        self.root.geometry("500x500")
        
        self.db = DatabaseManager()
        self.create_widgets()

    def create_widgets(self):
        """Build the report interface with date filtering."""
        tk.Label(self.root, text="Financial Performance", font=("Arial", 18, "bold")).pack(pady=15)

        # 1. Date Range Selection
        filter_frame = tk.LabelFrame(self.root, text="Filter by Date (YYYY-MM-DD)", padx=10, pady=10)
        filter_frame.pack(padx=20, pady=10, fill="x")

        tk.Label(filter_frame, text="From:").grid(row=0, column=0)
        self.ent_start = tk.Entry(filter_frame)
        self.ent_start.insert(0, "2026-01-01") # Default start
        self.ent_start.grid(row=0, column=1, padx=5)

        tk.Label(filter_frame, text="To:").grid(row=0, column=2)
        self.ent_end = tk.Entry(filter_frame)
        self.ent_end.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_end.grid(row=0, column=3, padx=5)

        # 2. Action Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Generate Report", bg="blue", fg="white", 
                  width=15, command=self.generate_report).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Export to Excel", bg="darkgreen", fg="white", 
              width=15, command=self.export_to_excel).pack(side="left", padx=5)

        # 3. Results Display (Labels)
        results_frame = tk.LabelFrame(self.root, text="Results", padx=20, pady=20)
        results_frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.lbl_sales = tk.Label(results_frame, text="Total Sales: 0.00 SAR", font=("Arial", 12))
        self.lbl_sales.pack(pady=5)

        self.lbl_purchases = tk.Label(results_frame, text="Total Purchases: 0.00 SAR", font=("Arial", 12))
        self.lbl_purchases.pack(pady=5)

        self.lbl_profit = tk.Label(results_frame, text="Net Profit: 0.00 SAR", 
                                   font=("Arial", 14, "bold"), fg="green")
        self.lbl_profit.pack(pady=15)
    
    def generate_report(self):
        """Calculate and display totals from DB."""
        start = self.ent_start.get()
        end = self.ent_end.get()

        try:
            # 1. Fetch Total Sales
            sales_query = "SELECT SUM(total_price) FROM sales WHERE sale_date BETWEEN ? AND ?"
            cursor = self.db.connection.cursor()
            cursor.execute(sales_query, (start, end))
            total_sales = cursor.fetchone()[0] or 0.0

            # 2. Fetch Total Purchases
            purch_query = "SELECT SUM(cost_price) FROM purchases WHERE purchase_date BETWEEN ? AND ?"
            cursor.execute(purch_query, (start, end))
            total_purch = cursor.fetchone()[0] or 0.0

            # 3. Calculate Profit
            profit = total_sales - total_purch

            # 4. Update UI
            self.lbl_sales.config(text=f"Total Sales: {total_sales:.2f} SAR")
            self.lbl_purchases.config(text=f"Total Purchases: {total_purch:.2f} SAR")
            self.lbl_profit.config(text=f"Net Profit: {profit:.2f} SAR")
            
            # Change profit color based on value
            if profit < 0:
                self.lbl_profit.config(fg="red")
            else:
                self.lbl_profit.config(fg="green")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
    def export_to_excel(self):
        """Fetch all sales and purchases data and save to an Excel file."""
        try:
            # 1. Fetch Sales Data
            sales_df = pd.read_sql_query("SELECT * FROM sales", self.db.connection)
            
            # 2. Fetch Purchases Data
            purch_df = pd.read_sql_query("SELECT * FROM purchases", self.db.connection)
            
            # 3. Choose where to save the file
            file_path = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Report As"
            )
            
            if file_path:
                # Use ExcelWriter to save multiple sheets in one file
                with pd.ExcelWriter(file_path) as writer:
                    sales_df.to_excel(writer, sheet_name='Sales', index=False)
                    purch_df.to_excel(writer, sheet_name='Purchases', index=False)
                
                messagebox.showinfo("Success", f"Report exported to:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export data: {str(e)}")
if __name__ == "__main__":
    app_root = tk.Tk()
    ReportsWindow(app_root)
    app_root.mainloop()