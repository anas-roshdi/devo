import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from tkinter import messagebox

class AnalyticsManager:
    @staticmethod
    def display_profit_margin(data, group_type, start_dt, end_dt):
        """Analyzes and plots Weekly/Monthly profit margins from a business-wide perspective."""
        # import time
        # 1. Start timing the logic/processing part
        # start_proc = time.perf_counter()

        sales_data = {}
        purchases_data = {}
        
        # We assume 'data' contains all records because of the check in the router
        for row in data:
            try:
                current_dt = datetime.strptime(row[0], "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
            
            # Dynamic grouping logic
            if group_type == "Weekly":
                days_diff = (current_dt - start_dt).days
                idx = days_diff // 7
                label = (start_dt + timedelta(days=idx * 7)).strftime("%m-%d")
            else: 
                # Monthly: Group by Year and Month
                label = current_dt.strftime("%Y-%m")
            
            amount = row[3]
            if row[1] == 'SALE':
                sales_data[label] = sales_data.get(label, 0) + amount
            elif row[1] == 'PURCHASE':
                purchases_data[label] = purchases_data.get(label, 0) + amount

        # Ensure chronological order and shared axis labels
        all_labels = sorted(list(set(sales_data.keys()) | set(purchases_data.keys())))
        sales_values = [sales_data.get(l, 0) for l in all_labels]
        purchase_values = [purchases_data.get(l, 0) for l in all_labels]

        if not all_labels:
            messagebox.showinfo("No Data", "No financial records found for the selected period.")
            return

        # --- Plotting Logic ---
        x = range(len(all_labels))
        width = 0.35
        fig, ax = plt.subplots(figsize=(12, 7))
        
        rects1 = ax.bar([i - width/2 for i in x], sales_values, width, label='Total Sales', color='#2ecc71')
        rects2 = ax.bar([i + width/2 for i in x], purchase_values, width, label='Total Purchases', color='#e74c3c')

        # Formatting with professional styling
        title_suffix = "Weekly" if group_type == "Weekly" else "Monthly"
        ax.set_title(f'Business Profit Margin Analysis ({title_suffix})\nRange: {start_dt.date()} to {end_dt.date()}', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_ylabel('Amount (SAR)', fontsize=11, fontweight='bold')
        ax.set_xlabel('Time Period', fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(all_labels, rotation=45)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        # Attach value labels above bars
        AnalyticsManager._add_bar_labels(ax, rects1)
        AnalyticsManager._add_bar_labels(ax, rects2)

        # 2. End timing JUST BEFORE showing the window
        # end_proc = time.perf_counter()
        # print(f" Logic & Rendering Time: {end_proc - start_proc:.4f} seconds")

        plt.tight_layout()
        plt.show()
        
       
    @staticmethod
    def _add_bar_labels(ax, rects):
        """Helper method to attach a text label above each bar."""
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.0f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, fontweight='bold')
               