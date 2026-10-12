package middleware

import (
	"log"
	"net/http"

	"github.com/gin-gonic/gin"

	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/response"
)

// Recovery catches panics and returns a unified internal-error response.
func Recovery() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if rec := recover(); rec != nil {
				log.Printf("panic recovered: %v request_id=%s", rec, GetRequestID(c))
				response.FailApp(c, http.StatusInternalServerError, apperr.ErrInternal)
				c.Abort()
			}
		}()
		c.Next()
	}
}
