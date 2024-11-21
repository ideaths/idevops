package utils

import (
	"bytes"
	"text/template"
)

// RenderTemplate đọc và render một template với dữ liệu cung cấp
func RenderTemplate(filePath string, data interface{}) (string, error) {
	tmpl, err := template.ParseFiles(filePath)
	if err != nil {
		return "", err
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, data); err != nil {
		return "", err
	}

	return buf.String(), nil
}
