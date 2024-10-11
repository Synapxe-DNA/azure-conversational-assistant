import ast

import pytest
from simple_term_menu import TerminalMenu


def main():
    selected_type = get_test_type_option().lower()
    selected_file = get_test_file_option().lower()

    if selected_file != "all":
        file_path = f"backend/test/{selected_file}_test.py"
        test_functions = extract_test_functions(file_path)
        selected_function = get_test_function(test_functions)

        full_path = f"{file_path}::{selected_function}" if selected_function.lower() != "all" else file_path
        print(f"Running {selected_function} test function(s) in {selected_file} for {selected_type} backend")
    else:
        full_path = "backend/test/"  # Run all tests and functions
        print(f"Running all tests on {selected_type} backend")

    pytest_args = (
        ["-v", "-s", "--local", full_path, "-n", "auto"]
        if selected_type == "local"
        else ["-v", "-s", full_path, "-n", "auto"]
    )
    pytest.main(pytest_args)


def extract_test_functions(file_path):
    """
    Extract all test functions from the selected file

    Args:
        file_path (str): The file path of the selected test file

    Returns:
        list[str]: A list of test functions from the selected file
    """
    with open(file_path) as file:
        tree = ast.parse(file.read())

    test_functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_"):
            test_functions.append(node.name)

    return test_functions


def get_test_type_option():
    """
    Function to ask the user to select the backend they want to test

    Returns:
        str: The selected backend by the user
    """
    options = ["Local", "Deployed"]
    terminal_menu = TerminalMenu(
        options, title="Select the backend you want to test", menu_highlight_style=("bg_blue", "bold")
    )
    menu_entry_index = terminal_menu.show()
    return options[menu_entry_index]


def get_test_file_option():
    """
    Function to ask the user to select the test they want to test

    Returns:
        str: The selected test by the user
    """
    options = ["All", "Chat", "Feedback", "Speech", "Transcription", "Voice"]
    terminal_menu = TerminalMenu(
        options, title="Select the test you want to run", menu_highlight_style=("bg_blue", "bold")
    )
    menu_entry_index = terminal_menu.show()
    return options[menu_entry_index]


def get_test_function(test_functions: list[str]):
    """
    Function to ask the user to select the test function they want to test

    Args:
        test_functions (list[str]): A list of test functions from the selected file

    Returns:
        str: The selected test function by the user
    """
    options = ["All"] + test_functions
    terminal_menu = TerminalMenu(
        options, title="Select the test function you want to run", menu_highlight_style=("bg_blue", "bold")
    )
    menu_entry_index = terminal_menu.show()
    return options[menu_entry_index]


if __name__ == "__main__":
    main()
