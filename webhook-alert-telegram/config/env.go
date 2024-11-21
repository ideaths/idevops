package config

import "os"

// GetEnv lấy giá trị từ biến môi trường hoặc giá trị mặc định
func GetEnv(key, defaultValue string) string {
	value, exists := os.LookupEnv(key)
	if !exists {
		return defaultValue
	}
	return value
}
