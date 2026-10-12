package handler

import (
	"encoding/json"
	"io"
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"opspilot/internal/middleware"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/response"
	"opspilot/internal/service"
)

// TicketHandler serves ticket HTTP endpoints (Phase 4).
type TicketHandler struct {
	tickets *service.TicketService
}

// NewTicketHandler creates a TicketHandler.
func NewTicketHandler(tickets *service.TicketService) *TicketHandler {
	return &TicketHandler{tickets: tickets}
}

type createTicketRequest struct {
	Title       string  `json:"title"`
	Description string  `json:"description"`
	Priority    string  `json:"priority"`
	ServiceID   string  `json:"service_id"`
	Analysis    *string `json:"analysis"`
}

// patchTicketRequest uses pointers so omitted fields stay nil.
type patchTicketRequest struct {
	Title       *string `json:"title"`
	Description *string `json:"description"`
	Priority    *string `json:"priority"`
	Status      *string `json:"status"`
	AssigneeID  *string `json:"assignee_id"`
	Analysis    *string `json:"analysis"`
	Resolution  *string `json:"resolution"`
}

// Create handles POST /api/v1/tickets.
func (h *TicketHandler) Create(c *gin.Context) {
	var req createTicketRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	creatorID := middleware.GetUserID(c)
	view, err := h.tickets.Create(creatorID, middleware.GetRequestID(c), service.CreateTicketInput{
		Title:       req.Title,
		Description: req.Description,
		Priority:    req.Priority,
		ServiceID:   req.ServiceID,
		Analysis:    req.Analysis,
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

// List handles GET /api/v1/tickets.
func (h *TicketHandler) List(c *gin.Context) {
	userID := middleware.GetUserID(c)
	role := middleware.GetRole(c)
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "20"))
	status := c.Query("status")
	q := c.Query("q")
	serviceID := c.Query("service_id")

	result, err := h.tickets.List(userID, role, page, pageSize, status, q, serviceID)
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

// Get handles GET /api/v1/tickets/:id.
func (h *TicketHandler) Get(c *gin.Context) {
	userID := middleware.GetUserID(c)
	role := middleware.GetRole(c)
	id := c.Param("id")

	view, err := h.tickets.Get(userID, role, id)
	if err != nil {
		writeServiceError(c, err)
		return
	}

	response.OK(c, view)
}

// Patch handles PATCH /api/v1/tickets/:id.
func (h *TicketHandler) Patch(c *gin.Context) {
	body, err := io.ReadAll(c.Request.Body)
	if err != nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}
	if len(strings.TrimSpace(string(body))) == 0 {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	var req patchTicketRequest
	if err := json.Unmarshal(body, &req); err != nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}
	if req.Title == nil && req.Description == nil && req.Priority == nil && req.Status == nil && req.AssigneeID == nil && req.Analysis == nil && req.Resolution == nil {
		response.FailApp(c, http.StatusBadRequest, apperr.ErrInvalidRequest)
		return
	}

	userID := middleware.GetUserID(c)
	role := middleware.GetRole(c)
	view, err := h.tickets.Patch(userID, role, c.Param("id"), middleware.GetRequestID(c), service.PatchTicketInput{
		Title:       req.Title,
		Description: req.Description,
		Priority:    req.Priority,
		Status:      req.Status,
		AssigneeID:  req.AssigneeID,
		Analysis:    req.Analysis,
		Resolution:  req.Resolution,
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
