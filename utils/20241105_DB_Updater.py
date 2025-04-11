import sqlite3
import logging
import os

# Set up logging for feedback
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Update the path to your database file
DATABASE_PATH = "data/processed_articles.db"  # Update to the correct path

def add_text_content_column():
    """Adds a 'text_content' column to the 'articles' table if it doesn't already exist."""
    if not os.path.exists(DATABASE_PATH):
        logging.error(f"Database file not found at {DATABASE_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if column already exists by attempting to query it
        cursor.execute("PRAGMA table_info(articles);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'text_content' not in columns:
            # Add the `text_content` column
            cursor.execute("ALTER TABLE articles ADD COLUMN text_content TEXT")
            conn.commit()
            logging.info("Column 'text_content' added to 'articles' table.")
        else:
            logging.info("Column 'text_content' already exists in 'articles' table. Skipping.")
    except sqlite3.Error as e:
        logging.error(f"An error occurred while adding the 'text_content' column: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def create_listens_table():
    """Creates the 'listens' table for tracking audio listens if it doesn't already exist."""
    if not os.path.exists(DATABASE_PATH):
        logging.error(f"Database file not found at {DATABASE_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create the `listens` table if it doesn’t already exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                listen_date TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        conn.commit()
        logging.info("Table 'listens' created successfully.")
    except sqlite3.Error as e:
        logging.error(f"An error occurred while creating the 'listens' table: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    logging.info("Starting database update...")
    add_text_content_column()
    create_listens_table()
    logging.info("Database update completed successfully.")

if __name__ == "__main__":
    main()
