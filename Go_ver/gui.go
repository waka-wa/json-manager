package main

import (
    "fmt"
    "log"
    "os"
    "path/filepath"
    "strconv"
    "strings"
    "time"

    "fyne.io/fyne/v2/app"
    "fyne.io/fyne/v2/container"
    "fyne.io/fyne/v2/dialog"
    "fyne.io/fyne/v2/widget"
)

func main() {
    a := app.New()
    w := a.NewWindow("JSON File Manager")

    var (
        directoryPath         string
        clearName             bool
        writeFilenameToName   bool
        removeDescription     bool
        roundPositions        bool
        roundToDecimal        int
        findExactDuplicates   bool
        findSimilarMatches    bool
        similarityThreshold   float64
        preserveDirectoryTree bool
        progressBar           *widget.ProgressBar
        currentFileLabel      *widget.Label
        matchesLabel          *widget.Label
        filesScannedLabel     *widget.Label
        duplicateListBox      *widget.List
    )

    directoryEntry := widget.NewEntry()
    directoryEntry.SetPlaceHolder("Select Directory")

    browseButton := widget.NewButton("Browse", func() {
        dialog.ShowFolderOpen(func(dir fyne.ListableURI, err error) {
            if err != nil {
                dialog.ShowError(err, w)
                return
            }
            if dir != nil {
                directoryEntry.SetText(dir.Path())
            }
        }, w)
    })

    clearNameCheckbox := widget.NewCheck("Clear Name Field", func(value bool) {
        clearName = value
    })

    writeFilenameToNameCheckbox := widget.NewCheck("Write Filename to Name Field", func(value bool) {
        writeFilenameToName = value
    })

    removeDescriptionCheckbox := widget.NewCheck("Remove Description Field", func(value bool) {
        removeDescription = value
    })

    roundPositionsCheckbox := widget.NewCheck("Round Positional Data", func(value bool) {
        roundPositions = value
    })

    roundToDecimalEntry := widget.NewEntry()
    roundToDecimalEntry.SetText("2")
    roundToDecimalEntry.OnChanged = func(s string) {
        roundToDecimal, _ = strconv.Atoi(s)
    }

    findExactDuplicatesCheckbox := widget.NewCheck("Find Exact Duplicates", func(value bool) {
        findExactDuplicates = value
    })

    findSimilarMatchesCheckbox := widget.NewCheck("Find Similar Matches", func(value bool) {
        findSimilarMatches = value
    })

    similarityThresholdEntry := widget.NewEntry()
    similarityThresholdEntry.SetText("0.9")
	similarityThreshold, _ = strconv.ParseFloat(s, 64)
}

progressBar = widget.NewProgressBar()
currentFileLabel = widget.NewLabel("Current File: ")
matchesLabel = widget.NewLabel("0 Matches Found")
filesScannedLabel = widget.NewLabel("0/0 Files Scanned (0.00%)")

startButton := widget.NewButton("Begin!", func() {
	go processFiles(directoryEntry.Text, clearName, writeFilenameToName, removeDescription, roundPositions, roundToDecimal, findExactDuplicates, findSimilarMatches, similarityThreshold)
})

cleaningFrame := widget.NewCard("Cleaning Options", "", container.NewVBox(
	clearNameCheckbox,
	writeFilenameToNameCheckbox,
	removeDescriptionCheckbox,
	roundPositionsCheckbox,
	container.NewBorder(nil, nil, widget.NewLabel("Round to Decimal:"), nil, roundToDecimalEntry),
))

duplicateFrame := widget.NewCard("Duplicate Options", "", container.NewVBox(
	findExactDuplicatesCheckbox,
	findSimilarMatchesCheckbox,
	container.NewBorder(nil, nil, widget.NewLabel("Similarity Threshold:"), nil, similarityThresholdEntry),
))

progressFrame := container.NewVBox(
	currentFileLabel,
	progressBar,
	container.NewHBox(
		matchesLabel,
		layout.NewSpacer(),
		filesScannedLabel,
	),
)

content := container.NewVBox(
	container.NewHBox(directoryEntry, browseButton),
	cleaningFrame,
	duplicateFrame,
	progressFrame,
	startButton,
)

w.SetContent(content)
w.ShowAndRun()
}

func processFiles(directoryPath string, clearName, writeFilenameToName, removeDescription, roundPositions bool, roundToDecimal int, findExactDuplicates, findSimilarMatches bool, similarityThreshold float64) {
if directoryPath == "" {
	dialog.ShowInformation("Warning", "Please select a directory.", fyne.CurrentApp().Driver().AllWindows()[0])
	return
}

cleanOptions := map[string]interface{}{
	"clear_name":              clearName,
	"write_filename_to_name":  writeFilenameToName,
	"remove_description":      removeDescription,
	"round_positions":         roundPositions,
	"round_to_decimal":        roundToDecimal,
}

duplicateOptions := map[string]interface{}{
	"find_exact_duplicates":  findExactDuplicates,
	"find_similar_matches":   findSimilarMatches,
	"similarity_threshold":   similarityThreshold,
}

progressBar.Show()
progressBar.SetValue(0)

startTime := time.Now()

duplicates := make(map[string]struct{})
nearDuplicates := make(map[string]struct{})

findDuplicateAndNearDuplicatePositions(
	directoryPath,
	duplicates,
	nearDuplicates,
	"*.json",
	true,
	cleanOptions["round_to_decimal"].(int),
	cleanOptions["write_filename_to_name"].(bool),
	cleanOptions["remove_description"].(bool),
	cleanOptions["clear_name"].(bool),
	cleanOptions["round_positions"].(bool),
	duplicateOptions["find_similar_matches"].(bool),
	duplicateOptions["similarity_threshold"].(float64),
	func(current, total int, filePath string) {
		updateProgress(current, total, filePath)
	},
)

endTime := time.Now()

progressBar.Hide()

duplicateWindow := fyne.CurrentApp().NewWindow("Duplicate JSON Files")
duplicateWindow.Resize(fyne.NewSize(800, 600))

duplicateListBox = widget.NewList(
	func() int {
		return len(positionToFiles)
	},
	func() fyne.CanvasObject {
		return widget.NewLabel("template")
	},
	func(id widget.ListItemID, cell fyne.CanvasObject) {
		label := cell.(*widget.Label)
		var files []string
		for _, file := range positionToFiles[getPositionKey(id)] {
			files = append(files, strings.TrimPrefix(file, directoryPath+string(os.PathSeparator)))
		}
		label.SetText(strings.Join(files, "\n"))
	},
)

scrollContainer := container.NewScroll(duplicateListBox)

deleteButton := widget.NewButton("Delete Selected Files", func() {
	selectedPositions := duplicateListBox.SelectedIndexes()
	var selectedFiles []string
	for _, pos := range selectedPositions {
		positionKey := getPositionKey(pos)
		selectedFiles = append(selectedFiles, positionToFiles[positionKey]...)
	}

	confirmMessage := "Are you sure you want to delete the following files?\n\n"
	confirmMessage += strings.Join(selectedFiles, "\n")
	dialog.ShowConfirm("Confirm Deletion", confirmMessage, func(confirm bool) {
		if !confirm {
			return
		}

		for _, file := range selectedFiles {
			err := os.Remove(file)
			if err != nil {
				log.Printf("Error deleting file: %s - %v", file, err)
			}
		}

		for _, pos := range selectedPositions {
			positionKey := getPositionKey(pos)
			delete(positionToFiles, positionKey)
		}

		duplicateListBox.UnselectAll()
		duplicateListBox.Refresh()

		dialog.ShowInformation("Deletion Complete", "Selected files have been deleted.", duplicateWindow)
	}, duplicateWindow)
})

preserveDirectoryTreeCheckbox := widget.NewCheck("Preserve Directory Tree", func(value bool) {
	preserveDirectoryTree = value
})

moveButton := widget.NewButton("Move Selected Files", func() {
	selectedPositions := duplicateListBox.SelectedIndexes()
	var selectedFiles []string
	for _, pos := range selectedPositions {
		positionKey := getPositionKey(pos)
		selectedFiles = append(selectedFiles, positionToFiles[positionKey]...)
	}

	dialog.ShowFolderOpen(func(dir fyne.ListableURI, err error) {
		if err != nil {
			dialog.ShowError(err, duplicateWindow)
			return
		}
		if dir == nil {
			return
		}

		destinationFolder := dir.Path()

		confirmMessage := "Are you sure you want to move the following files?\n\n"
		confirmMessage += strings.Join(selectedFiles, "\n")
		dialog.ShowConfirm("Confirm Move", confirmMessage, func(confirm bool) {
			if !confirm {
				return
			}

			for _, file := range selectedFiles {
				var destinationPath string
				if preserveDirectoryTree {
					relativePath := strings.TrimPrefix(file, directoryPath+string(os.PathSeparator))
					destinationPath = filepath.Join(destinationFolder, relativePath)
				} else {
					destinationPath = filepath.Join(destinationFolder, filepath.Base(file))
				}

				err := os.MkdirAll(filepath.Dir(destinationPath), os.ModePerm)
				if err != nil {
					log.Printf("Error creating directory: %s - %v", destinationPath, err)
					continue
				}

				err = os.Rename(file, destinationPath)
				if err != nil {
					log.Printf("Error moving file: %s - %v", file, err)
				}
			}

			for _, pos := range selectedPositions {
				positionKey := getPositionKey(pos)
				delete(positionToFiles, positionKey)
			}

			duplicateListBox.UnselectAll()
			duplicateListBox.Refresh()

			dialog.ShowInformation("Move Complete", "Selected files have been moved.", duplicateWindow)
		}, duplicateWindow)
	}, duplicateWindow)
})

autoSelectEntry := widget.NewEntry()
autoSelectEntry.SetPlaceHolder("Auto-Select Directory (with wildcards)")

autoSelectButton := widget.NewButton("Select", func() {
	autoSelectDir := autoSelectEntry.Text
	selectedIndices := make([]int, 0)
	for i := 0; i < duplicateListBox.Length(); i++ {
		positionKey := getPositionKey(i)
		for _, file := range positionToFiles[positionKey] {
			if strings.HasPrefix(file, autoSelectDir) {
				selectedIndices = append(selectedIndices, i)
				break
			}
		}
	}

	duplicateListBox.UnselectAll()
	for _, index := range selectedIndices {
		duplicateListBox.Select(index)
	}
})

saveButton := widget.NewButton("Save Results", func() {
	dialog.ShowFileSave(func(file fyne.URIWriteCloser, err error) {
		if err != nil {
			dialog.ShowError(err, duplicateWindow)
			return
		}
		if file == nil {
			return
		}

		defer file.Close()

		_, err = file.Write([]byte("Exact Duplicate Positions:\n"))
		if err != nil {
			dialog.ShowError(err, duplicateWindow)
			return
		}

		for position := range duplicatePositions {
			_, err = file.Write([]byte(fmt.Sprintf("Position: %v\n", position)))
			if err != nil {
				dialog.ShowError(err, duplicateWindow)
				return
			}

			_, err = file.Write([]byte("Files:\n"))
			if err != nil {
				dialog.ShowError(err, duplicateWindow)
				return
			}

			for _, filePath := range positionToFiles[position] {
				_, err = file.Write([]byte(fmt.Sprintf("%s\n", strings.TrimPrefix(filePath, directoryPath+string(os.PathSeparator)))))
				if err != nil {
					dialog.ShowError(err, duplicateWindow)
					return
				}
			}

			_, err = file.Write([]byte("\n"))
			if err != nil {
				dialog.ShowError(err, duplicateWindow)
				return
			}
		}

		_, err = file.Write([]byte("\nNear Duplicate Positions:\n"))
		if err != nil {
			dialog.ShowError(err, duplicateWindow)
			return
		}

		for position := range nearDuplicatePositions {
			_, err = file.Write([]byte(fmt.Sprintf("Position: %v\n", position)))
			if err != nil {
				dialog.ShowError(err, duplicateWindow)
				return
			}

			_, err = file.Write([]byte("Files:\n"))
			if err != nil {
				dialog.ShowError(err, duplicateWindow)
				return
			}

			for _, filePath := range positionToFiles[position] {
				_, err = file.Write([]byte(fmt.Sprintf("%s\n", strings.TrimPrefix(filePath, directoryPath+string(os.PathSeparator)))))
				if err != nil {
					dialog.ShowError(err, duplicateWindow)
					return
				}
			}

			_, err = file.Write([]byte("\n"))
			if err != nil {
				dialog.ShowError(err, duplicateWindow)
				return
			}
		}

		dialog.ShowInformation("Save Results", "Results saved successfully.", duplicateWindow)
	}, duplicateWindow)
})

duplicateContent := container.NewBorder(
	nil,
	container.NewVBox(
		container.NewGridWithColumns(3,
			deleteButton,
			preserveDirectoryTreeCheckbox,
			moveButton,
		),
		container.NewBorder(nil, nil, widget.NewLabel("Auto-Select Directory (with wildcards):"), autoSelectButton, autoSelectEntry),
		saveButton,
	),
	nil,
	nil,
	scrollContainer,
)
duplicateWindow.SetContent(duplicateContent)

totalMatches := len(duplicatePositions) + len(nearDuplicatePositions)
totalFiles := progressBar.Max
elapsedTime := endTime.Sub(startTime).Seconds()
filesPerSecond := float64(totalFiles) / elapsedTime

resultMessage := fmt.Sprintf("Process completed.\n\n"+
	"Number of exact duplicate positions: %d\n"+
	"Number of near duplicate positions: %d\n"+
	"Total matches found: %d\n"+
	"Total files scanned: %d\n"+
	"Files per second: %.2f\n"+
	"Elapsed time: %.2f seconds\n\n"+
	"Duplicate and near duplicate files are listed in the new window.",
	len(duplicatePositions),
	len(nearDuplicatePositions),
	totalMatches,
	totalFiles,
	filesPerSecond,
	elapsedTime,
)

dialog.ShowInformation("Results", resultMessage, fyne.CurrentApp().Driver().AllWindows()[0])

duplicateWindow.Show()
}

func updateProgress(current, total int, filePath string) {
progressBar.SetValue(float64(current) / float64(total))
currentFileLabel.SetText(fmt.Sprintf("Current File: %s", strings.TrimPrefix(filePath, directoryPath+string(os.PathSeparator))))

totalMatches := len(duplicatePositions) + len(nearDuplicatePositions)
completionPercentage := float64(current) / float64(total) * 100

matchesLabel.SetText(fmt.Sprintf("%d Matches Found", totalMatches))
filesScannedLabel.SetText(fmt.Sprintf("%d/%d Files Scanned (%.2f%%)", current, total, completionPercentage))
}

func getPositionKey(index int) string {
i := 0
for position := range positionToFiles {
	if i == index {
		return position
	}
	i++
}
return ""
}