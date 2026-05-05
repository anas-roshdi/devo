import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
import time
import arabic_reshaper
from bidi.algorithm import get_display

class AnalyticsManager:
    @staticmethod
    def display_profit_margin(data, group_type, start_dt, end_dt, enable_forecast=False, forecast_periods=3):
        """Analyzes history and optionally forecasts both Sales & Purchases."""
        start_proc = time.perf_counter()
        
        sales_by_date = {}
        purchases_by_date = {}
        
        # 1. Data Processing
        for row in data:
            try:
                current_dt = datetime.strptime(row[0], "%Y-%m-%d")
            except: continue
            
            if group_type == "Weekly":
                idx = (current_dt - start_dt).days // 7
                period_key = start_dt + timedelta(days=idx * 7)
            else: 
                period_key = datetime(current_dt.year, current_dt.month, 1)
            
            amount = row[3]
            if row[1] == 'SALE':
                sales_by_date[period_key] = sales_by_date.get(period_key, 0) + amount
            elif row[1] == 'PURCHASE':
                purchases_by_date[period_key] = purchases_by_date.get(period_key, 0) + amount

        sorted_keys = sorted(list(set(sales_by_date.keys()) | set(purchases_by_date.keys())))
        if not sorted_keys: return

        sales_values = [sales_by_date.get(k, 0) for k in sorted_keys]
        purchase_values = [purchases_by_date.get(k, 0) for k in sorted_keys]
        all_labels = [k.strftime("%m-%d" if group_type == "Weekly" else "%Y-%m") for k in sorted_keys]

        # 2. AI Forecasting Logic for both Sales & Purchases
        f_labels, f_sales, f_purchases = [], [], []
        
        if enable_forecast and len(sales_values) >= 3:
            X = np.array(range(len(sales_values))).reshape(-1, 1)
            future_indices = np.array(range(len(sales_values), len(sales_values) + forecast_periods)).reshape(-1, 1)
            
            # Forecast Sales
            model_s = LinearRegression().fit(X, np.array(sales_values))
            f_sales = [max(0, p) for p in model_s.predict(future_indices)]
            
            # Forecast Purchases
            model_p = LinearRegression().fit(X, np.array(purchase_values))
            f_purchases = [max(0, p) for p in model_p.predict(future_indices)]
            
            suffix = "W" if group_type == "Weekly" else "M"
            f_labels = [f"F-{suffix}{i+1}" for i in range(forecast_periods)]

        # 3. Plotting
        x_act = range(len(all_labels))
        x_for = range(len(all_labels), len(all_labels) + len(f_labels))
        width = 0.35
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Plot Actuals
        r1 = ax.bar([i - width/2 for i in x_act], sales_values, width, label='Actual Sales', color='#2ecc71')
        r2 = ax.bar([i + width/2 for i in x_act], purchase_values, width, label='Actual Purchases', color='#e74c3c')
        
        # Plot Forecasts
        r3, r4 = None, None
        if f_labels:
            r3 = ax.bar([i - width/2 for i in x_for], f_sales, width, label='AI Sales Forecast', 
                        color='#2ecc71', alpha=0.3, edgecolor='#2ecc71', linestyle='--', hatch='//')
            r4 = ax.bar([i + width/2 for i in x_for], f_purchases, width, label='AI Purchase Forecast', 
                        color='#e74c3c', alpha=0.3, edgecolor='#e74c3c', linestyle='--', hatch='\\')

        # Add Labels
        for r in [r1, r2, r3, r4]:
            if r: AnalyticsManager._add_bar_labels(ax, r)

        # Styling
        ax.set_title(f'Profit Margin & AI Double-Forecast ({group_type})', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(list(x_act) + list(x_for))
        ax.set_xticklabels(all_labels + f_labels, rotation=45)
        ax.legend()
        
        plt.tight_layout()
        print(f"AI Analytics Performance: {time.perf_counter() - start_proc:.4f}s")
        plt.show()

    @staticmethod
    def _add_bar_labels(ax, rects):
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.0f}', xy=(rect.get_x() + rect.get_width()/2, height),
                            xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', 
                            fontsize=8, fontweight='bold')
                
    @staticmethod
    def display_top_products(data, num_fields):
        """
        Generates a horizontal bar chart for the top selling products.
        Includes support for proper rendering of Arabic text in Matplotlib.
        """
        # Import required libraries for plotting and Arabic text rendering
        import matplotlib.pyplot as plt
        import arabic_reshaper
        from bidi.algorithm import get_display

        # Ensure a font that supports Arabic characters is used globally (e.g., Arial, Tahoma)
        plt.rcParams['font.family'] = 'Arial' 

        labels = []
        values = []

        # Process the data rows dynamically based on the selected group fields
        for row in data:
            # Combine the selected text fields (e.g., Name, Category) into a single string
            raw_label = " - ".join(str(item) for item in row[:num_fields])
            
            # Fix Arabic text rendering issues (reshaping and Right-to-Left direction)
            reshaped_text = arabic_reshaper.reshape(raw_label)
            bidi_text = get_display(reshaped_text)
            
            # Append the corrected text and the quantity value
            labels.append(bidi_text)
            values.append(row[-1]) # The last element is always the total quantity

        # Create the figure and axis for the chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot the horizontal bar chart
        bars = ax.barh(labels, values, color='#3498db')
        
        # Invert the Y-axis so the product with the highest sales appears at the very top
        ax.invert_yaxis()

        # Add data labels (e.g., "523 Units") at the end of each bar for better readability
        max_value = max(values) if values else 1
        for bar in bars:
            width = bar.get_width()
            # Calculate a slight offset based on the maximum value to position the text nicely
            offset = max_value * 0.01
            
            ax.text(width + offset, 
                    bar.get_y() + bar.get_height() / 2, 
                    f'{int(width)} Units', 
                    ha='left', 
                    va='center', 
                    fontweight='bold')

        # Set chart title and labels
        ax.set_title("Top Best-Selling Products", fontsize=16, fontweight='bold')
        ax.set_xlabel("Total Quantity Sold", fontweight='bold')
        
        # Adjust layout to prevent label cropping and display the chart
        plt.tight_layout()
        plt.show()

    @staticmethod
    def display_customer_performance(data):
        """
        Generates a Bubble Chart for customer performance / VIP analysis.
        
        Data format: list of (customer_name, total_invoices, total_units, total_amount)
        - X-axis: Total Amount Spent (how much they pay)
        - Y-axis: Number of Invoices (how often they buy)
        - Bubble size: Total Units purchased (volume)
        - Color: Gradient based on total amount (darker = higher value)
        """
        import matplotlib.pyplot as plt
        import arabic_reshaper
        from bidi.algorithm import get_display
        import numpy as np
        
        plt.rcParams['font.family'] = 'Arial'
        
        if not data:
            return
        
        names = []
        invoices = []   # Y-axis
        amounts = []    # X-axis
        units = []      # Bubble size
        
        for row in data:
            # Fix Arabic text rendering
            reshaped = arabic_reshaper.reshape(str(row[0]))
            bidi_name = get_display(reshaped)
            names.append(bidi_name)
            invoices.append(row[1])
            units.append(row[2])
            amounts.append(row[3])
        
        # --- Create the Bubble Chart ---
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Normalize bubble sizes (min 200, max 2500 for visibility)
        units_arr = np.array(units, dtype=float)
        if units_arr.max() > units_arr.min():
            normalized = 200 + (units_arr - units_arr.min()) / (units_arr.max() - units_arr.min()) * 2300
        else:
            normalized = np.full_like(units_arr, 800)
        
        # Color gradient based on total amount (gold → red for VIP)
        amounts_arr = np.array(amounts, dtype=float)
        colors = plt.cm.YlOrRd(np.linspace(0.3, 0.95, len(amounts_arr)))
        
        # Sort by amount so highest is plotted last (on top)
        sort_idx = np.argsort(amounts_arr)
        
        # Plot bubbles
        scatter = ax.scatter(
            amounts_arr[sort_idx], 
            np.array(invoices)[sort_idx],
            s=normalized[sort_idx],
            c=colors[np.arange(len(sort_idx))],
            alpha=0.75,
            edgecolors='#2c3e50',
            linewidths=1.5,
            zorder=5
        )
        
        # Add customer name labels on each bubble
        for i in sort_idx:
            ax.annotate(
                names[i],
                (amounts[i], invoices[i]),
                ha='center', va='center',
                fontsize=8, fontweight='bold', color='#2c3e50',
                zorder=6
            )
        
        # Mark the VIP customer (highest amount) with a special highlight
        vip_idx = int(np.argmax(amounts_arr))
        ax.annotate(
            '⭐ VIP',
            (amounts[vip_idx], invoices[vip_idx]),
            xytext=(15, 15), textcoords='offset points',
            fontsize=11, fontweight='bold', color='#c0392b',
            arrowprops=dict(arrowstyle='->', color='#c0392b', lw=2),
            zorder=7
        )
        
        # --- Styling ---
        ax.set_title('Customer Performance & VIP Analysis', 
                     fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
        ax.set_xlabel('Total Amount Spent', fontsize=12, fontweight='bold', color='#34495e')
        ax.set_ylabel('Number of Invoices (Orders)', fontsize=12, fontweight='bold', color='#34495e')
        
        # Grid for readability
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Background styling
        fig.patch.set_facecolor('#fafafa')
        ax.set_facecolor('#fafafa')
        
        # Add size legend (explaining bubble size = units)
        legend_sizes = [int(units_arr.min()), int(np.median(units_arr)), int(units_arr.max())]
        legend_sizes = sorted(set(legend_sizes))  # Remove duplicates
        
        if units_arr.max() > units_arr.min():
            legend_normalized = [200 + (s - units_arr.min()) / (units_arr.max() - units_arr.min()) * 2300 
                                for s in legend_sizes]
        else:
            legend_normalized = [800 for _ in legend_sizes]
        
        legend_bubbles = [ax.scatter([], [], s=sz, c='#f39c12', alpha=0.6, 
                                     edgecolors='#2c3e50', linewidths=1)
                         for sz in legend_normalized]
        ax.legend(legend_bubbles, [f'{s} Units' for s in legend_sizes],
                 title='Total Units Purchased', title_fontsize=10,
                 loc='upper left', framealpha=0.9, fontsize=9)
        
        plt.tight_layout()
        plt.show()