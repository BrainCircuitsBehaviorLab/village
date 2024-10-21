import os
import re


def find_python_files(directory):
    """Recursively find all Python files in the given directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def extract_imports(file_path):
    """Extract imported modules from a Python file."""
    imports = set()
    with open(file_path, "r") as file:
        for line in file:
            # Match both 'import module' and 'from module import ...'
            match = re.match(r"from (\S+) import |import (\S+)", line)
            if match:
                module = match.group(1) or match.group(2)
                # Take only the base package name
                base_module = module.split(".")[0]
                imports.add(base_module)
    return imports


def update_autodoc_mock_imports(project_directory, conf_file) -> None:
    """Update the autodoc_mock_imports list in conf.py with imports
    from all Python files."""
    all_imports = set()
    for python_file in find_python_files(project_directory):
        all_imports.update(extract_imports(python_file))

    # Convert the set to a sorted list
    imports_list = sorted(list(all_imports))

    # Now, you would update the conf.py file. This is a simplified approach:
    with open(conf_file, "r") as file:
        lines = file.readlines()

    with open(conf_file, "w") as file:
        for line in lines:
            if line.strip().startswith("autodoc_mock_imports"):
                file.write(f"autodoc_mock_imports: list = {imports_list}\n")
            else:
                file.write(line)


# Example usage
project_directory = "/home/pi/village"
conf_file = "/home/pi/village/docs/source/conf.py"
update_autodoc_mock_imports(project_directory, conf_file)
