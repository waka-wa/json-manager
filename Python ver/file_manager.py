from utils import extract_positions, round_position, update_name_field, remove_description, clear_name_value, round_positions_in_file, coarse_hash, euclidean_distance
from collections import defaultdict
import os
import logging

def find_duplicate_and_near_duplicate_positions(directory_path, duplicates, near_duplicates, file_pattern='*.json', ignore_empty=False, num_decimals=None, update_name=False, remove_description=False, clear_name=False, round_positions=False, find_near_duplicates=False, tolerance=1, grid_cell_size=2, progress_callback=None):
    position_groups = defaultdict(list)
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
                    group_key = coarse_hash(rounded_position, grid_cell_size)
                    position_groups[group_key].append((rounded_position, file_path))
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

    for positions_in_group in position_groups.values():
        for i in range(len(positions_in_group)):
            for j in range(i + 1, len(positions_in_group)):
                pos1, file1 = positions_in_group[i]
                pos2, file2 = positions_in_group[j]

                if pos1 == pos2:
                    duplicate_positions.add(pos1)
                    duplicates.add(file1)
                    duplicates.add(file2)
                elif find_near_duplicates and euclidean_distance(pos1, pos2) <= tolerance:
                    near_duplicate_positions.add(pos1)
                    near_duplicates.add(file1)
                    near_duplicates.add(file2)

    for rounded_position, file_paths in position_groups.items():
        selected_file = None
        for file_path in file_paths:
            if file_path not in filenames_within_group[rounded_position]:
                filenames_within_group[rounded_position].add(file_path)
                selected_file = file_path
                break

    return position_groups, duplicate_positions, near_duplicate_positions, filenames_within_group