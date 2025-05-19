import os
import sqlite3
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def reset_database():
    """Reset the database by deleting it and recreating from scratch"""
    # Check if database exists
    if os.path.exists(DATABASE_PATH):
        confirm = input(f"Are you sure you want to delete the existing database at {DATABASE_PATH}? (y/n): ")
        if confirm.lower() != 'y':
            print("Database reset cancelled.")
            return False
        
        try:
            # Delete the database file
            os.remove(DATABASE_PATH)
            logger.info(f"Existing database deleted: {DATABASE_PATH}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete database: {e}")
            return False
    else:
        logger.info("No existing database found.")
        return True

def cleanup_orphaned_files():
    """Clean up orphaned files in uploads directory that are not referenced in the database"""
    if not os.path.exists(DATABASE_PATH):
        logger.warning("Database doesn't exist, cannot clean up orphaned files.")
        return
    
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    if not os.path.exists(uploads_dir):
        logger.info("Uploads directory doesn't exist.")
        return
    
    try:
        # Get all files in uploads directory
        all_files = [os.path.join(uploads_dir, f) for f in os.listdir(uploads_dir) 
                    if os.path.isfile(os.path.join(uploads_dir, f))]
        
        # Get files referenced in database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM documents")
        referenced_files = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Find orphaned files
        orphaned_files = [f for f in all_files if f not in referenced_files]
        
        if not orphaned_files:
            logger.info("No orphaned files found.")
            return
        
        # Ask for confirmation
        print(f"Found {len(orphaned_files)} orphaned files.")
        for f in orphaned_files[:5]:  # Show first 5 as examples
            print(f"  - {os.path.basename(f)}")
        
        if len(orphaned_files) > 5:
            print(f"  ...and {len(orphaned_files) - 5} more.")
        
        confirm = input("Do you want to delete these orphaned files? (y/n): ")
        if confirm.lower() != 'y':
            print("Cleanup cancelled.")
            return
        
        # Delete orphaned files
        for f in orphaned_files:
            try:
                os.remove(f)
                logger.info(f"Deleted orphaned file: {f}")
            except Exception as e:
                logger.error(f"Failed to delete {f}: {e}")
        
        print(f"Cleaned up {len(orphaned_files)} orphaned files.")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    print("Document Summarizer Database Utility")
    print("-----------------------------------")
    print("1. Reset database (delete and recreate)")
    print("2. Clean up orphaned files")
    print("3. Run both operations")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        if reset_database():
            print("Now run 'python setup.py' to initialize the database.")
    elif choice == '2':
        cleanup_orphaned_files()
    elif choice == '3':
        if reset_database():
            print("Database reset. Now initializing...")
            # Import and run setup
            from setup import init_db
            init_db()
            cleanup_orphaned_files()
    elif choice == '4':
        sys.exit(0)
    else:
        print("Invalid choice. Exiting.")