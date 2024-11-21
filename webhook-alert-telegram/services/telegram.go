package services

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
)

type TelegramPayload struct {
	ChatID    string `json:"chat_id"`
	Text      string `json:"text"`
	ParseMode string `json:"parse_mode"`
}

func SendToTelegram(botToken, chatID, message string) error {
	apiURL := "https://api.telegram.org/bot" + botToken + "/sendMessage"

	payload := TelegramPayload{
		ChatID:    chatID,
		Text:      message,
		ParseMode: "HTML",
	}

	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	resp, err := http.Post(apiURL, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Telegram API response: %s", resp.Status)
	}
	return nil
}
