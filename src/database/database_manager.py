import sqlite3
from config import DB_NAME

class DatabaseManager:
    def __init__(self, db_name=None):
        self.db_name = db_name or DB_NAME
        self.create_tables()

    def connect(self):
        """Establish a connection to the SQLite database."""
        return sqlite3.connect(self.db_name)

    def execute_query(self, query, params=()):
        """Execute a single query (Insert, Update, Delete)."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def fetch_data(self, query, params=()):
        """Fetch data from the database (Select)."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def create_tables(self):
        """Initialize the full ERP database schema."""
        
        # 1. Products Table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                unit_price FLOAT,
                product_type TEXT, -- 'sellable', 'buyable', 'both'
                size TEXT
            )
        ''')

        # 2. Customers Table (For Wholesale and Retail)
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. Sale Invoices (Header)
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS sale_invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                sale_date DATE,
                total_amount FLOAT,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')

        # 4. Sale Items (Details - Multi-item support)
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS sale_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                unit_price_sold FLOAT, -- Flexible pricing for shops
                subtotal FLOAT,
                FOREIGN KEY (invoice_id) REFERENCES sale_invoices (invoice_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')

        # 5. Purchase Invoices (Header)
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS purchase_invoices (
                purchase_invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_name TEXT,
                purchase_date DATE,
                total_amount FLOAT
            )
        ''')

        # 6. Purchase Items (Details)
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS purchase_items (
                p_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_invoice_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                unit_cost_price FLOAT,
                subtotal FLOAT,
                FOREIGN KEY (purchase_invoice_id) REFERENCES purchase_invoices (purchase_invoice_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')
        
        # Insert a default 'General Customer' if table is empty
        check_customer = self.fetch_data("SELECT * FROM customers WHERE name='General Customer'")
        if not check_customer:
            self.execute_query("INSERT INTO customers (name) VALUES ('General Customer')")

    # =========================================================
    # PRODUCT OPERATIONS
    # =========================================================

    def get_all_products(self):
        """Fetch all products from the products table."""
        return self.fetch_data("SELECT * FROM products")

    def get_products_by_type(self, p_type):
        """Fetch products that match the given type or 'both'."""
        return self.fetch_data(
            "SELECT * FROM products WHERE product_type = ? OR product_type = 'both'", (p_type,)
        )

    def get_products_for_combo(self, product_type):
        """
        Fetch products for combobox display, filtered by type.
        Returns list of (product_id, name, unit_price, category, size).
        """
        return self.fetch_data(
            """SELECT product_id, name, unit_price, category, size 
               FROM products 
               WHERE product_type IN (?, 'both') 
               ORDER BY name ASC""",
            (product_type,)
        )

    def add_product(self, name, category, price, p_type, size):
        """Insert a new product record into the database."""
        self.execute_query(
            "INSERT INTO products (name, category, unit_price, product_type, size) VALUES (?, ?, ?, ?, ?)",
            (name, category, price, p_type, size)
        )

    def update_product(self, product_id, name, category, price, p_type, size):
        """Update an existing product's information."""
        self.execute_query(
            "UPDATE products SET name=?, category=?, unit_price=?, product_type=?, size=? WHERE product_id=?",
            (name, category, price, p_type, size, product_id)
        )

    def delete_product(self, product_id):
        """Permanently remove a product from the database."""
        self.execute_query("DELETE FROM products WHERE product_id=?", (product_id,))

    # =========================================================
    # CUSTOMER OPERATIONS
    # =========================================================

    def get_all_customers(self):
        """Fetch all customer records."""
        return self.fetch_data("SELECT * FROM customers")

    def add_customer(self, name, phone, address):
        """Insert a new customer record."""
        self.execute_query(
            "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
            (name, phone, address)
        )

    def update_customer(self, customer_id, name, phone, address):
        """Update an existing customer's information."""
        self.execute_query(
            "UPDATE customers SET name=?, phone=?, address=? WHERE customer_id=?",
            (name, phone, address, customer_id)
        )

    def delete_customer(self, customer_id):
        """Remove a customer from the database."""
        self.execute_query("DELETE FROM customers WHERE customer_id=?", (customer_id,))

    # =========================================================
    # SALE INVOICE OPERATIONS
    # =========================================================

    def save_sale_invoice(self, customer_id, date_str, total_amount, items):
        """
        Save a complete sale invoice (header + detail items) in one transaction.
        
        Args:
            customer_id: ID of the customer.
            date_str: Sale date string (YYYY-MM-DD).
            total_amount: Total invoice amount.
            items: List of dicts with keys: 'id', 'qty', 'price', 'subtotal'.
        
        Returns:
            The generated invoice_id.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            # Insert header
            cursor.execute(
                "INSERT INTO sale_invoices (customer_id, sale_date, total_amount) VALUES (?, ?, ?)",
                (customer_id, date_str, total_amount)
            )
            invoice_id = cursor.lastrowid
            # Insert detail items
            for item in items:
                cursor.execute(
                    """INSERT INTO sale_items (invoice_id, product_id, quantity, unit_price_sold, subtotal) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (invoice_id, item['id'], item['qty'], item['price'], item['subtotal'])
                )
            conn.commit()
            return invoice_id

    def get_last_sale_price(self, customer_id, product_id):
        """
        Fetch the most recent selling price for a specific customer and product.
        Returns the price as float, or None if no previous sale exists.
        """
        result = self.fetch_data(
            """SELECT si.unit_price_sold 
               FROM sale_items si
               JOIN sale_invoices s ON si.invoice_id = s.invoice_id
               WHERE s.customer_id = ? AND si.product_id = ?
               ORDER BY s.sale_date DESC, s.invoice_id DESC
               LIMIT 1""",
            (customer_id, product_id)
        )
        return result[0][0] if result else None

    # =========================================================
    # PURCHASE INVOICE OPERATIONS
    # =========================================================

    def save_purchase_invoice(self, supplier_name, date_str, total_amount, items):
        """
        Save a complete purchase invoice (header + detail items) in one transaction.
        
        Args:
            supplier_name: Name of the supplier.
            date_str: Purchase date string (YYYY-MM-DD).
            total_amount: Total invoice amount.
            items: List of dicts with keys: 'id', 'qty', 'cost', 'subtotal'.
        
        Returns:
            The generated purchase_invoice_id.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            # Insert header
            cursor.execute(
                "INSERT INTO purchase_invoices (supplier_name, purchase_date, total_amount) VALUES (?, ?, ?)",
                (supplier_name, date_str, total_amount)
            )
            p_invoice_id = cursor.lastrowid
            # Insert detail items
            for item in items:
                cursor.execute(
                    """INSERT INTO purchase_items (purchase_invoice_id, product_id, quantity, unit_cost_price, subtotal) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (p_invoice_id, item['id'], item['qty'], item['cost'], item['subtotal'])
                )
            conn.commit()
            return p_invoice_id

    # =========================================================
    # REPORT & ANALYTICS QUERIES
    # =========================================================

    def get_financial_report(self, customer_name, start_date, end_date):
        """
        Fetch combined sales and purchase records for financial reporting.
        
        Args:
            customer_name: Customer filter ("All Customers" for global view).
            start_date: Start date string (YYYY-MM-DD).
            end_date: End date string (YYYY-MM-DD).
        
        Returns:
            Tuple of (sales_data, purchases_data) where each is a list of tuples.
        """
        # Fetch sales
        s_query = """SELECT sale_date, 'SALE', customers.name, total_amount 
                     FROM sale_invoices 
                     JOIN customers ON sale_invoices.customer_id = customers.customer_id 
                     WHERE sale_date BETWEEN ? AND ?"""
        s_params = [start_date, end_date]
        
        if customer_name != "All Customers":
            s_query += " AND customers.name = ?"
            s_params.append(customer_name)
        
        sales = self.fetch_data(s_query, tuple(s_params))
        
        # Fetch purchases (only for global/all customers view)
        purchases = []
        if customer_name == "All Customers":
            p_query = """SELECT purchase_date, 'PURCHASE', supplier_name, total_amount 
                         FROM purchase_invoices 
                         WHERE purchase_date BETWEEN ? AND ?"""
            purchases = self.fetch_data(p_query, (start_date, end_date))
        
        return sales, purchases

    def get_top_products_by_date(self, start_date, end_date):
        """Fetches the top 5 products based on total quantity sold within a date range."""
        return self.fetch_data(
            """SELECT p.name, SUM(si.quantity) as total_qty
               FROM sale_items si
               JOIN products p ON si.product_id = p.product_id
               JOIN sale_invoices i ON si.invoice_id = i.invoice_id
               WHERE i.sale_date BETWEEN ? AND ?
               GROUP BY p.name
               ORDER BY total_qty DESC
               LIMIT 5""",
            (start_date, end_date)
        )

    def get_top_products_dynamic(self, start_date, end_date, group_fields, store_name, limit_num):
        """
        Fetches top products dynamically with store filter and custom limit.
        """
        if not group_fields:
            group_fields = ['name'] 
            
        select_cols = ", ".join([f"p.{field}" for field in group_fields])
        group_cols = ", ".join([f"p.{field}" for field in group_fields])
        
        # Base query joining customers
        query = f"""
            SELECT {select_cols}, SUM(si.quantity) as total_qty
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sale_invoices i ON si.invoice_id = i.invoice_id
            JOIN customers c ON i.customer_id = c.customer_id
            WHERE i.sale_date BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        
        # Add store filter if a specific store is selected
        if store_name and store_name != "All Customers": 
            query += " AND c.name = ?"
            params.append(store_name)
            
        # Add GROUP BY, ORDER BY, and dynamic LIMIT
        query += f"""
            GROUP BY {group_cols}
            ORDER BY total_qty DESC
            LIMIT ?
        """
        params.append(limit_num)
        
        return self.fetch_data(query, tuple(params))

    def get_customer_performance(self, start_date, end_date, limit_num=10):
        """
        Fetch customer performance data for VIP/loyalty analysis.
        
        Returns list of tuples:
            (customer_name, total_invoices, total_units, total_amount)
        Sorted by total_amount descending, excluding 'General Customer'.
        """
        return self.fetch_data(
            """SELECT c.name,
                      COUNT(DISTINCT s.invoice_id) as total_invoices,
                      COALESCE(SUM(si.quantity), 0) as total_units,
                      COALESCE(SUM(si.subtotal), 0) as total_amount
               FROM customers c
               JOIN sale_invoices s ON c.customer_id = s.customer_id
               JOIN sale_items si ON s.invoice_id = si.invoice_id
               WHERE s.sale_date BETWEEN ? AND ?
                 AND c.name != 'General Customer'
               GROUP BY c.customer_id, c.name
               ORDER BY total_amount DESC
               LIMIT ?""",
            (start_date, end_date, limit_num)
        )


# Testing the connection
if __name__ == "__main__":
    db = DatabaseManager()
    print(db.get_all_customers())