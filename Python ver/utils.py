import json
import os
import logging

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