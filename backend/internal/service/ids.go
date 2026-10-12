package service

import (
	"regexp"
	"strings"
)

var uuidRE = regexp.MustCompile(`(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)

func isUUID(raw string) bool {
	return uuidRE.MatchString(strings.TrimSpace(raw))
}
