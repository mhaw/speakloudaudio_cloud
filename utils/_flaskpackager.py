from pathlib import Path
import fnmatch
import datetime

# Define root directory and default output file
FLASK_APP_DIR = Path.cwd()
APP_DIR = FLASK_APP_DIR / "app"
DEFAULT_OUTPUT_FILE = "flask_app_summary.txt"
FILE_SIZE_LIMIT = 500 * 1024  # 500 KB

# Define patterns and corresponding directories
PATTERNS = {
    "Python Files": ("*.py", APP_DIR),
    "HTML Templates": ("*.html", APP_DIR / "templates"),
    "CSS Files": ("*.css", APP_DIR / "static"),
    "JavaScript Files": ("*.js", APP_DIR / "static"),
    "Other Static Files": (("*.png", "*.jpg", "*.jpeg", "*.svg", "*.gif"), APP_DIR / "static"),
}

# Configuration files to include if present
CONFIG_FILES = ["config.py", "Dockerfile", "docker-compose.yml", ".env"]

def read_file_content(file_path):
    """Read file content with size check and error handling."""
    try:
        if file_path.stat().st_size > FILE_SIZE_LIMIT:
            return f"[File exceeds {FILE_SIZE_LIMIT / 1024:.1f} KB and was skipped]\n"
        
        with file_path.open("r", encoding="utf-8") as file:
            return file.read()
    except (FileNotFoundError, PermissionError) as e:
        return f"[Error reading file: {str(e)}]\n"

def write_header(output_file, header):
    output_file.write(f"\n{'='*20} {header} {'='*20}\n")

def iterate_files(patterns, directory):
    """Yield files matching pattern(s) within a directory."""
    if isinstance(patterns, tuple):
        for pattern in patterns:
            yield from iterate_files(pattern, directory)
    else:
        for path in directory.rglob(patterns):
            yield path

def select_patterns():
    """Interactive menu to select which file types to include."""
    print("Select file types to include in the package:")
    selected_patterns = {}
    for idx, (key, value) in enumerate(PATTERNS.items(), start=1):
        print(f"{idx}. {key}")
    print(f"{len(PATTERNS) + 1}. All")

    choices = input("Enter numbers (comma-separated): ").split(",")
    try:
        choices = [int(choice.strip()) for choice in choices]
        if len(PATTERNS) + 1 in choices:  # Include all if "All" is selected
            return PATTERNS

        for choice in choices:
            if 1 <= choice <= len(PATTERNS):
                key = list(PATTERNS.keys())[choice - 1]
                selected_patterns[key] = PATTERNS[key]

    except ValueError:
        print("Invalid input. Defaulting to all file types.")
        return PATTERNS

    return selected_patterns

def collect_app_content(output_file_name):
    patterns = select_patterns()
    output_file_path = FLASK_APP_DIR / output_file_name
    
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        # Write dynamic header
        header = (
            "This package includes Python files, templates, and configuration files from a Flask app.\n"
            f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "Key files: app.py, routes.py. Focus: Debugging template rendering issues.\n"
        )
        output_file.write(header)

        # Collect specific file patterns
        for section, (pattern, directory) in patterns.items():
            write_header(output_file, section)
            for file_path in iterate_files(pattern, directory):
                output_file.write(f"\n[File: {file_path}]\n")
                output_file.write(read_file_content(file_path))

        # Collect configuration files if they exist
        write_header(output_file, "Configuration Files")
        for config_file in CONFIG_FILES:
            config_path = FLASK_APP_DIR / config_file
            if config_path.exists():
                output_file.write(f"\n[File: {config_path}]\n")
                output_file.write(read_file_content(config_path))

if __name__ == "__main__":
    output_file_name = input(f"Enter output file name (default: {DEFAULT_OUTPUT_FILE}): ").strip()
    if not output_file_name:
        output_file_name = DEFAULT_OUTPUT_FILE

    collect_app_content(output_file_name)
    print(f"Content collected in '{output_file_name}'")
