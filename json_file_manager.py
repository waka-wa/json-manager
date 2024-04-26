import json
import os
import logging
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
import numpy as np

invalid_positions = set()

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_positions(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            position = data.get('position')
            if position:
                return tuple(position)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error processing file: {file_path} - {str(e)}")
    return None

def round_position(position, num_decimals, file_path):
    if position is None:
        invalid_positions.add(file_path)
        return None
    elif isinstance(position, (tuple, list)):
        return tuple(round(float(x), num_decimals) for x in position)
    else:
        invalid_positions.add(file_path)
        logging.warning(f"Invalid position format: {position} in file: {file_path}")
        return None

def update_name_field(file_path):
    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)

    try:
        with open(file_path, 'r+') as f:
            data = json.load(f)
            data['name'] = name
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error updating name field in file: {file_path} - {str(e)}")

def remove_description(file_path):
    try:
        with open(file_path, 'r+') as f:
            data = json.load(f)
            if 'description' in data:
                del data['description']  # Remove 'description'
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                print(f"Description removed from file: {file_path}")  # Conditional print
            else:
                print(f"No description found in file: {file_path}")  # Conditional print
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error processing file: {file_path} - {str(e)}")

def clear_name_value(file_path):
    try:
        with open(file_path, 'r+') as f:
            data = json.load(f)
            if 'name' in data:
                data['name'] = ''  # Set to an empty string
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error processing file: {file_path} - {str(e)}")

def round_positions_in_file(file_path, num_decimals):
    try:
        with open(file_path, 'r+') as f:
            data = json.load(f)
            position = data.get('position')
            if position:
                rounded_position = round_position(position, num_decimals, file_path)
                if rounded_position is not None:
                    data['position'] = list(rounded_position)
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error processing file: {file_path} - {str(e)}")

def find_duplicate_and_near_duplicate_positions(directory_path, duplicates, near_duplicates, file_pattern='*.json', ignore_empty=False, num_decimals=None, update_name=False, remove_description=False, clear_name=False, round_positions=False, find_near_duplicates=False, tolerance=1, progress_callback=None):
    position_to_files = defaultdict(list)
    duplicate_positions = set()
    near_duplicate_positions = set()

    file_list = []
    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(file_pattern.split('*')[-1]):
                file_path = os.path.join(root, filename)
                file_list.append(file_path)

    total_files = len(file_list)
    for index, file_path in enumerate(file_list, start=1):
        try:
            position = extract_positions(file_path)
            if position or not ignore_empty:
                if round_positions:
                    round_positions_in_file(file_path, num_decimals)
                rounded_position = round_position(position, num_decimals, file_path) if num_decimals is not None else position
                if rounded_position is not None:
                    if rounded_position in position_to_files:
                        position_to_files[rounded_position].append(file_path)
                        duplicate_positions.add(rounded_position)  # Update the duplicate_positions set directly
                        duplicates.add(file_path)
                    elif find_near_duplicates:
                        for existing_position in position_to_files:
                            if np.all(np.abs(np.array(rounded_position) - np.array(existing_position)) <= tolerance):
                                position_to_files[existing_position].append(file_path)
                            near_duplicate_positions.add(existing_position)  # Update the near_duplicate_positions set directly
                            near_duplicates.add(file_path)
                        else:
                            position_to_files[rounded_position] = [file_path]
                    else:
                        position_to_files[rounded_position] = [file_path]
                    if update_name:
                        update_name_field(file_path)
                    if remove_description:
                        remove_description(file_path)
                    if clear_name:
                        clear_name_value(file_path)
        except Exception as e:
            logging.error(f"Error processing file: {file_path} - {str(e)}")

        if progress_callback:
            progress_callback(index, total_files, file_path)

    return position_to_files, duplicates, near_duplicates, invalid_positions

def save_preferences(preferences):
    preferences_file = Path(script_dir, 'preferences.json')
    with open(preferences_file, 'w') as f:
        json.dump(preferences, f, indent=4)

def load_preferences():
    preferences_file = Path(script_dir, 'preferences.json')
    if preferences_file.exists():
        try:
            with open(preferences_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error loading preferences: {str(e)}. Using default settings.")
    return None  # Preferences file either doesn't exist or couldn't be loaded

script_dir = Path(__file__).parent.resolve()