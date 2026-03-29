import pandas as pd
from datetime import datetime

class BusinessLogic:
    """
    Handles complex calculations and data exporting for the devo system.
    Connects the DatabaseManager with the UI.
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def calculate_total_revenue(self, start_date, end_date):
        """Fetch and sum all sales within a date range."""
        query = "SELECT SUM(total_price) FROM sales WHERE sale_date BETWEEN ? AND ?"
        cursor = self.db.connection.cursor()
        cursor.execute(query, (start_date, end_date))
        result = cursor.fetchone()
        return result[0] if result[0] else 0.0

    def calculate_net_profit(self, start_date, end_date):
        """Net Profit = Total Sales - Total Purchase Costs."""
        revenue = self.calculate_total_revenue(start_date, end_date)
        
        # Calculate total costs from purchases
        query = "SELECT SUM(quantity * cost_price) FROM purchases WHERE purchase_date BETWEEN ? AND ?"
        cursor = self.db.connection.cursor()
        cursor.execute(query, (start_date, end_date))
        cost_result = cursor.fetchone()
        total_cost = cost_result[0] if cost_result[0] else 0.0
        
        return revenue - total_cost

    def export_to_excel(self, table_name, file_name):
        """Export any database table to a professional Excel report."""
        try:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, self.db.connection)
            path = f"reports/{file_name}.xlsx"
            df.to_excel(path, index=False)
            print(f"Report saved to {path}")
            return True
        except Exception as e:
            print(f"Export Error: {e}")
            return False