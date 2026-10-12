package handler

import (
	"encoding/json"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"opspilot/internal/middleware"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/response"
	"opspilot/internal/service"
)

// ServiceHandler serves V1 service catalog HTTP endpoints.
type ServiceHandler struct {
	catalog *service.CatalogService
}

// NewServiceHandler creates a ServiceHandler.
func NewServiceHandler(catalog *service.CatalogService) *ServiceHandler {
	return &ServiceHandler{catalog: catalog}
}

type patchServiceRequest struct {
	HealthStatus  *string `json:"health_status"`
	HealthSummary *string `json:"health_summary"`
	LastCheckedAt *string `json:"last_checked_at"`
}

// List handles GET /api/v1/services.
func (h *ServiceHandler) List(c *gin.Context) {
	items, err := h.catalog.ListActive()
	if err != nil {
		writeServiceError(c, err)
		return
	}
	response.OK(c, gin.H{"items": items})
}

// Get handles GET /api/v1/services/:id.
func (h *ServiceHandler) Get(c *gin.Context) {
	view, err := h.catalog.GetActive(c.Param("id"))
	if err != nil {
		writeServiceError(c, err)
		return
	}
	response.OK(c, view)
}

// Patch handles PATCH /api/v1/services/:id.
func (h *ServiceHandler) Patch(c *gin.Context) {
	body, err := io.ReadAll(c.Request.Body)
	if err != nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}
	if len(strings.TrimSpace(string(body))) == 0 {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	var req patchServiceRequest
	if err := json.Unmarshal(body, &req); err != nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}
	if req.HealthStatus == nil && req.HealthSummary == nil && req.LastCheckedAt == nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	var checkedAt *time.Time
	if req.LastCheckedAt != nil {
		raw := strings.TrimSpace(*req.LastCheckedAt)
		if raw == "" {
			response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
			return
		}
		t, err := time.Parse(time.RFC3339, raw)
		if err != nil {
			response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
			return
		}
		checkedAt = &t
	}

	view, err := h.catalog.PatchHealth(
		middleware.GetUserID(c),
		middleware.GetRole(c),
		c.Param("id"),
		middleware.GetRequestID(c),
		service.PatchServiceHealthInput{
			HealthStatus:  req.HealthStatus,
			HealthSummary: req.HealthSummary,
			LastCheckedAt: checkedAt,
		},
	)
	if err != nil {
		writeServiceError(c, err)
		return
	}
	response.OK(c, view)
}
