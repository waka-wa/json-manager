from utils import extract_positions, round_position, update_name_field, remove_description, clear_name_value, round_positions_in_file
from collections import defaultdict
import os
import logging
import numpy as np

def find_duplicate_and_near_duplicate_positions(directory_path, duplicates, near_duplicates, file_pattern='*.json', ignore_empty=False, num_decimals=None, update_name=False, remove_description=False, clear_name=False, round_positions=False, find_near_duplicates=False, tolerance=1, progress_callback=None):
    position_to_files = defaultdict(list)
    duplicate_positions = set()
    near_duplicate_positions = set()

    filenames_within_group = defaultdict(set)

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
                        duplicate_positions.add(rounded_position)
                        duplicates.add(file_path)
                    elif find_near_duplicates:
                        for existing_position in position_to_files:
                            if np.all(np.abs(np.array(rounded_position) - np.array(existing_position)) <= tolerance):
                                position_to_files[existing_position].append(file_path)
                                near_duplicate_positions.add(existing_position)
                                near_duplicates.add(file_path)
                                break
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

    for rounded_position, file_paths in position_to_files.items():
        selected_file = None
        for file_path in file_paths:
            if file_path not in filenames_within_group[rounded_position]:
                filenames_within_group[rounded_position].add(file_path)
                selected_file = file_path
                break

    return position_to_files, duplicate_positions, near_duplicate_positions, filenames_within_group