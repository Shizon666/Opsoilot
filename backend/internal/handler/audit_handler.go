package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"opspilot/internal/middleware"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/response"
	"opspilot/internal/service"
)

// AuditHandler serves GET /api/v1/audit-logs.
type AuditHandler struct {
	audits *service.AuditService
}

// NewAuditHandler creates an AuditHandler.
func NewAuditHandler(audits *service.AuditService) *AuditHandler {
	return &AuditHandler{audits: audits}
}

// List handles GET /api/v1/audit-logs?request_id=.
func (h *AuditHandler) List(c *gin.Context) {
	requestID := c.Query("request_id")
	if requestID == "" {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	items, err := h.audits.ListByRequestID(middleware.GetRole(c), requestID)
	if err != nil {
		writeServiceError(c, err)
		return
	}
	response.OK(c, gin.H{"items": items})
}
