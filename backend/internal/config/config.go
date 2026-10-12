package config

import (
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

// Config holds runtime settings for the Go Business API.
type Config struct {
	Host     string
	Port     string
	Database DatabaseConfig
	JWT      JWTConfig
}

// DatabaseConfig holds PostgreSQL connection settings.
type DatabaseConfig struct {
	URL string
}

// JWTConfig holds JWT signing settings.
type JWTConfig struct {
	Secret      string
	ExpireHours int
}

// Load reads configuration from environment variables.
// For local development it optionally loads OpsPilot/.env first.
// Priority: existing process env > OpsPilot/.env > code defaults.
// godotenv.Load does not override variables already set in the environment.
func Load() Config {
	loadDotEnv()

	return Config{
		Host: getEnv("BACKEND_HOST", "0.0.0.0"),
		Port: getEnv("BACKEND_PORT", "8080"),
		Database: DatabaseConfig{
			URL: getEnv("DATABASE_URL", ""),
		},
		JWT: JWTConfig{
			Secret:      getEnv("JWT_SECRET", ""),
			ExpireHours: getEnvInt("JWT_EXPIRE_HOURS", 24),
		},
	}
}

// loadDotEnv tries common paths for the repo-root .env (cwd may be OpsPilot/ or backend/).
// Missing files are ignored; load errors are logged and do not block startup.
func loadDotEnv() {
	candidates := []string{".env", "../.env"}
	for _, path := range candidates {
		if _, err := os.Stat(path); err != nil {
			continue
		}
		if err := godotenv.Load(path); err != nil {
			log.Printf("config: load %s: %v (continuing with process env)", path, err)
			return
		}
		return
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return fallback
	}
	return n
}
