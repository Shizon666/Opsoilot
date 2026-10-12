package handler

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"

	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/response"
	"opspilot/internal/service"
)

// AuthHandler serves auth HTTP endpoints.
type AuthHandler struct {
	auth *service.AuthService
}

// NewAuthHandler creates an AuthHandler.
func NewAuthHandler(auth *service.AuthService) *AuthHandler {
	return &AuthHandler{auth: auth}
}

type loginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// Login handles POST /api/v1/auth/login.
func (h *AuthHandler) Login(c *gin.Context) {
	var req loginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	result, err := h.auth.Login(req.Username, req.Password)
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, gin.H{
		"token":      result.Token,
		"expires_in": result.ExpiresIn,
		"user": gin.H{
			"id":       result.User.ID,
			"username": result.User.Username,
			"name":     result.User.Name,
			"role":     result.User.Role,
		},
	})
}

func writeServiceError(c *gin.Context, err error) {
	var appErr apperr.AppError
	if errors.As(err, &appErr) {
		switch appErr.Code {
		case apperr.CodeInvalidRequest:
			response.FailApp(c, http.StatusBadRequest, appErr)
		case apperr.CodeUnauthorized:
			response.FailApp(c, http.StatusUnauthorized, appErr)
		case apperr.CodeForbidden:
			response.FailApp(c, http.StatusForbidden, appErr)
		case apperr.CodeNotFound:
			response.FailApp(c, http.StatusNotFound, appErr)
		case apperr.CodeConflict:
			response.FailApp(c, http.StatusConflict, appErr)
		default:
			response.FailApp(c, http.StatusInternalServerError, appErr)
		}
		return
	}
	response.FailApp(c, http.StatusInternalServerError, apperr.ErrInternal)
}
