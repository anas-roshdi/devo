import sqlite3

class DatabaseManager:
    """
    Handles all database interactions for the devo management system.
    Supports creating tables and executing SQL queries.
    """
    def __init__(self, db_name="devo_database.sqlite"):
        self.db_name = db_name
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Establish a connection to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.db_name)
            print(f"Connected to {self.db_name} successfully.")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def create_tables(self):
        """Initialize the database schema based on our UML design."""
        cursor = self.connection.cursor()
        
        # 1. Create Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                unit_price REAL,
                product_type TEXT, -- Values: 'sellable', 'buyable', 'both'       
                size TEXT
            )
        ''')

        # 2. Create Sales table (MERN-style logic for transactions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER,
                total_price REAL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')

        # 3. Create Purchases table (Crucial for calculating profit)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER,
                cost_price REAL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')
        
        self.connection.commit()
        print("Database tables initialized successfully.")

    def execute_query(self, query, params=()):
        """Execute an action query (INSERT, UPDATE, DELETE)."""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()

    def add_product(self, name, category, unit_price,product_type, size):
        """Add a new product to the inventory."""
        query = "INSERT INTO products (name, category, unit_price,product_type, size) VALUES (?, ?, ?, ?)"
        self.execute_query(query, (name, category, unit_price, product_type, size))
        print(f"Product '{name}' added successfully.")

    def get_all_products(self):
        """Fetch all products from the database for display."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM products")
        return cursor.fetchall()
    
    def get_products_by_type(self, p_type):
        """Fetch products filtered by their type (useful for GUI lists)."""
        cursor = self.connection.cursor()
        query = "SELECT * FROM products WHERE product_type = ? OR product_type = 'both'"
        cursor.execute(query, (p_type,))
        return cursor.fetchall()

    def update_product_price(self, product_id, new_price):
        """Update the price of an existing product."""
        query = "UPDATE products SET unit_price = ? WHERE product_id = ?"
        self.execute_query(query, (new_price, product_id))

    def update_product_name(self, product_id, new_name):
        """Update the price of an existing product."""
        query = "UPDATE products SET name = ? WHERE product_id = ?"
        self.execute_query(query, (new_name, product_id))

    def update_product_category(self, product_id, new_category):
        """Update the price of an existing product."""
        query = "UPDATE products SET category = ? WHERE product_id = ?"
        self.execute_query(query, (new_category, product_id))

    def update_product_size(self, product_id, new_size):
        """Update the price of an existing product."""
        query = "UPDATE products SET size = ? WHERE product_id = ?"
        self.execute_query(query, (new_size, product_id))            

    def delete_product(self, product_id):
        """Remove a product from the database."""
        query = "DELETE FROM products WHERE product_id = ?"
        self.execute_query(query, (product_id,))    

    def add_sale(self, product_id, quantity, total_price):
        """Record a new sale transaction in the database."""
        query = "INSERT INTO sales (product_id, quantity, total_price) VALUES (?, ?, ?)"
        self.execute_query(query, (product_id, quantity, total_price))

    def add_purchase(self, product_id, quantity, cost_price):
        """Record a new supply purchase in the database."""
        query = "INSERT INTO purchases (product_id, quantity, cost_price) VALUES (?, ?, ?)"
        self.execute_query(query, (product_id, quantity, cost_price))    

# Testing the connection
if __name__ == "__main__":
    db = DatabaseManager()