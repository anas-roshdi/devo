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

# Testing the connection
if __name__ == "__main__":
    db = DatabaseManager()