package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"

	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/jwt"
	"opspilot/internal/pkg/response"
)

const (
	contextUserID = "user_id"
	contextRole   = "role"
)

// JWT validates Bearer tokens and stores user_id / role in context.
func JWT(manager *jwt.Manager) gin.HandlerFunc {
	return func(c *gin.Context) {
		header := c.GetHeader("Authorization")
		if header == "" {
			response.FailApp(c, http.StatusUnauthorized, apperr.ErrUnauthorized)
			c.Abort()
			return
		}
		parts := strings.SplitN(header, " ", 2)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") || parts[1] == "" {
			response.FailApp(c, http.StatusUnauthorized, apperr.ErrUnauthorized)
			c.Abort()
			return
		}

		claims, err := manager.Parse(parts[1])
		if err != nil {
			response.FailApp(c, http.StatusUnauthorized, apperr.ErrUnauthorized)
			c.Abort()
			return
		}

		c.Set(contextUserID, claims.Subject)
		c.Set(contextRole, claims.Role)
		c.Next()
	}
}

// GetUserID returns the authenticated user id from context.
func GetUserID(c *gin.Context) string {
	if v, ok := c.Get(contextUserID); ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

// GetRole returns the authenticated role code (DB uppercase) from context.
func GetRole(c *gin.Context) string {
	if v, ok := c.Get(contextRole); ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}
