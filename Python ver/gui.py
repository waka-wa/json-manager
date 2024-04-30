import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from file_manager import find_duplicate_and_near_duplicate_positions
import os
import threading
import time
import shutil

def create_gui():
    def select_directory():
        directory = filedialog.askdirectory()
        directory_entry.delete(0, tk.END)
        directory_entry.insert(tk.END, directory)

    def process_files():
        directory = directory_entry.get()
        if not directory:
            messagebox.showwarning("Warning", "Please select a directory.")
            return

        clean_options = {
            'clear_name': clear_name_var.get(),
            'write_filename_to_name': write_filename_to_name_var.get(),
            'remove_description': remove_description_var.get(),
            'round_positions': round_positions_var.get(),
            'round_to_decimal': int(round_to_decimal_entry.get()) if round_positions_var.get() else None
        }

        duplicate_options = {
            'find_exact_duplicates': find_exact_duplicates_var.get(),
            'find_similar_matches': find_similar_matches_var.get(),
            'similarity_threshold': float(similarity_threshold_entry.get()) if find_similar_matches_var.get() else None
        }

        progress_bar.pack()
        progress_bar.start()

        start_time = time.time()

        duplicates = set()
        near_duplicates = set()
        duplicate_positions = set()
        near_duplicate_positions = set()

        grid_cell_size = float(grid_cell_size_entry.get())

        position_to_files, duplicate_positions, near_duplicate_positions, filenames_within_group = find_duplicate_and_near_duplicate_positions(
            directory,
            duplicates,
            near_duplicates,
            num_decimals=clean_options['round_to_decimal'],
            update_name=clean_options['write_filename_to_name'],
            remove_description=clean_options['remove_description'],
            clear_name=clean_options['clear_name'],
            round_positions=clean_options['round_positions'],
            find_near_duplicates=duplicate_options['find_similar_matches'],
            tolerance=duplicate_options['similarity_threshold'],
            grid_cell_size=grid_cell_size,
            progress_callback=lambda current, total, file_path: update_progress(current, total, file_path, duplicate_positions, near_duplicate_positions)
        )
        end_time = time.time()

        progress_bar.stop()
        progress_bar.pack_forget()

        duplicate_window = tk.Toplevel(window)
        duplicate_window.title("Duplicate JSON Files")
        duplicate_window.geometry("800x600")
        duplicate_window.resizable(True, True)

        duplicate_frame = tk.Frame(duplicate_window)
        duplicate_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        duplicate_listbox = tk.Listbox(duplicate_frame, selectmode=tk.MULTIPLE, width=100, height=20)
        duplicate_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(duplicate_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        duplicate_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=duplicate_listbox.yview)

        for position in duplicate_positions:
            for file_path in position_to_files[position]:
                duplicate_listbox.insert(tk.END, os.path.relpath(file_path, directory))
            duplicate_listbox.insert(tk.END, "")  # Add a blank line between groups

        for position in near_duplicate_positions:
            for file_path in position_to_files[position]:
                duplicate_listbox.insert(tk.END, os.path.relpath(file_path, directory))
            duplicate_listbox.insert(tk.END, "")  # Add a blank line between groups

        def auto_select_files(directory):
            auto_select_dir = auto_select_entry.get()
            if auto_select_dir:
                selected_indices = []
                for index, result_file in enumerate(duplicate_listbox.get(0, tk.END)):
                    if result_file:
                        if result_file.startswith(auto_select_dir):
                            selected_indices.append(index)

                duplicate_listbox.selection_clear(0, tk.END)  # Clear any previous selection
                for index in selected_indices:
                    duplicate_listbox.selection_set(index)
                    duplicate_listbox.itemconfig(index, bg='lightblue')

        def delete_selected_files():
            selected_indices = duplicate_listbox.curselection()
            selected_files = [duplicate_listbox.get(index) for index in selected_indices]
            selected_files = [os.path.join(directory, file) for file in selected_files]
            confirm_message = "Are you sure you want to delete the following files?\n\n"
            confirm_message += "\n".join(os.path.relpath(file, directory) for file in selected_files)
            confirm = messagebox.askyesno("Confirm Deletion", confirm_message)
            if confirm:
                for file_path in selected_files:
                    try:
                        os.remove(file_path)
                        duplicate_listbox.delete(duplicate_listbox.get(0, tk.END).index(os.path.relpath(file_path, directory)))
                    except FileNotFoundError:
                        pass
                messagebox.showinfo("Deletion Complete", "Selected files have been deleted.")

        def move_selected_files():
            selected_indices = duplicate_listbox.curselection()
            selected_files = [duplicate_listbox.get(index) for index in selected_indices]
            selected_files = [os.path.join(directory, file) for file in selected_files]
            destination_folder = filedialog.askdirectory(title="Select Destination Folder")
            if destination_folder:
                confirm_message = "Are you sure you want to move the following files?\n\n"
                confirm_message += "\n".join(os.path.relpath(file, directory) for file in selected_files)
                confirm = messagebox.askyesno("Confirm Move", confirm_message)
                if confirm:
                    for file_path in selected_files:
                        try:
                            if preserve_directory_tree_var.get():
                                relative_path = os.path.relpath(file_path, directory)
                                destination_path = os.path.join(destination_folder, relative_path)
                                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                            else:
                                destination_path = os.path.join(destination_folder, os.path.basename(file_path))
                            shutil.move(file_path, destination_path)
                            duplicate_listbox.delete(duplicate_listbox.get(0, tk.END).index(os.path.relpath(file_path, directory)))
                        except FileNotFoundError:
                            pass
                    messagebox.showinfo("Move Complete", "Selected files have been moved.")

        action_frame = tk.Frame(duplicate_window)
        action_frame.pack(pady=10)

        delete_button = tk.Button(action_frame, text="Delete Selected Files", command=delete_selected_files)
        delete_button.pack(side=tk.LEFT, padx=5)

        preserve_directory_tree_var = tk.BooleanVar()
        preserve_directory_tree_checkbox = tk.Checkbutton(action_frame, text="Preserve Directory Tree", variable=preserve_directory_tree_var)
        preserve_directory_tree_checkbox.pack(side=tk.LEFT, padx=5)

        move_button = tk.Button(action_frame, text="Move Selected Files", command=move_selected_files)
        move_button.pack(side=tk.LEFT)

        auto_select_frame = tk.Frame(duplicate_window)
        auto_select_frame.pack(pady=10)

        auto_select_label = tk.Label(auto_select_frame, text="Auto-Select Directory (with wildcards):")
        auto_select_label.pack(side=tk.LEFT)

        auto_select_entry = tk.Entry(auto_select_frame, width=30)
        auto_select_entry.pack(side=tk.LEFT, padx=5)

        auto_select_button = tk.Button(auto_select_frame, text="Select", command=lambda: auto_select_files(directory))
        auto_select_button.pack(side=tk.LEFT)

        def save_results():
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write("Exact Duplicate Positions:\n")
                        for position in duplicate_positions:
                            file.write(f"Position: {position}\n")
                            file.write("Files:\n")
                            for file_path in position_to_files[position]:
                                file.write(f"{os.path.relpath(file_path, directory)}\n")
                            file.write("\n")

                        file.write("\nNear Duplicate Positions:\n")
                        for position in near_duplicate_positions:
                            file.write(f"Position: {position}\n")
                            file.write("Files:\n")
                            for file_path in position_to_files[position]:
                                file.write(f"{os.path.relpath(file_path, directory)}\n")
                            file.write("\n")

                    messagebox.showinfo("Save Results", "Results saved successfully.")
                except IOError:
                    messagebox.showerror("Save Results", "An error occurred while saving the results.")

        save_button = tk.Button(duplicate_window, text="Save Results", command=save_results)
        save_button.pack(pady=10)

        total_matches = len(duplicate_positions) + len(near_duplicate_positions)
        total_files = progress_bar["maximum"]
        elapsed_time = end_time - start_time
        files_per_second = total_files / elapsed_time if elapsed_time > 0 else 0

        result_message = f"Process completed.\n\n"
        result_message += f"Number of exact duplicate positions: {len(duplicate_positions)}\n"
        result_message += f"Number of near duplicate positions: {len(near_duplicate_positions)}\n"
        result_message += f"Total matches found: {total_matches}\n"
        result_message += f"Total files scanned: {total_files}\n"
        result_message += f"Files per second: {files_per_second:.2f}\n"
        result_message += f"Elapsed time: {elapsed_time:.2f} seconds\n\n"
        result_message += "Duplicate and near duplicate files are listed in the new window."

        messagebox.showinfo("Results", result_message)

    def update_progress(current, total, file_path, duplicate_positions, near_duplicate_positions):
        progress_bar["value"] = current
        progress_bar["maximum"] = total
        current_file_label.config(text=f"Current File: {os.path.relpath(file_path, directory_entry.get())}", anchor="w")

        total_matches = len(duplicate_positions) + len(near_duplicate_positions)
        completion_percentage = (current / total) * 100 if total > 0 else 0

        matches_label.config(text=f"{total_matches} Matches Found")
        files_scanned_label.config(text=f"{current}/{total} Files Scanned ({completion_percentage:.2f}%)")

        window.update_idletasks()

    def start_process():
        thread = threading.Thread(target=process_files)
        thread.start()

    # Create the main window
    window = tk.Tk()
    window.title("JSON File Manager")
    window.geometry("500x600")

    # Directory selection
    directory_frame = tk.Frame(window)
    directory_frame.pack(pady=10)

    directory_label = tk.Label(directory_frame, text="Select Directory:")
    directory_label.pack(side=tk.LEFT)

    directory_entry = tk.Entry(directory_frame, width=30)
    directory_entry.pack(side=tk.LEFT, padx=5)

    browse_button = tk.Button(directory_frame, text="Browse", command=select_directory)
    browse_button.pack(side=tk.LEFT)

    # Cleaning options
    cleaning_frame = tk.LabelFrame(window, text="Cleaning Options")
    cleaning_frame.pack(pady=10, padx=10, fill=tk.BOTH)

    clear_name_var = tk.BooleanVar()
    clear_name_checkbox = tk.Checkbutton(cleaning_frame, text="Clear Name Field", variable=clear_name_var)
    clear_name_checkbox.pack(anchor=tk.W)

    write_filename_to_name_var = tk.BooleanVar()
    write_filename_to_name_checkbox = tk.Checkbutton(cleaning_frame, text="Write Filename to Name Field", variable=write_filename_to_name_var)
    write_filename_to_name_checkbox.pack(anchor=tk.W)

    remove_description_var = tk.BooleanVar()
    remove_description_checkbox = tk.Checkbutton(cleaning_frame, text="Remove Description Field", variable=remove_description_var)
    remove_description_checkbox.pack(anchor=tk.W)

    round_positions_var = tk.BooleanVar()
    round_positions_checkbox = tk.Checkbutton(cleaning_frame, text="Round Positional Data", variable=round_positions_var)
    round_positions_checkbox.pack(anchor=tk.W)

    round_to_decimal_frame = tk.Frame(cleaning_frame)
    round_to_decimal_frame.pack(anchor=tk.W, padx=20)

    round_to_decimal_label = tk.Label(round_to_decimal_frame, text="Round to Decimal:")
    round_to_decimal_label.pack(side=tk.LEFT)

    round_to_decimal_entry = tk.Entry(round_to_decimal_frame, width=5)
    round_to_decimal_entry.insert(tk.END, "2")
    round_to_decimal_entry.pack(side=tk.LEFT)

    # Duplicate options
    duplicate_frame = tk.LabelFrame(window, text="Duplicate Options")
    duplicate_frame.pack(pady=10, padx=10, fill=tk.BOTH)

    find_exact_duplicates_var = tk.BooleanVar()
    find_exact_duplicates_checkbox = tk.Checkbutton(duplicate_frame, text="Find Exact Duplicates", variable=find_exact_duplicates_var)
    find_exact_duplicates_checkbox.pack(anchor=tk.W)

    find_similar_matches_var = tk.BooleanVar()
    find_similar_matches_checkbox = tk.Checkbutton(duplicate_frame, text="Find Similar Matches", variable=find_similar_matches_var)
    find_similar_matches_checkbox.pack(anchor=tk.W)

    similarity_threshold_frame = tk.Frame(duplicate_frame)
    similarity_threshold_frame.pack(anchor=tk.W, padx=20)

    similarity_threshold_label = tk.Label(similarity_threshold_frame, text="Similarity Threshold:")
    similarity_threshold_label.pack(side=tk.LEFT)

    similarity_threshold_entry = tk.Entry(similarity_threshold_frame, width=5)
    similarity_threshold_entry.insert(tk.END, "0.9")
    similarity_threshold_entry.pack(side=tk.LEFT)

    # Progress bar
    progress_frame = tk.Frame(window)
    progress_frame.pack(fill=tk.X, padx=10, pady=5)

    current_file_label = tk.Label(progress_frame, text="Current File: ", anchor="w")
    current_file_label.pack(fill=tk.X)

    progress_bar = ttk.Progressbar(progress_frame, length=400, mode="determinate")
    progress_bar.pack(fill=tk.X)

    matches_label = tk.Label(progress_frame, text="0 Matches Found")
    matches_label.pack(side=tk.LEFT)

    files_scanned_label = tk.Label(progress_frame, text="0/0 Files Scanned (0.00%)")
    files_scanned_label.pack(side=tk.RIGHT)

    # Start button
    start_button = tk.Button(window, text="Begin!", command=start_process)
    start_button.pack(pady=10)

    # Grid cell size adjustment
    grid_cell_size_frame = tk.Frame(duplicate_frame)
    grid_cell_size_frame.pack(anchor=tk.W, padx=20)

    grid_cell_size_label = tk.Label(grid_cell_size_frame, text="Grid Cell Size:")
    grid_cell_size_label.pack(side=tk.LEFT)

    grid_cell_size_entry = tk.Entry(grid_cell_size_frame, width=5)
    grid_cell_size_entry.insert(tk.END, "2")
    grid_cell_size_entry.pack(side=tk.LEFT)

    # Run the GUI
    window.mainloop()