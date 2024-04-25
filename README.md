# JSON File Manager

The JSON File Manager is a Python GUI application for processing and managing JSON files. It provides functionality to clean JSON data and find exact and similar duplicate JSON files based on the 'position' field.

![JSON File Manager Screenshot](JSON_File_Manager.png)

![JSON File Manager Screenshot](JSON_File_Manager_results.png)

## Features

- Select a directory containing JSON files
- Clean JSON data:
  - Clear the 'name' field
  - Write the filename to the 'name' field
  - Remove the 'description' field
- Find exact duplicate JSON files based on the 'position' field
- Find similar duplicate JSON files within a specified tolerance
- Round position values to a specified decimal places
- Display progress and results in the GUI
- Sort and delete duplicate/near-duplicate files
- Save results to a text file

## Usage

1. Clone the repository or download the script files.
2. Install the required dependencies (tkinter, NumPy).
3. Run the `gui.py` script to launch the JSON File Manager application.
4. Select the directory containing the JSON files you want to process.
5. Choose the desired cleaning and duplicate finding options.
6. Click the "Begin!" button to start processing the files.
7. View the progress and results in the GUI.
8. Sort and delete duplicate/near-duplicate files as needed.
9. Save the results to a text file if desired.

## Requirements

- Python 3.x
- tkinter
- NumPy

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).