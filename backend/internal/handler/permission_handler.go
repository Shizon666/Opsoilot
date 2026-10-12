package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"opspilot/internal/middleware"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/response"
	"opspilot/internal/service"
)

// PermissionHandler serves /api/v1/permissions endpoints (Phase 5).
type PermissionHandler struct {
	accessRequests *service.AccessRequestService
}

// NewPermissionHandler creates a PermissionHandler.
func NewPermissionHandler(accessRequests *service.AccessRequestService) *PermissionHandler {
	return &PermissionHandler{accessRequests: accessRequests}
}

type createPermissionRequest struct {
	ServiceID       string `json:"service_id"`
	ResourceType    string `json:"resource_type"`
	ResourceName    string `json:"resource_name"`
	PermissionLevel string `json:"permission_level"`
	Reason          string `json:"reason"`
}

// Create handles POST /api/v1/permissions.
func (h *PermissionHandler) Create(c *gin.Context) {
	var req createPermissionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	requesterID := middleware.GetUserID(c)
	view, err := h.accessRequests.Create(requesterID, service.CreateAccessRequestInput{
		ServiceID:       req.ServiceID,
		ResourceType:    req.ResourceType,
		ResourceName:    req.ResourceName,
		PermissionLevel: req.PermissionLevel,
		Reason:          req.Reason,
	})
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, gin.H{
		"id":     view.ID,
		"status": view.Status,
	})
}

// List handles GET /api/v1/permissions.
func (h *PermissionHandler) List(c *gin.Context) {
	userID := middleware.GetUserID(c)
	role := middleware.GetRole(c)
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "20"))
	status := c.Query("status")

	result, err := h.accessRequests.List(userID, role, page, pageSize, status)
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, gin.H{
		"items":     result.Items,
		"total":     result.Total,
		"page":      result.Page,
		"page_size": result.PageSize,
	})
}

// Get handles GET /api/v1/permissions/:id.
func (h *PermissionHandler) Get(c *gin.Context) {
	userID := middleware.GetUserID(c)
	role := middleware.GetRole(c)
	id := c.Param("id")

	view, err := h.accessRequests.Get(userID, role, id)
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, view)
}

// Approve handles POST /api/v1/permissions/:id/approve.
func (h *PermissionHandler) Approve(c *gin.Context) {
	userID := middleware.GetUserID(c)
	role := middleware.GetRole(c)
	view, err := h.accessRequests.Approve(userID, role, c.Param("id"))
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, gin.H{
		"id":     view.ID,
		"status": view.Status,
	})
}

// Reject handles POST /api/v1/permissions/:id/reject.
func (h *PermissionHandler) Reject(c *gin.Context) {
	userID := middleware.GetUserID(c)
	role := middleware.GetRole(c)
	view, err := h.accessRequests.Reject(userID, role, c.Param("id"))
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, gin.H{
		"id":     view.ID,
		"status": view.Status,
	})
}
