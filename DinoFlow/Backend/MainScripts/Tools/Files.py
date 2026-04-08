import os
import shutil


def read_file(path, max_size=10*1024*1024):

    if not os.path.isfile(path):
        return f"Error: file not found: {path}"
    
    try:
        file_size = os.path.getsize(path)
        if file_size > max_size:
            return f"Error: File too large ({file_size} bytes). Max size: {max_size} bytes. Use search_files with content parameter to search within the file instead."
    except Exception as e:
        return f"Error checking file size: {e}"
    
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written successfully: {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def delete_file(path):
    if not os.path.isfile(path):
        return f"Error: file not found: {path}"
    try:
        os.remove(path)
        return f"Deleted: {path}"
    except Exception as e:
        return f"Error deleting file: {e}"


def list_directory(path):
    if not os.path.isdir(path):
        return f"Error: directory not found: {path}"
    try:
        entries = os.listdir(path)
        lines = []
        for entry in sorted(entries):
            full = os.path.join(path, entry)
            tag = "[DIR] " if os.path.isdir(full) else "[FILE]"
            lines.append(f"{tag} {entry}")
        return "\n".join(lines) if lines else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"


def search_files(directory, filename="", content=""):
    if not os.path.isdir(directory):
        return f"Error: directory not found: {directory}"
    filename_pattern = filename.lower() if filename else ""
    content_pattern = content.lower() if content else ""
    matches = []
    CHUNK_SIZE = 8192
    
    try:
        for root, dirs, files in os.walk(directory):
            for f in files:
                if filename_pattern and filename_pattern not in f.lower():
                    continue
                full_path = os.path.join(root, f)
                if content_pattern:
                    try:
                        found = False
                        with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                            while True:
                                chunk = fh.read(CHUNK_SIZE)
                                if not chunk:
                                    break
                                if content_pattern.lower() in chunk.lower():
                                    found = True
                                    break
                                if len(chunk) == CHUNK_SIZE:
                                    fh.seek(fh.tell() - len(content_pattern))
                        if found:
                            matches.append(full_path)
                    except Exception:
                        pass
                else:
                    matches.append(full_path)
        return "\n".join(matches) if matches else "No matches found."
    except Exception as e:
        return f"Error searching files: {e}"


def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Error creating folder: {e}"


def move_file(source, destination):

    try:
        if not os.path.exists(source):
            return f"Error: Source not found: {source}"
        
        if os.path.isdir(destination):
            dest_path = os.path.join(destination, os.path.basename(source))
        else:
            dest_path = destination
        
        if os.path.exists(dest_path):
            return f"Error: Destination already exists: {dest_path}"
        
        parent_dir = os.path.dirname(dest_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        shutil.move(source, dest_path)
        
        item_type = "folder" if os.path.isdir(dest_path) else "file"
        return f"Moved {item_type}: {source} → {dest_path}"
        
    except PermissionError:
        return f"Error: Permission denied moving {source} to {destination}"
    except Exception as e:
        return f"Error moving file: {e}"


def copy_file(source, destination, preserve_attrs=True):

    try:
        if not os.path.exists(source):
            return f"Error: Source not found: {source}"
        
        if os.path.isdir(destination) and os.path.isfile(source):
            dest_path = os.path.join(destination, os.path.basename(source))
        else:
            dest_path = destination
        
        if os.path.exists(dest_path):
            return f"Error: Destination already exists: {dest_path}"
        
        parent_dir = os.path.dirname(dest_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        total_size = 0
        if os.path.isdir(source):
            if preserve_attrs:
                shutil.copytree(source, dest_path, copy_function=shutil.copy2)
            else:
                shutil.copytree(source, dest_path)
            item_type = "folder"
            for dirpath, dirnames, filenames in os.walk(dest_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            size_str = f" ({total_size} bytes total)"
        else:
            if preserve_attrs:
                shutil.copy2(source, dest_path)
            else:
                shutil.copy(source, dest_path)
            item_type = "file"
            size_str = f" ({os.path.getsize(dest_path)} bytes)"
        
        return f"Copied {item_type}: {source} → {dest_path}{size_str}"
        
    except PermissionError:
        return f"Error: Permission denied copying {source} to {destination}"
    except Exception as e:
        return f"Error copying file: {e}"
