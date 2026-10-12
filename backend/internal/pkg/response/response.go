package response

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"opspilot/internal/pkg/apperr"
)

// Body is the unified API response envelope aligned with docs/API.md.
type Body struct {
	Code    int         `json:"code"`
	Message string      `json:"message"`
	Data    interface{} `json:"data"`
}

// OK writes a successful response with code 0.
func OK(c *gin.Context, data interface{}) {
	if data == nil {
		data = gin.H{}
	}
	c.JSON(http.StatusOK, Body{
		Code:    apperr.CodeOK,
		Message: "success",
		Data:    data,
	})
}

// Fail writes a business-error response using the given application code.
func Fail(c *gin.Context, httpStatus int, code int, message string) {
	c.JSON(httpStatus, Body{
		Code:    code,
		Message: message,
		Data:    nil,
	})
}

// FailApp writes a failure using a predefined AppError.
func FailApp(c *gin.Context, httpStatus int, err apperr.AppError) {
	Fail(c, httpStatus, err.Code, err.Message)
}
