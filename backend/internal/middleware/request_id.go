package middleware

import (
	"crypto/rand"
	"encoding/hex"

	"github.com/gin-gonic/gin"
)

const (
	headerRequestID = "X-Request-ID"
	contextRequestID = "request_id"
)

// RequestID ensures every request has an X-Request-ID and stores it in context.
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		rid := c.GetHeader(headerRequestID)
		if rid == "" {
			rid = newRequestID()
		}
		c.Set(contextRequestID, rid)
		c.Writer.Header().Set(headerRequestID, rid)
		c.Next()
	}
}

// GetRequestID returns the request ID from the Gin context, or empty string.
func GetRequestID(c *gin.Context) string {
	if v, ok := c.Get(contextRequestID); ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

func newRequestID() string {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "req-fallback"
	}
	return hex.EncodeToString(b)
}
