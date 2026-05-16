import shutil
import os
import datetime

def create_backup(db_source_path):
    """
    Creates a secure backup of the specified database file.
    
    Args:
        db_source_path (str): The absolute or relative path to the source SQLite database.
        
    Returns:
        tuple: (True, backup_filepath) on success, or (False, error_message) on exception.
    """
    try:
        # Determine the root directory (assuming this script is in src/utils/)
        # Using os.getcwd() or dynamically finding the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        backups_dir = os.path.join(project_root, 'backups')
        
        # Check if a directory named 'backups' exists; if not, create it
        if not os.path.exists(backups_dir):
            os.makedirs(backups_dir)
            
        # Generate a timestamped filename
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"devo_backup_{timestamp}.sqlite"
        backup_filepath = os.path.join(backups_dir, filename)
        
        # Safely copy the database file
        shutil.copy2(db_source_path, backup_filepath)
        
        return True, backup_filepath
    except Exception as e:
        return False, str(e)
