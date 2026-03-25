import os
import json

class IOManager:
    """Handles all file and folder operations for the SDLC flow."""
    
    @staticmethod
    def create_project_structure(project_name):
        """Creates the hierarchical folder structure for a new project."""
        target_path = os.path.join("projects", project_name)
        sub_folders = ["tasks", "analysis", "codes", "tests", "output"]
        
        #duzeltme exist_ok=True ile if kontrolü kalktı
        os.makedirs(target_path, exist_ok=True)
            
        # Create sub-folders (tasks, codes etc.)
        for folder in sub_folders:
            folder_path = os.path.join(target_path, folder)
            os.makedirs(folder_path, exist_ok=True)
        
        return target_path


    @staticmethod
    def read_file(path):
        if not os.path.exists(path):
            return ""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def write_file(path, content):
        os.makedirs(os.path.dirname(path), exist_ok=True) #klasor yoksa otomatik olusturur.
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def save_json(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True) #klasor yoksa otomatik olusturur.
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)