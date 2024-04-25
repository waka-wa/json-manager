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


def find_duplicate_and_near_duplicate_positions(directory_path, file_pattern='*.json', ignore_empty=False, num_decimals=None, save_rounded=False, update_name=False, remove_description=False, clear_name=False, find_near_duplicates=False, tolerance=1):
    position_to_files = defaultdict(list)
    duplicate_positions = set()
    near_duplicate_positions = set()

    file_list = []
    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(file_pattern.split('*')[-1]):
                file_path = os.path.join(root, filename)
                file_list.append(file_path)

    for file_path in tqdm(file_list, unit='file'):
        try:
            position = extract_positions(file_path)
            if position or not ignore_empty:
                rounded_position = round_position(position, num_decimals, file_path) if num_decimals is not None else position
                if rounded_position is not None:
                    if rounded_position in position_to_files:
                        position_to_files[rounded_position].append(file_path)
                        duplicate_positions.add(rounded_position)
                    elif find_near_duplicates:
                        for existing_position in position_to_files:
                            if np.all(np.abs(np.array(rounded_position) - np.array(existing_position)) <= tolerance):
                                position_to_files[existing_position].append(file_path)
                                near_duplicate_positions.add(existing_position)
                                break
                        else:
                            position_to_files[rounded_position] = [file_path]
                    else:
                        position_to_files[rounded_position] = [file_path]
                    if save_rounded:
                        with open(file_path, 'r+') as f:
                            data = json.load(f)
                            data['position'] = list(rounded_position)
                            f.seek(0)
                            json.dump(data, f, indent=4)
                            f.truncate()
                    if update_name:
                        update_name_field(file_path)
                    if remove_description:
                        remove_description(file_path)
                    if clear_name:
                        clear_name_value(file_path)
        except Exception as e:
            logging.error(f"Error processing file: {file_path} - {str(e)}")

    return position_to_files, duplicate_positions, near_duplicate_positions, invalid_positions

def save_preferences(directory, round_positions, num_decimals, save_rounded, update_name, remove_description, clear_name, find_near_duplicates, tolerance):
    preferences = {
        'directory': directory,
        'round_positions': round_positions,
        'num_decimals': num_decimals,
        'save_rounded': save_rounded,
        'update_name': update_name,
        'remove_description': remove_description,
        'clear_name': clear_name,
        'find_near_duplicates': find_near_duplicates,
        'tolerance': tolerance
    }
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

previous_preferences = load_preferences()
if previous_preferences:
    use_previous_preferences = input("Previous preferences found. Do you want to use them? (y/n): ").lower() == 'y'
else:
    use_previous_preferences = False

if use_previous_preferences:
    directory = previous_preferences['directory']
    round_positions = previous_preferences['round_positions']
    num_decimals = previous_preferences['num_decimals']
    save_rounded = previous_preferences['save_rounded']
    update_name = previous_preferences['update_name']
    remove_description = previous_preferences['remove_description']
    clear_name = previous_preferences['clear_name']
    find_near_duplicates = previous_preferences['find_near_duplicates']
    tolerance = previous_preferences['tolerance']
else:
    default_dir = str(script_dir)
    directory = input(f"Enter the directory path (leave blank to use {default_dir}): ") or default_dir
    round_positions = input("Do you want to round the position data for comparison? (y/n): ").lower() == 'y'
    if round_positions:
        num_decimals = int(input("Enter the number of decimal places to round to: "))
        save_rounded = input("Do you want to save the rounded position data to the JSON files? (y/n): ").lower() == 'y'
    else:
        num_decimals = None
        save_rounded = False
    update_name = input("Do you want to update the 'name' field in the JSON files to match the filename? (y/n): ").lower() == 'y'
    remove_description = input("Do you want to remove the 'description' line from JSON files? (y/n): ").lower() == 'y'
    clear_name = input("Do you want to clear the 'name' value from JSON files? (y/n): ").lower() == 'y'
    find_near_duplicates = input("Do you want to search for near duplicates? (y/n): ").lower() == 'y'
    if find_near_duplicates:
        tolerance = int(input("Enter the maximum integer difference allowed for near duplicates: "))
    else:
        tolerance = None

print(f"Preferences set:\n"
      f"Directory: {directory}\n"
      f"Round Positions: {round_positions}\n"
      f"Number of Decimals: {num_decimals}\n"
      f"Save Rounded: {save_rounded}\n"
      f"Update Name: {update_name}\n"
      f"Remove Description: {remove_description}\n"
      f"Clear Name: {clear_name}\n"
      f"Find Near Duplicates: {find_near_duplicates}\n"
      f"Tolerance: {tolerance}\n")

save_preferences(directory, round_positions, num_decimals, save_rounded, update_name, remove_description, clear_name, find_near_duplicates, tolerance)

log_to_file = input("Do you want to log the output to a file? (y/n): ").lower() == 'y'
if log_to_file:
    output_file = Path(script_dir, "duplicate_positions.txt")
else:
    output_file = None

print("Searching for duplicate and near duplicate positions...")
try:
    positions_to_files, duplicates, near_duplicates, invalid_positions = find_duplicate_and_near_duplicate_positions(
        directory, num_decimals=num_decimals, save_rounded=save_rounded, update_name=update_name,
        remove_description=remove_description, clear_name=clear_name, find_near_duplicates=find_near_duplicates,
        tolerance=tolerance
    )
except Exception as e:
    logging.error(f"Error during search: {str(e)}")
    print("An error occurred during the search process. Please check the error.log file for more details.")
    input("Press Enter to exit...")
    exit(1)

print(f"Number of exact duplicate positions: {len(duplicates)}")
print(f"Number of near duplicate positions: {len(near_duplicates)}")
print(f"Number of invalid positions: {len(invalid_positions)}")

if output_file:
    with open(output_file, 'w', encoding='utf-8') as f:
        if duplicates or near_duplicates or invalid_positions:
            if duplicates:
                f.write("Exact Duplicate Positions Found:\n\n")
                for position in sorted(duplicates):
                    f.write(f"Position: {position}\n")
                    f.write("Files containing this position:\n")
                    for file_path in sorted(positions_to_files[position]):
                        f.write(f"{file_path}\n")
                    f.write("\n")
            if near_duplicates:
                f.write("Near Duplicate Positions Found:\n\n")
                for position in sorted(near_duplicates):
                    f.write(f"Position: {position}\n")
                    f.write("Files containing this position:\n")
                    for file_path in sorted(positions_to_files[position]):
                        f.write(f"{file_path}\n")
                    f.write("\n")
            if invalid_positions:
                f.write("\nFiles with Invalid Positions:\n\n")
                for file_path in sorted(invalid_positions):
                    f.write(f"{file_path}\n")
        else:
            f.write("No duplicate or near duplicate positions found.")
    print(f"Output written to {output_file}")
else:
    if duplicates:
        print("Exact Duplicate Positions Found:")
        for position in sorted(duplicates):
            print(f"Position: {position}")
            print("Files containing this position:")
            for file_path in sorted(positions_to_files[position]):
                print(file_path)
            print()
    if near_duplicates:
        print("Near Duplicate Positions Found:")
        for position in sorted(near_duplicates):
            print(f"Position: {position}")
            print("Files containing this position:")
            for file_path in sorted(positions_to_files[position]):
                print(file_path)
            print()
    if invalid_positions:
        print("Files with Invalid Positions:")
        for file_path in sorted(invalid_positions):
            print(file_path)
    if not duplicates and not near_duplicates and not invalid_positions:
        print("No duplicate or near duplicate positions found.")

num_exact_duplicates = sum(len(files) - 1 for files in positions_to_files.values() if len(files) > 1)
print(f"Number of exact duplicate files: {num_exact_duplicates}")

delete_duplicates = input("Do you want to delete the files with duplicate positions? (y/n): ").lower() == 'y'
if delete_duplicates:
    for position in duplicates:
        for file_path in positions_to_files[position][1:]:
            try:
                os.remove(file_path)
                print(f"Deleted {file_path}")
            except Exception as e:
                logging.error(f"Error deleting file: {file_path} - {str(e)}")
                print(f"Error deleting {file_path}. Please check the error.log file for more details.")

print("Script finished.")
input("Press Enter to exit...")