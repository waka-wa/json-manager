import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from json_file_manager import find_duplicate_and_near_duplicate_positions
import os
import threading
import time

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
        'remove_description': remove_description_var.get()
    }

    duplicate_options = {
        'find_exact_duplicates': find_exact_duplicates_var.get(),
        'find_similar_matches': find_similar_matches_var.get(),
        'similarity_threshold': float(similarity_threshold_entry.get()) if find_similar_matches_var.get() else None,
        'round_and_save_data': round_and_save_data_var.get(),
        'round_to_decimal': int(round_to_decimal_entry.get()) if round_and_save_data_var.get() else None
    }

    progress_bar.pack()
    progress_bar.start()

    start_time = time.time()

    duplicates = set()
    near_duplicates = set()

    position_to_files, duplicate_positions, near_duplicate_positions, invalid_positions = find_duplicate_and_near_duplicate_positions(
        directory,
        duplicates,
        near_duplicates,
        num_decimals=duplicate_options['round_to_decimal'],
        save_rounded=duplicate_options['round_and_save_data'],
        update_name=clean_options['write_filename_to_name'],
        remove_description=clean_options['remove_description'],
        clear_name=clean_options['clear_name'],
        find_near_duplicates=duplicate_options['find_similar_matches'],
        tolerance=duplicate_options['similarity_threshold'],
        progress_callback=lambda current, total, file_path: update_progress(current, total, file_path, duplicate_positions, near_duplicate_positions)
    )
    end_time = time.time()

    progress_bar.stop()
    progress_bar.pack_forget()

    duplicate_window = tk.Toplevel(window)
    duplicate_window.title("Duplicate JSON Files")

    duplicate_frame = tk.Frame(duplicate_window)
    duplicate_frame.pack(pady=10, padx=10)

    duplicate_listbox = tk.Listbox(duplicate_frame, selectmode=tk.MULTIPLE, width=100, height=20)
    duplicate_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(duplicate_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    duplicate_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=duplicate_listbox.yview)

    for position in duplicate_positions:
        for file_path in position_to_files[position]:
            duplicate_listbox.insert(tk.END, file_path)
        duplicate_listbox.insert(tk.END, "")  # Add a blank line between groups

    for position in near_duplicate_positions:
        for file_path in position_to_files[position]:
            duplicate_listbox.insert(tk.END, file_path)
        duplicate_listbox.insert(tk.END, "")  # Add a blank line between groups

    def delete_selected_files():
        selected_indices = duplicate_listbox.curselection()
        selected_files = [duplicate_listbox.get(index) for index in selected_indices]
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the following files?\n\n{', '.join(selected_files)}")
        if confirm:
            for file_path in selected_files:
                try:
                    os.remove(file_path)
                    duplicate_listbox.delete(duplicate_listbox.get(0, tk.END).index(file_path))
                except FileNotFoundError:
                    pass
            messagebox.showinfo("Deletion Complete", "Selected files have been deleted.")

    def sort_listbox(sort_option):
        file_list = list(duplicate_listbox.get(0, tk.END))
        file_list = [file for file in file_list if file.strip()]  # Remove empty lines
        if sort_option == "exact" or sort_option == "similar":
            try:
                file_list.sort(key=lambda x: (position_to_files[tuple(map(float, x.split()[-3:]))], x), reverse=(sort_option == "similar"))
            except (KeyError, IndexError, ValueError):
                file_list.sort()  # Fallback to alphabetical sorting
        else:
            file_list.sort()
        duplicate_listbox.delete(0, tk.END)
        for file in file_list:
            duplicate_listbox.insert(tk.END, file)
            if file == file_list[-1] or (len(file.split()[-3:]) == 3 and tuple(map(float, file.split()[-3:])) != tuple(map(float, duplicate_listbox.get(duplicate_listbox.index(file) + 1).split()[-3:]))):
                duplicate_listbox.insert(tk.END, "")  # Add a blank line between groups

    sort_frame = tk.Frame(duplicate_window)
    sort_frame.pack(pady=10)

    sort_label = tk.Label(sort_frame, text="Sort by:")
    sort_label.pack(side=tk.LEFT)

    sort_var = tk.StringVar()
    sort_var.set("exact")

    exact_radio = tk.Radiobutton(sort_frame, text="Exact Matches", variable=sort_var, value="exact", command=lambda: sort_listbox("exact"))
    exact_radio.pack(side=tk.LEFT)

    similar_radio = tk.Radiobutton(sort_frame, text="Similar Matches", variable=sort_var, value="similar", command=lambda: sort_listbox("similar"))
    similar_radio.pack(side=tk.LEFT)

    alphabetical_radio = tk.Radiobutton(sort_frame, text="Alphabetical", variable=sort_var, value="alphabetical", command=lambda: sort_listbox("alphabetical"))
    alphabetical_radio.pack(side=tk.LEFT)

    delete_button = tk.Button(duplicate_window, text="Delete Selected Files", command=delete_selected_files)
    delete_button.pack(pady=10)

    def save_results():
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "w") as file:
                    file.write("Exact Duplicate Positions:\n")
                    for position in duplicates:
                        file.write(f"Position: {position}\n")
                        file.write("Files:\n")
                        for file_path in position_to_files[position]:
                            file.write(f"{file_path}\n")
                        file.write("\n")

                    file.write("\nNear Duplicate Positions:\n")
                    for position in near_duplicates:
                        file.write(f"Position: {position}\n")
                        file.write("Files:\n")
                        for file_path in position_to_files[position]:
                            file.write(f"{file_path}\n")
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

round_and_save_data_var = tk.BooleanVar()
round_and_save_data_checkbox = tk.Checkbutton(duplicate_frame, text="Round and Save Data", variable=round_and_save_data_var)
round_and_save_data_checkbox.pack(anchor=tk.W)

round_to_decimal_frame = tk.Frame(duplicate_frame)
round_to_decimal_frame.pack(anchor=tk.W, padx=20)

round_to_decimal_label = tk.Label(round_to_decimal_frame, text="Round to Decimal:")
round_to_decimal_label.pack(side=tk.LEFT)

round_to_decimal_entry = tk.Entry(round_to_decimal_frame, width=5)
round_to_decimal_entry.insert(tk.END, "2")
round_to_decimal_entry.pack(side=tk.LEFT)

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

# Initialize variables
duplicates = []
near_duplicates = []
start_time = 0

# Run the GUI
window.mainloop()