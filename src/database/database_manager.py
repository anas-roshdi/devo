import sqlite3

class DatabaseManager:
    def __init__(self, db_name="devo_business.sqlite"):
        self.db_name = db_name
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
        """Initialize the full ERP database schema (Task 7)."""
        
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

    # --- Helper Methods for the new structure ---
    def get_products_by_type(self, p_type):
        return self.fetch_data("SELECT * FROM products WHERE product_type = ? OR product_type = 'both'", (p_type,))

    def get_all_customers(self):
        return self.fetch_data("SELECT * FROM customers") 
      
    def get_all_products(self):
        """Fetch all products from the products table."""
        query = "SELECT * FROM products"
        cursor = self.execute_query(query)
        return cursor.fetchall()
    
    def add_product(self, name, category, price, p_type, size):
        """Insert a new product record into the database."""
        query = """
            INSERT INTO products (name, category, unit_price, product_type, size)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (name, category, price, p_type, size)
        self.execute_query(query, params)

    def get_top_products_by_date(self, start_date, end_date):
        """Fetches the top 5 products based on total quantity sold within a date range."""
        query = """
            SELECT p.name, SUM(si.quantity) as total_qty
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sale_invoices i ON si.invoice_id = i.invoice_id
            WHERE i.sale_date BETWEEN ? AND ?
            GROUP BY p.name
            ORDER BY total_qty DESC
            LIMIT 5
        """
        # We use fetch_data because it already returns cursor.fetchall()
        return self.fetch_data(query, (start_date, end_date))

    def get_top_products_dynamic(self, start_date, end_date, group_fields, store_name, limit_num):
        """
        Fetches top products dynamically with store filter and custom limit.
        """
        if not group_fields:
            group_fields = ['name'] 
            
        select_cols = ", ".join([f"p.{field}" for field in group_fields])
        group_cols = ", ".join([f"p.{field}" for field in group_fields])
        
        # Base query joining customers (Assuming customers represent stores/entities)
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

# Testing the connection
if __name__ == "__main__":
    db = DatabaseManager()
    print(db.get_all_customers())