package handler

import (
	"github.com/gin-gonic/gin"

	"opspilot/internal/middleware"
	"opspilot/internal/pkg/response"
	"opspilot/internal/service"
)

// UserHandler serves user HTTP endpoints.
type UserHandler struct {
	users *service.UserService
}

// NewUserHandler creates a UserHandler.
func NewUserHandler(users *service.UserService) *UserHandler {
	return &UserHandler{users: users}
}

// Me handles GET /api/v1/users/me.
func (h *UserHandler) Me(c *gin.Context) {
	userID := middleware.GetUserID(c)
	view, err := h.users.Me(userID)
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, gin.H{
		"id":             view.ID,
		"username":       view.Username,
		"name":           view.Name,
		"department":     view.Department,
		"position":       view.Position,
		"employee_level": view.EmployeeLevel,
		"role":           view.Role,
	})
}
