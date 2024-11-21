package handlers

import (
	"log"
	"net/http"
	"text/template"
	"utils"
)

func AlertmanagerHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Giả sử nhận dữ liệu JSON từ Alertmanager (mock)
	alertData := map[string]string{
		"alertname": "High CPU Usage",
		"severity":  "critical",
	}

	// Xử lý render template
	message, err := utils.RenderTemplate("templates/message.tmpl", alertData)
	if err != nil {
		log.Printf("Failed to render template: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	// Gửi tin nhắn tới Telegram
	log.Printf("Rendered message: %s", message)
	w.Write([]byte("Alert received and processed"))
}
