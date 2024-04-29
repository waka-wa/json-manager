package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"math"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
)

type PositionData struct {
	Position    []float64 `json:"position"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
}

var (
	invalidPositions       = make(map[string]struct{})
	positionToFiles        = make(map[string][]string)
	duplicatePositions     = make(map[string]struct{})
	nearDuplicatePositions = make(map[string]struct{})
	filenamesWithinGroup   = make(map[string]map[string]struct{})
	mu                     sync.Mutex
)

func extractPositions(filePath string) ([]float64, error) {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("error reading file: %s - %w", filePath, err)
	}

	var positionData PositionData
	err = json.Unmarshal(data, &positionData)
	if err != nil {
		return nil, fmt.Errorf("error parsing JSON: %s - %w", filePath, err)
	}

	return positionData.Position, nil
}

func roundPosition(position []float64, numDecimals int, filePath string) []float64 {
	if position == nil {
		mu.Lock()
		invalidPositions[filePath] = struct{}{}
		mu.Unlock()
		return nil
	}

	roundedPosition := make([]float64, len(position))
	for i, n := range position {
		roundedPosition[i] = round(n, numDecimals)
	}
	return roundedPosition
}

func round(val float64, numDecimals int) float64 {
	factor := math.Pow10(numDecimals)
	return math.Round(val*factor) / factor
}

func updateNameField(filePath string) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file: %s - %w", filePath, err)
	}

	var positionData PositionData
	err = json.Unmarshal(data, &positionData)
	if err != nil {
		return fmt.Errorf("error parsing JSON: %s - %w", filePath, err)
	}

	positionData.Name = strings.TrimSuffix(filepath.Base(filePath), filepath.Ext(filePath))

	updatedData, err := json.MarshalIndent(positionData, "", "    ")
	if err != nil {
		return fmt.Errorf("error marshaling JSON: %s - %w", filePath, err)
	}

	err = ioutil.WriteFile(filePath, updatedData, 0644)
	if err != nil {
		return fmt.Errorf("error writing file: %s - %w", filePath, err)
	}

	return nil
}

func removeDescription(filePath string) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file: %s - %w", filePath, err)
	}

	var positionData PositionData
	err = json.Unmarshal(data, &positionData)
	if err != nil {
		return fmt.Errorf("error parsing JSON: %s - %w", filePath, err)
	}

	if positionData.Description != "" {
		positionData.Description = ""

		updatedData, err := json.MarshalIndent(positionData, "", "    ")
		if err != nil {
			return fmt.Errorf("error marshaling JSON: %s - %w", filePath, err)
		}

		err = ioutil.WriteFile(filePath, updatedData, 0644)
		if err != nil {
			return fmt.Errorf("error writing file: %s - %w", filePath, err)
		}

		fmt.Printf("Description removed from file: %s\n", filePath)
	} else {
		fmt.Printf("No description found in file: %s\n", filePath)
	}

	return nil
}

func clearNameValue(filePath string) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file: %s - %w", filePath, err)
	}

	var positionData PositionData
	err = json.Unmarshal(data, &positionData)
	if err != nil {
		return fmt.Errorf("error parsing JSON: %s - %w", filePath, err)
	}

	if positionData.Name != "" {
		positionData.Name = ""

		updatedData, err := json.MarshalIndent(positionData, "", "    ")
		if err != nil {
			return fmt.Errorf("error marshaling JSON: %s - %w", filePath, err)
		}

		err = ioutil.WriteFile(filePath, updatedData, 0644)
		if err != nil {
			return fmt.Errorf("error writing file: %s - %w", filePath, err)
		}
	}

	return nil
}

func roundPositionsInFile(filePath string, numDecimals int) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file: %s - %w", filePath, err)
	}

	var positionData PositionData
	err = json.Unmarshal(data, &positionData)
	if err != nil {
		return fmt.Errorf("error parsing JSON: %s - %w", filePath, err)
	}

	if positionData.Position != nil {
		roundedPosition := roundPosition(positionData.Position, numDecimals, filePath)
		if roundedPosition != nil {
			positionData.Position = roundedPosition

			updatedData, err := json.MarshalIndent(positionData, "", "    ")
			if err != nil {
				return fmt.Errorf("error marshaling JSON: %s - %w", filePath, err)
			}

			err = ioutil.WriteFile(filePath, updatedData, 0644)
			if err != nil {
				return fmt.Errorf("error writing file: %s - %w", filePath, err)
			}
		}
	}

	return nil
}

func findDuplicateAndNearDuplicatePositions(directoryPath string, duplicates, nearDuplicates map[string]struct{}, filePattern string, ignoreEmpty bool, numDecimals int, updateName, removeDesc, clearName, roundPos, findNearDuplicates bool, tolerance float64, progressCallback func(int, int, string)) {
	var fileList []string
	err := filepath.Walk(directoryPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && strings.HasSuffix(info.Name(), strings.TrimPrefix(filePattern, "*.")) {
			fileList = append(fileList, path)
		}
		return nil
	})
	if err != nil {
		log.Printf("Error walking directory: %v", err)
		return
	}

	totalFiles := len(fileList)
	for index, filePath := range fileList {
		position, err := extractPositions(filePath)
		if err != nil {
			log.Printf("Error processing file: %s - %v", filePath, err)
			continue
		}

		if position != nil || !ignoreEmpty {
			if roundPos {
				err = roundPositionsInFile(filePath, numDecimals)
				if err != nil {
					log.Printf("Error rounding positions in file: %s - %v", filePath, err)
				}
			}

			var roundedPosition []float64
			if numDecimals >= 0 {
				roundedPosition = roundPosition(position, numDecimals, filePath)
			} else {
				roundedPosition = position
			}

			if roundedPosition != nil {
				positionKey := fmt.Sprintf("%v", roundedPosition)
				mu.Lock()
				if _, exists := positionToFiles[positionKey]; exists {
					positionToFiles[positionKey] = append(positionToFiles[positionKey], filePath)
					duplicatePositions[positionKey] = struct{}{}
					duplicates[filePath] = struct{}{}
				} else if findNearDuplicates {
					for existingPositionKey := range positionToFiles {
						existingPosition := stringToPosition(existingPositionKey)
						if nearlyEqual(roundedPosition, existingPosition, tolerance) {
							positionToFiles[existingPositionKey] = append(positionToFiles[existingPositionKey], filePath)
							nearDuplicatePositions[existingPositionKey] = struct{}{}
							nearDuplicates[filePath] = struct{}{}
							break
						}
					}
					if _, exists := nearDuplicates[filePath]; !exists {
						positionToFiles[positionKey] = []string{filePath}
					}
				} else {
					positionToFiles[positionKey] = []string{filePath}
				}
				mu.Unlock()

				if updateName {
					err = updateNameField(filePath)
					if err != nil {
						log.Printf("Error updating name field in file: %s - %v", filePath, err)
					}
				}
				if removeDesc {
					err = removeDescription(filePath)
					if err != nil {
						log.Printf("Error removing description in file: %s - %v", filePath, err)
					}
				}
				if clearName {
					err = clearNameValue(filePath)
					if err != nil {
						log.Printf("Error clearing name value in file: %s - %v", filePath, err)
					}
				}
			}
		}

		if progressCallback != nil {
			progressCallback(index+1, totalFiles, filePath)
		}
	}

	for positionKey, filePaths := range positionToFiles {
		mu.Lock()
		if _, exists := filenamesWithinGroup[positionKey]; !exists {
			filenamesWithinGroup[positionKey] = make(map[string]struct{})
		}
		for _, filePath := range filePaths {
			if _, exists := filenamesWithinGroup[positionKey][filePath]; !exists {
				filenamesWithinGroup[positionKey][filePath] = struct{}{}
				break
			}
		}
		mu.Unlock()
	}
}

func stringToPosition(s string) []float64 {
	var position []float64
	err := json.Unmarshal([]byte(s), &position)
	if err != nil {
		log.Printf("Error converting string to position: %v", err)
	}
	return position
}

func nearlyEqual(a, b []float64, tolerance float64) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if math.Abs(a[i]-b[i]) > tolerance {
			return false
		}
	}
	return true
}

func savePreferences(preferences map[string]interface{}) error {
	preferencesFile := filepath.Join(getScriptDir(), "preferences.json")
	data, err := json.MarshalIndent(preferences, "", "    ")
	if err != nil {
		return fmt.Errorf("error marshaling preferences: %w", err)
	}

	err = ioutil.WriteFile(preferencesFile, data, 0644)
	if err != nil {
		return fmt.Errorf("error saving preferences: %w", err)
	}

	return nil
}

func loadPreferences() (map[string]interface{}, error) {
	preferencesFile := filepath.Join(getScriptDir(), "preferences.json")
	if _, err := os.Stat(preferencesFile); err == nil {
		data, err := ioutil.ReadFile(preferencesFile)
		if err != nil {
			return nil, fmt.Errorf("error reading preferences file: %w", err)
		}

		var preferences map[string]interface{}
		err = json.Unmarshal(data, &preferences)
		if err != nil {
			return nil, fmt.Errorf("error parsing preferences: %w", err)
		}

		return preferences, nil
	}

	return nil, nil
}

func getScriptDir() string {
	_, filename, _, _ := runtime.Caller(0)
	return filepath.Dir(filename)
}
