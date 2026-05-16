"""
Financial Analytics & Reports Window.
=======================================
Provides financial reporting, top product analysis, AI forecasting,
and Excel export functionality.
All database operations go through DatabaseManager methods.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from src.database.database_manager import DatabaseManager
from src.utils.widgets import CalendarHelper
from src.utils.analytics import AnalyticsManager
from config import (Colors, Fonts, WindowConfig, ALL_CUSTOMERS_LABEL,
                    ANALYSIS_MODES, GROUP_BY_OPTIONS, DEFAULT_TOP_LIMIT, 
                    DEFAULT_FORECAST_PERIODS)
import time
from src.utils.translator import t, get_pack_side, is_rtl


class ReportsWindow:
    def __init__(self, root):
        """Initialize the Reports Window and core database/variable components."""
        self.root = root
        self.root.title(t('reports_win_title'))
        
        geo, min_w, min_h = WindowConfig.REPORTS
        self.root.geometry(geo)
        self.root.minsize(min_w, min_h)
        
        # Initialize database manager instance
        self.db = DatabaseManager()
        
        # Storage for report data and search history
        self.current_report_data = [] 
        self.last_search_start = None
        self.last_search_end = None

        # Initialize UI Variables for tracking states and filter values
        self.var_enable_forecast = tk.BooleanVar(value=False)
        self.var_forecast_periods = tk.IntVar(value=DEFAULT_FORECAST_PERIODS)
        self.var_grp_name = tk.BooleanVar(value=True)
        self.var_grp_cat = tk.BooleanVar(value=False)
        self.var_grp_size = tk.BooleanVar(value=False)
        self.var_top_limit = tk.IntVar(value=DEFAULT_TOP_LIMIT)
        
        # Build the user interface and load initial data filters
        self.create_widgets()
        self.load_filters()

    def create_widgets(self):
        """Create and arrange all UI components including filters, cards, and tables."""
        
        # --- Filter Section Frame ---
        filter_frame = tk.LabelFrame(self.root, text=t('lbl_report_filters'), padx=10, pady=10)
        filter_frame.pack(fill="x", padx=20, pady=10)

        # Organized rows inside the filter frame using Grid
        row1 = tk.Frame(filter_frame)
        row1.pack(fill="x", pady=5)
        
        row2 = tk.Frame(filter_frame)
        row2.pack(fill="x", pady=5)

        # Row 1: 
        # Shop Selection and Date Range
        tk.Label(row1, text=t('lbl_shop')).grid(row=0, column=0)
        self.combo_customer = ttk.Combobox(row1, state="readonly", width=20)
        self.combo_customer.grid(row=0, column=1, padx=5)
        
        current_year = datetime.now().year
        
        # Start Date Entry with Calendar Helper
        tk.Label(row1, text=t('lbl_from')).grid(row=0, column=2)
        self.ent_from = tk.Entry(row1, width=10)
        self.ent_from.insert(0, f"{current_year}-01-01") 
        self.ent_from.grid(row=0, column=3)
        tk.Button(row1, text="📅", 
                  command=lambda: CalendarHelper.show_calendar(self.root, self.ent_from)
                  ).grid(row=0, column=4, padx=5)

        # End Date Entry with Calendar Helper
        tk.Label(row1, text=t('lbl_to')).grid(row=0, column=5)
        self.ent_to = tk.Entry(row1, width=10)
        self.ent_to.insert(0, f"{current_year}-12-31") 
        self.ent_to.grid(row=0, column=6)
        tk.Button(row1, text="📅", 
                  command=lambda: CalendarHelper.show_calendar(self.root, self.ent_to)
                  ).grid(row=0, column=7, padx=5)

        # Execution Buttons
        tk.Button(row1, text=t('btn_generate'), bg=Colors.BLUE_DARK, fg=Colors.TEXT_WHITE, 
                  command=self.generate_btn_action).grid(row=0, column=8, padx=5)
        tk.Button(row1, text=t('btn_export_excel'), bg=Colors.GREEN_DARK, fg=Colors.TEXT_WHITE, 
                  command=self.export_to_excel).grid(row=0, column=9, padx=5)
        
        # Row 2: Dynamic Analysis Options and Forecast Controls
        # Limit frame for Top Products and Customer Performance
        self.frame_limit = tk.Frame(row2)
        tk.Label(self.frame_limit, text=t('lbl_limit')).pack(side=get_pack_side(tk.LEFT))
        self.spin_top_limit = tk.Spinbox(self.frame_limit, from_=1, to=100, width=5, textvariable=self.var_top_limit)
        self.spin_top_limit.pack(side=get_pack_side(tk.LEFT), padx=5)
        
        # Grouping frame specifically for 'Top Products' analysis mode
        self.frame_grouping = tk.Frame(row2)
        tk.Checkbutton(self.frame_grouping, text=t('chk_name'), variable=self.var_grp_name).pack(side=get_pack_side(tk.LEFT))
        tk.Checkbutton(self.frame_grouping, text=t('chk_category'), variable=self.var_grp_cat).pack(side=get_pack_side(tk.LEFT))
        tk.Checkbutton(self.frame_grouping, text=t('chk_size'), variable=self.var_grp_size).pack(side=get_pack_side(tk.LEFT))

        # Chart/Analysis Mode Selector
        tk.Label(row2, text=t('lbl_analysis')).grid(row=0, column=0, pady=5)
        self.combo_chart = ttk.Combobox(row2, state="readonly", width=18)
        self.analysis_modes_map = {
            t('mode_profit_margin'): "Profit Margin",
            t('mode_top_products'): "Top Products",
            t('mode_customer_performance'): "Customer Performance"
        }
        self.combo_chart['values'] = list(self.analysis_modes_map.keys())
        self.combo_chart.set(t('mode_profit_margin'))
        self.combo_chart.grid(row=0, column=1, padx=5)

        # Time Grouping Selector (Weekly/Monthly)
        self.lbl_group_by = tk.Label(row2, text=t('lbl_group_by'))
        self.lbl_group_by.grid(row=0, column=2)
        self.combo_group = ttk.Combobox(row2, state="readonly", width=10)
        self.group_options_map = {
            t('grp_weekly'): "Weekly",
            t('grp_monthly'): "Monthly"
        }
        self.combo_group['values'] = list(self.group_options_map.keys())
        self.combo_group.set(t('grp_weekly'))
        self.combo_group.grid(row=0, column=3, padx=5)

        # AI Forecast Settings
        self.forecast_sub_frame = tk.Frame(row2)
        self.forecast_sub_frame.grid(row=0, column=4, padx=5)
        tk.Label(self.forecast_sub_frame, text=t('chk_enable_forecast')).pack(side=get_pack_side(tk.LEFT))
        self.check_forecast = tk.Checkbutton(self.forecast_sub_frame, variable=self.var_enable_forecast)
        self.check_forecast.pack(side=get_pack_side(tk.LEFT))
        self.lbl_periods = tk.Label(row2, text=t('lbl_periods'))
        self.lbl_periods.grid(row=0, column=5)
        self.spin_periods = tk.Spinbox(row2, from_=1, to=12, width=5, textvariable=self.var_forecast_periods)
        self.spin_periods.grid(row=0, column=6)
        tk.Button(row2, text=t('btn_show_analytics'), bg=Colors.PURPLE, fg=Colors.TEXT_WHITE, 
                  command=self.analytics_router).grid(row=0, column=7, padx=5)

        # Bind change event to dynamically update the UI layout
        self.combo_chart.bind("<<ComboboxSelected>>", self.on_chart_change)

        # --- Summary Section (Using PACK) ---
        # IMPORTANT: Summary cards use 'pack' layout. Do not use 'grid' on these items.
        self.summary_frame = tk.Frame(self.root)
        self.summary_frame.pack(fill="x", padx=20, pady=10)

        self.card_sales = tk.Label(self.summary_frame, text=f"{t('lbl_total_sales')}\n0.00", 
                                   bg=Colors.GREEN, fg=Colors.TEXT_WHITE, 
                                   font=Fonts.CARD, width=22, height=3)
        self.card_sales.pack(side=get_pack_side(tk.LEFT), padx=5)

        self.card_purchases = tk.Label(self.summary_frame, text=f"{t('lbl_total_purchases')}\n0.00", 
                                       bg=Colors.RED, fg=Colors.TEXT_WHITE, 
                                       font=Fonts.CARD, width=22, height=3)
        self.card_purchases.pack(side=get_pack_side(tk.LEFT), padx=5)

        self.card_profit = tk.Label(self.summary_frame, text=f"{t('lbl_net_profit')}\n0.00", 
                                    bg=Colors.YELLOW, fg=Colors.TEXT_BLACK, 
                                    font=Fonts.CARD, width=22, height=3)
        self.card_profit.pack(side=get_pack_side(tk.LEFT), padx=5)

        # Specialized card for product units (hidden by default)
        self.card_top_units = tk.Label(self.summary_frame, text=f"{t('lbl_total_units')}\n0", 
                                       bg=Colors.DARK_GRAY, fg=Colors.TEXT_WHITE, 
                                       font=Fonts.CARD, width=22, height=3)

        # Customer Performance cards (hidden by default)
        self.card_vip_name = tk.Label(self.summary_frame, text=f"{t('lbl_vip_customer')}\n---",
                                      bg="#e67e22", fg=Colors.TEXT_WHITE,
                                      font=Fonts.CARD, width=22, height=3)
        self.card_total_customers = tk.Label(self.summary_frame, text=f"{t('lbl_active_customers')}\n0",
                                             bg=Colors.PURPLE, fg=Colors.TEXT_WHITE,
                                             font=Fonts.CARD, width=22, height=3)
        self.card_total_revenue = tk.Label(self.summary_frame, text=f"{t('lbl_total_revenue')}\n0.00",
                                           bg=Colors.BLUE_DARK, fg=Colors.TEXT_WHITE,
                                           font=Fonts.CARD, width=22, height=3)

        # --- Main Data Table (Treeview) ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.standard_columns = (t('col_date'), t('col_type'), t('col_entity'), t('col_amount'))
        self.tree = ttk.Treeview(table_frame, columns=self.standard_columns, show="headings")
        for col in self.standard_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(side=get_pack_side(tk.LEFT), fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def generate_report(self):
        """Fetch sales and purchase records and update the summary cards based on selection."""
        customer = self.combo_customer.get()
        start = self.ent_from.get()
        end = self.ent_to.get()

        # Reset and define standard columns for financial view
        self.tree["columns"] = self.standard_columns
        for col in self.standard_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

        # Fetch data from DatabaseManager
        sales, purchases = self.db.get_financial_report(customer, start, end)

        # Merge results and populate the Treeview
        self.current_report_data = list(sales) + list(purchases)
        for i in self.tree.get_children(): self.tree.delete(i)
        for row in self.current_report_data: self.tree.insert("", "end", values=row)
        
        # Update Sales Card
        ts = sum(s[3] for s in sales)
        self.card_sales.config(text=f"{t('lbl_total_sales')}\n{ts:.2f}")
        
        # Update Purchase and Profit cards only for global view
        if customer == t('all_customers'):
            tp = sum(p[3] for p in purchases) 
            # Re-display cards using PACK to maintain layout integrity
            self.card_purchases.pack(side=get_pack_side(tk.LEFT), padx=5) 
            self.card_profit.pack(side=get_pack_side(tk.LEFT), padx=5)    
            self.card_purchases.config(text=f"{t('lbl_total_purchases')}\n{tp:.2f}")
            self.card_profit.config(text=f"{t('lbl_net_profit')}\n{(ts - tp):.2f}")
        else:
            # Hide non-relevant cards for specific shop view
            self.card_purchases.pack_forget() 
            self.card_profit.pack_forget()

    def _hide_all_mode_elements(self):
        """Hide all mode-specific UI elements (cards, filters) for clean switching."""
        # Hide all summary cards
        self.card_sales.pack_forget()
        self.card_purchases.pack_forget()
        self.card_profit.pack_forget()
        self.card_top_units.pack_forget()
        self.card_vip_name.pack_forget()
        self.card_total_customers.pack_forget()
        self.card_total_revenue.pack_forget()
        
        # Hide mode-specific filter elements
        self.frame_limit.grid_remove()
        self.frame_grouping.grid_remove()
        self.lbl_group_by.grid_remove()
        self.combo_group.grid_remove()
        self.forecast_sub_frame.grid_remove()
        self.lbl_periods.grid_remove()
        self.spin_periods.grid_remove()

    def on_chart_change(self, event=None):
        """Dynamically toggle between analysis mode UI layouts."""
        mode = self.analysis_modes_map.get(self.combo_chart.get())
        self._hide_all_mode_elements()
        
        if mode == "Top Products":
            # Show Top Product specific grouping and cards
            self.frame_limit.grid(row=0, column=2, sticky="w", padx=5)
            self.frame_grouping.grid(row=0, column=3, columnspan=2, sticky="w", padx=5)
            self.card_top_units.pack(side=get_pack_side(tk.LEFT), padx=5)
            
        elif mode == "Customer Performance":
            # Show Customer Performance cards
            self.frame_limit.grid(row=0, column=2, sticky="w", padx=5)
            self.card_vip_name.pack(side=get_pack_side(tk.LEFT), padx=5)
            self.card_total_customers.pack(side=get_pack_side(tk.LEFT), padx=5)
            self.card_total_revenue.pack(side=get_pack_side(tk.LEFT), padx=5)
            
        else:  # Profit Margin (default)
            # Restore Financial Analysis layout
            self.lbl_group_by.grid()
            self.combo_group.grid()
            self.forecast_sub_frame.grid()
            self.lbl_periods.grid()
            self.spin_periods.grid()

            # Restore cards logically based on customer selection
            self.card_sales.pack(side=get_pack_side(tk.LEFT), padx=5)
            if self.combo_customer.get() == t('all_customers'):
                self.card_purchases.pack(side=get_pack_side(tk.LEFT), padx=5)
                self.card_profit.pack(side=get_pack_side(tk.LEFT), padx=5)

    def generate_btn_action(self):
        """Determine which report function to execute based on current selection."""
        mode = self.analysis_modes_map.get(self.combo_chart.get())
        if mode == "Top Products":
            self.fetch_and_display_top_products()
        elif mode == "Customer Performance":
            self.fetch_and_display_customer_performance()
        else:
            self.generate_report()

    def analytics_router(self):
        """Route to appropriate AnalyticsManager function for chart generation."""
        current_start = self.ent_from.get()
        current_end = self.ent_to.get()
        chart_type = self.analysis_modes_map.get(self.combo_chart.get())
        try:
            start_dt = datetime.strptime(current_start, "%Y-%m-%d")
            end_dt = datetime.strptime(current_end, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(t('msg_error_title'), t('msg_invalid_date_format'))
            return

        if chart_type == "Top Products":
            data = self.fetch_and_display_top_products()
            if data:
                # num_fields defines the descriptive columns before the 'Quantity' column
                AnalyticsManager.display_top_products(data, len(data[0]) - 1)
        elif chart_type == "Customer Performance":
            data = self.fetch_and_display_customer_performance()
            if data:
                AnalyticsManager.display_customer_performance(data)
        elif chart_type == "Profit Margin":
            # Refresh data if filters have changed
            if not self.current_report_data or current_start != self.last_search_start:
                self.generate_report()
            AnalyticsManager.display_profit_margin(
                self.current_report_data, self.group_options_map.get(self.combo_group.get()), 
                start_dt, end_dt, 
                self.var_enable_forecast.get(), self.var_forecast_periods.get()
            )

    def fetch_and_display_top_products(self):
        """Retrieve top selling products based on dynamic grouping (Name, Category, Size)."""
        group_fields = []
        if self.var_grp_name.get(): group_fields.append('name')
        if self.var_grp_cat.get(): group_fields.append('category')
        if self.var_grp_size.get(): group_fields.append('size')
        if not group_fields: group_fields = ['name']  # Default fallback

        # Fetch data from database
        top_products = self.db.get_top_products_dynamic(
            self.ent_from.get(), self.ent_to.get(), 
            group_fields, self.combo_customer.get(), self.var_top_limit.get()
        )
        
        if not top_products:
            messagebox.showinfo(t('msg_no_data'), t('msg_no_product_sales'))
            return None 

        # Update product statistics card
        self.card_top_units.config(text=f"{t('lbl_total_units')}\n{int(sum(row[-1] for row in top_products))}")
        
        # Dynamically rebuild Treeview columns based on selected groupings
        col_names = []
        for f in group_fields:
            if f == 'name': col_names.append(t('chk_name'))
            elif f == 'category': col_names.append(t('chk_category'))
            elif f == 'size': col_names.append(t('chk_size'))
        col_names.append(t('col_qty_sold'))
        
        self.tree["columns"] = tuple(col_names)
        for col in col_names:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)
            
        self.tree.delete(*self.tree.get_children())
        for row in top_products: self.tree.insert("", tk.END, values=row)
        return top_products

    def fetch_and_display_customer_performance(self):
        """Retrieve customer performance data and display in table with summary cards."""
        # Fetch data from database
        perf_data = self.db.get_customer_performance(
            self.ent_from.get(), self.ent_to.get(), 
            self.var_top_limit.get()
        )
        
        if not perf_data:
            messagebox.showinfo(t('msg_no_data'), t('msg_no_customer_sales'))
            return None
        
        # Update summary cards
        vip_name = perf_data[0][0]  # First row = highest amount
        total_customers = len(perf_data)
        total_revenue = sum(row[3] for row in perf_data)
        
        self.card_vip_name.config(text=f"{t('lbl_vip_customer')}\n{vip_name}")
        self.card_total_customers.config(text=f"{t('lbl_active_customers')}\n{total_customers}")
        self.card_total_revenue.config(text=f"{t('lbl_total_revenue')}\n{total_revenue:,.2f}")
        
        # Rebuild Treeview columns for customer performance
        col_names = (t('col_customer'), t('col_invoices'), t('col_units_bought'), t('col_total_amount'))
        self.tree["columns"] = col_names
        for col in col_names:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)
        
        self.tree.delete(*self.tree.get_children())
        for row in perf_data:
            # Format the amount with 2 decimal places
            formatted = (row[0], row[1], row[2], f"{row[3]:,.2f}")
            self.tree.insert("", tk.END, values=formatted)
        
        return perf_data

    def load_filters(self):
        """Fetch all customers from DB and populate the shop filter dropdown."""
        customers = self.db.get_all_customers()
        self.combo_customer['values'] = [t('all_customers')] + [c[1] for c in customers]
        self.combo_customer.set(t('all_customers'))

    def export_to_excel(self):
        """Export the current viewable report data to an Excel spreadsheet."""
        import pandas as pd
        if not self.current_report_data: 
            messagebox.showwarning(t('msg_empty_title'), t('msg_no_data_export'))
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if file_path:
            try:
                pd.DataFrame(self.current_report_data).to_excel(file_path, index=False)
                messagebox.showinfo(t('msg_success_title'), t('msg_report_exported'))
            except Exception as e:
                messagebox.showerror(t('msg_error_title'), t('msg_export_failed').format(e=e))

# Entry point for testing the module directly
if __name__ == "__main__":
    root = tk.Tk()
    app = ReportsWindow(root)
    root.mainloop()