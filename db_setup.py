import sqlite3
import logging

def initialize_database(db_path: str = "/app/data/processed_articles.db"):
    """Initializes the database and creates necessary tables if they do not exist."""
    logging.basicConfig(level=logging.INFO)
    logging.info("Initializing the database...")
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the 'articles' table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source TEXT,
                url TEXT,
                publish_date TEXT,
                processed_date TEXT,
                download_link TEXT,
                authors TEXT DEFAULT 'Unknown'
            )
        """)
        conn.commit()
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()