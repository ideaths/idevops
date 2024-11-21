package main

import (
	"log"
	"net/http"
	"os"

	"handlers"
)

func initLogger() *os.File {
	// Tạo hoặc mở file log
	logFile, err := os.OpenFile("logs/app.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}

	// Đặt log ghi cả ra file và stdout
	log.SetOutput(logFile)
	log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)
	return logFile
}

func main() {
	// Khởi tạo logger
	logFile := initLogger()
	defer logFile.Close()

	// Router cho ứng dụng
	http.HandleFunc("/alertmanager", handlers.AlertmanagerHandler)
	http.HandleFunc("/logs", handlers.ViewLogHandler)

	// Chạy server
	log.Println("Starting server on :5000")
	if err := http.ListenAndServe(":5000", nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
