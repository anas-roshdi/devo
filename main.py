"""
Devo Business Management System - Main Dashboard
==================================================
Entry point for the application. Displays the main navigation menu
with buttons to access all system modules.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
from src.utils.license_verifier import is_licensed, show_license_screen

# --- GATEKEEPER CHECK ---
# If the app is not licensed, show the activation screen
if not is_licensed():
    success = show_license_screen()
    # If the user closes the window without activating, exit the app entirely
    if not success:
        sys.exit()
# ------------------------

# The rest of your main.py code starts here...
# e.g., root = tk.Tk()
# ...

# Import the window classes from their respective files
from src.UI.manage_products_gui import ManageProductsWindow 
from src.UI.customer_gui import CustomerWindow
from src.UI.sales_invoice_gui import SalesInvoiceWindow
from src.UI.purchase_invoice_gui import PurchaseInvoiceWindow
from src.UI.reports_gui import ReportsWindow
from src.UI.ai_sales_gui import AISalesWindow
from src.UI.login_gui import LoginScreen
from config import Colors, Fonts, WindowConfig, ACTIVE_LANGUAGE
from src.utils.translator import t, get_pack_side

class DevoDashboard:
    def __init__(self, root, role='admin'):
        self.root = root
        self.role = role
        self.logged_out = False
        self.root.title(t('dashboard_title'))
        
        geo, min_w, min_h = WindowConfig.DASHBOARD
        self.root.geometry(geo)
        self.root.minsize(min_w, min_h)
        self.root.configure(bg=Colors.BACKGROUND)
        
        # Initialize the main dashboard layout
        self.create_widgets()

    def create_widgets(self):
        """Build the main menu interface with navigation buttons."""
        
        # --- Top Header Section ---
        header_frame = tk.Frame(self.root, bg=Colors.PRIMARY_DARK, height=100)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text=t('dashboard_header'), fg=Colors.TEXT_WHITE, 
                 bg=Colors.PRIMARY_DARK, font=Fonts.HEADER_LARGE, pady=20).place(relx=0.5, rely=0.5, anchor="center")
        
        # Language switch button in header (Smaller, single word)
        tk.Button(header_frame, text=t('btn_lang_toggle'), bg=Colors.GRAY, fg=Colors.TEXT_WHITE,
                  font=("Arial", 8, "bold"), width=8, command=self.toggle_language).pack(side=get_pack_side(tk.RIGHT), padx=20, pady=25)

        # --- Main Navigation Menu Grid ---
        menu_frame = tk.Frame(self.root, bg=Colors.BACKGROUND, pady=20)
        menu_frame.pack(expand=True)

        # Standard button style for the main menu grid
        btn_style = {"font": Fonts.BODY_BOLD, "width": 22, "height": 4, 
                     "fg": Colors.TEXT_WHITE, "bd": 0}

        # Button 1: Product Management
        tk.Button(menu_frame, text=t('btn_manage_products'), bg=Colors.BLUE, **btn_style,
                  command=self.open_manage_products).grid(row=0, column=0, padx=15, pady=15)

        # Button 2: Customer & Shop Management
        tk.Button(menu_frame, text=t('btn_manage_customers'), bg=Colors.PURPLE, **btn_style,
                  command=self.open_customers).grid(row=0, column=1, padx=15, pady=15)

        # Button 3: Sales Invoicing Module
        tk.Button(menu_frame, text=t('btn_sales_invoice'), bg=Colors.GREEN, **btn_style,
                  command=self.open_sales).grid(row=1, column=0, padx=15, pady=15)

        # Button 4: Purchase Invoicing Module
        tk.Button(menu_frame, text=t('btn_purchase_invoice'), bg=Colors.RED, **btn_style,
                  command=self.open_purchases).grid(row=1, column=1, padx=15, pady=15)

        # Button 5: AI Sales Entry (NEW)
        tk.Button(menu_frame, text=t('btn_ai_sales'), bg=Colors.DARK_GRAY, **btn_style,
                  command=self.open_ai_sales).grid(row=2, column=0, padx=15, pady=15)

        # Button 6: Comprehensive Financial Reports
        report_state = tk.NORMAL if self.role == 'admin' else tk.DISABLED
        tk.Button(menu_frame, text=t('btn_financial_reports'), bg=Colors.YELLOW, 
                  **{**btn_style, "fg": Colors.TEXT_BLACK},
                  command=self.open_reports, state=report_state).grid(row=2, column=1, padx=15, pady=15)

        # --- Bottom Utility Section ---
        bottom_frame = tk.Frame(self.root, bg=Colors.BACKGROUND)
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=15)

        # Logout Button (Packed to one side)
        tk.Button(bottom_frame, text=t('btn_logout', default="🚪 Logout"), bg=Colors.RED_DARK, fg=Colors.TEXT_WHITE,
                  font=("Arial", 9, "bold"), width=15, 
                  command=self.logout).pack(side=get_pack_side(tk.LEFT), padx=10, pady=10)

        # Backup Database Button (Packed to the opposite side)
        backup_state = tk.NORMAL if self.role == 'admin' else tk.DISABLED
        tk.Button(bottom_frame, text=t('btn_backup', default="💾 Backup Database"), bg=Colors.GRAY, fg=Colors.TEXT_WHITE,
                  font=("Arial", 9, "bold"), width=20, 
                  command=self.perform_backup, state=backup_state).pack(side=get_pack_side(tk.RIGHT), padx=10, pady=10)

    # --- Utility Functions ---

    def logout(self):
        """Safely destroy the dashboard and trigger a return to the login screen."""
        confirm = messagebox.askyesno(
            t('msg_logout_title', default='Confirm Logout'),
            t('msg_logout_confirm', default='Are you sure you want to log out?')
        )
        if confirm:
            self.logged_out = True
            self.root.destroy()

    # --- Backup System ---
    
    def perform_backup(self):
        """Execute the secure database backup process."""
        from src.utils.backup_manager import create_backup
        from config import DB_NAME
        
        # Determine the full path to the database
        db_path = os.path.join(os.path.dirname(__file__), DB_NAME)
        
        success, message = create_backup(db_path)
        if success:
            messagebox.showinfo("Backup Success", f"Database backed up successfully to:\n{message}")
        else:
            messagebox.showerror("Backup Error", f"Failed to backup database:\n{message}")

    # --- Navigation Logic: Opening Sub-Windows ---

    def open_manage_products(self):
        """Open the product management window as a new top-level window."""
        new_win = tk.Toplevel(self.root)
        ManageProductsWindow(new_win)

    def open_customers(self):
        """Open the customer/shop management window."""
        new_win = tk.Toplevel(self.root)
        CustomerWindow(new_win)

    def open_sales(self):
        """Open the sales invoice interface."""
        new_win = tk.Toplevel(self.root)
        SalesInvoiceWindow(new_win)

    def open_purchases(self):
        """Open the purchase invoice interface."""
        new_win = tk.Toplevel(self.root)
        PurchaseInvoiceWindow(new_win)

    def open_reports(self):
        """Open the financial analytics and reporting window."""
        new_win = tk.Toplevel(self.root)
        ReportsWindow(new_win)

    def open_ai_sales(self):
        """Open the AI-powered WhatsApp sales entry window."""
        new_win = tk.Toplevel(self.root)
        AISalesWindow(new_win)

    def toggle_language(self):
        """Toggle active language in config.py and restart app."""
        new_lang = "en" if ACTIVE_LANGUAGE == "ar" else "ar"
        lang_display = "English" if new_lang == "en" else "العربية"
        
        # 1. Update config.py file
        config_path = os.path.join(os.path.dirname(__file__), "config.py")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            with open(config_path, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.startswith("ACTIVE_LANGUAGE ="):
                        f.write(f"ACTIVE_LANGUAGE = \"{new_lang}\"  # 'ar' for Arabic, 'en' for English\n")
                    else:
                        f.write(line)
            
            # 2. Inform and Restart
            messagebox.showinfo(t('msg_lang_changed_title'), 
                                t('msg_lang_changed_body').format(lang=lang_display))
            
            self.root.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not update language: {e}")

def run_app():
    """Main application loop to handle logging in and out cleanly."""
    while True:
        # --- LOGIN SYSTEM ---
        login_screen = LoginScreen()
        role = login_screen.run()
        
        if not role:
            # Exit if login failed or window closed
            break

        # Standard application entry point
        root = tk.Tk()
        app = DevoDashboard(root, role=role)
        root.mainloop()
        
        # If the user logged out, the loop continues and shows login screen again
        # If the user simply closed the window (X button), exit the app
        if not getattr(app, 'logged_out', False):
            break

if __name__ == "__main__":
    run_app()