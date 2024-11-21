package handlers

import (
	"net/http"
	"os"
	"path/filepath"
)

func ViewLogHandler(w http.ResponseWriter, r *http.Request) {
	// Đường dẫn file log
	logFile := "logs/app.log"

	// Mở file log
	file, err := os.Open(logFile)
	if err != nil {
		http.Error(w, "Unable to open log file", http.StatusInternalServerError)
		return
	}
	defer file.Close()

	// Đọc nội dung file log
	http.ServeFile(w, r, filepath.Clean(logFile))
}
