"""
Devo Business Management System - Central Configuration File
=============================================================
All shared constants (colors, fonts, window sizes, database settings)
are defined here for easy maintenance and consistency across the app.
"""

# =====================================================
# DATABASE CONFIGURATION
# =====================================================
DB_NAME = "devo_business.sqlite"


# =====================================================
# COLOR PALETTE
# =====================================================
class Colors:
    """Centralized color constants used throughout the application UI."""
    
    # --- Primary & Background ---
    PRIMARY_DARK = "#2c3e50"       # Main header / dark elements
    BACKGROUND = "#f0f3f5"         # Main window background
    
    # --- Accent Colors ---
    BLUE = "#3498db"               # Products / Info actions
    BLUE_DARK = "#2980b9"          # Update / secondary blue actions
    PURPLE = "#9b59b6"             # Customers module
    GREEN = "#2ecc71"              # Sales / Success
    GREEN_DARK = "#27ae60"         # Add / Confirm actions
    RED = "#e74c3c"                # Purchases / Danger
    RED_DARK = "#c0392b"           # Delete actions
    YELLOW = "#f1c40f"             # Reports / Warnings
    ORANGE = "#f39c12"             # Remove / secondary actions
    GRAY = "#7f8c8d"               # Clear / neutral actions
    DARK_GRAY = "#34495e"          # Dark info cards
    
    # --- Text Colors ---
    TEXT_WHITE = "white"
    TEXT_BLACK = "black"
    TEXT_DARK_GREEN = "darkgreen"
    TEXT_BLUE = "blue"


# =====================================================
# FONT DEFINITIONS
# =====================================================
class Fonts:
    """Centralized font definitions used throughout the application UI."""
    
    # --- Headers ---
    HEADER_LARGE = ("Helvetica", 22, "bold")    # Main dashboard title
    HEADER_MEDIUM = ("Arial", 20, "bold")       # Window titles
    HEADER_SMALL = ("Arial", 16, "bold")        # Total labels
    
    # --- Body ---
    BODY = ("Arial", 11)
    BODY_BOLD = ("Arial", 11, "bold")
    BODY_ITALIC = ("Arial", 12, "italic")
    
    # --- Buttons ---
    BTN_LARGE = ("Arial", 12, "bold")
    BTN_MEDIUM = ("Arial", 10, "bold")
    BTN_SMALL = ("Arial", 9, "bold")
    
    # --- Cards ---
    CARD = ("Arial", 11, "bold")
    
    # --- Labels ---
    LABEL_FRAME = ("Arial", 10, "bold")
    TOTAL_LABEL = ("Arial", 14, "bold")


# =====================================================
# WINDOW CONFIGURATIONS
# =====================================================
class WindowConfig:
    """Default window sizes and minimum sizes for each module."""
    
    # Format: (geometry_string, min_width, min_height)
    DASHBOARD = ("800x550", 700, 450)
    PRODUCTS = ("1000x750", 800, 600)
    CUSTOMERS = ("700x500", 600, 400)
    SALES_INVOICE = ("900x600", 750, 500)
    PURCHASE_INVOICE = ("900x600", 750, 500)
    REPORTS = ("850x650", 750, 550)


# =====================================================
# DEFAULT VALUES
# =====================================================
DEFAULT_CUSTOMER = "General Customer"
ALL_CUSTOMERS_LABEL = "All Customers"
UNKNOWN_SUPPLIER = "Unknown Supplier"
DATE_FORMAT = "%Y-%m-%d"

# Product types
PRODUCT_TYPES = ["sellable", "buyable", "both"]
DEFAULT_PRODUCT_TYPE_INDEX = 2  # 'both'

# Analysis modes
ANALYSIS_MODES = ("Profit Margin", "Top Products")
GROUP_BY_OPTIONS = ("Weekly", "Monthly")
DEFAULT_TOP_LIMIT = 5
DEFAULT_FORECAST_PERIODS = 3
