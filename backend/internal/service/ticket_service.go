package service

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
	"unicode/utf8"

	"opspilot/internal/model"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/repository"
)

// TicketService handles ticket business logic (Phase 4: create / list / get / patch + state machine).
type TicketService struct {
	tickets  *repository.TicketRepository
	services *repository.ServiceRepository
	users    *repository.UserRepository
	audits   *repository.AuditLogRepository
}

// NewTicketService creates a TicketService.
func NewTicketService(
	tickets *repository.TicketRepository,
	services *repository.ServiceRepository,
	users *repository.UserRepository,
	audits *repository.AuditLogRepository,
) *TicketService {
	return &TicketService{tickets: tickets, services: services, users: users, audits: audits}
}

// CreateTicketInput is the service-level create payload (no user identity fields).
type CreateTicketInput struct {
	Title       string
	Description string
	Priority    string
	ServiceID   string
	Analysis    *string
}

// PatchTicketInput is the service-level partial update payload.
// Pointer / presence flags distinguish "not sent" from empty string where needed.
type PatchTicketInput struct {
	Title       *string
	Description *string
	Priority    *string
	Status      *string
	AssigneeID  *string
	Analysis    *string
	Resolution  *string
}

// TicketView is the API-facing ticket representation.
// creator_id maps from DB requester_id (Plan R4).
type TicketView struct {
	ID          string    `json:"id"`
	TicketNo    string    `json:"ticket_no"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Status      string    `json:"status"`
	Priority    string    `json:"priority"`
	CreatorID   string    `json:"creator_id"`
	AssigneeID  *string   `json:"assignee_id,omitempty"`
	ServiceID   string    `json:"service_id"`
	Analysis    *string   `json:"analysis"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// TicketListResult is a paginated ticket list.
type TicketListResult struct {
	Items    []TicketView
	Total    int64
	Page     int
	PageSize int
}

// Create creates a ticket for the authenticated creator (JWT user_id).
func (s *TicketService) Create(creatorID, requestID string, in CreateTicketInput) (*TicketView, error) {
	if creatorID == "" {
		return nil, apperr.ErrUnauthorized
	}

	title := strings.TrimSpace(in.Title)
	description := strings.TrimSpace(in.Description)
	if title == "" || description == "" {
		return nil, apperr.ErrInvalidRequest
	}
	if utf8.RuneCountInString(title) > 200 {
		return nil, apperr.ErrInvalidRequest
	}

	priority, ok := normalizePriority(in.Priority)
	if !ok {
		return nil, apperr.ErrInvalidRequest
	}

	serviceID := strings.TrimSpace(in.ServiceID)
	if serviceID == "" || !isUUID(serviceID) {
		return nil, apperr.ErrInvalidRequest
	}
	svc, err := s.services.GetByID(serviceID)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrInvalidRequest
		}
		return nil, apperr.ErrDatabase
	}
	if svc.Status != model.ServiceStatusActive {
		return nil, apperr.ErrInvalidRequest
	}

	now := time.Now().UTC()
	ticket := &model.Ticket{
		TicketNo:    generateTicketNo(),
		RequesterID: creatorID,
		ServiceID:   serviceID,
		Title:       title,
		Description: description,
		Priority:    priority,
		Status:      model.TicketStatusOpen,
		Analysis:    optionalTrimmedText(in.Analysis),
		CreatedAt:   now,
		UpdatedAt:   now,
	}

	if err := s.tickets.Create(ticket); err != nil {
		return nil, apperr.ErrDatabase
	}

	if err := appendAuditLog(s.audits, creatorID, requestID, auditActionTicketCreate, auditResourceTicket, ticket.ID); err != nil {
		return nil, apperr.ErrDatabase
	}

	view := toTicketView(ticket)
	return &view, nil
}

// List returns tickets visible to the current role.
// EMPLOYEE: own tickets only. IT_SUPPORT / ADMIN: all tickets.
func (s *TicketService) List(userID, role string, page, pageSize int, status, q, serviceID string) (*TicketListResult, error) {
	if userID == "" {
		return nil, apperr.ErrUnauthorized
	}
	if page <= 0 {
		page = 1
	}
	if pageSize <= 0 {
		pageSize = 20
	}
	if pageSize > 100 {
		pageSize = 100
	}

	dbStatus := ""
	if status != "" {
		normalized, ok := normalizeTicketStatus(status)
		if !ok {
			return nil, apperr.ErrInvalidRequest
		}
		dbStatus = normalized
	}

	q = strings.TrimSpace(q)
	if utf8.RuneCountInString(q) > 100 {
		return nil, apperr.ErrInvalidRequest
	}

	serviceID = strings.TrimSpace(serviceID)
	if serviceID != "" && !isUUID(serviceID) {
		return nil, apperr.ErrInvalidRequest
	}

	filter := repository.TicketListFilter{
		Status:    dbStatus,
		ServiceID: serviceID,
		Q:         q,
		Limit:     pageSize,
		Offset:    (page - 1) * pageSize,
	}
	if !isSupportRole(role) {
		filter.RequesterID = userID
	}

	items, total, err := s.tickets.List(filter)
	if err != nil {
		return nil, apperr.ErrDatabase
	}

	views := make([]TicketView, 0, len(items))
	for i := range items {
		views = append(views, toTicketView(&items[i]))
	}

	return &TicketListResult{
		Items:    views,
		Total:    total,
		Page:     page,
		PageSize: pageSize,
	}, nil
}

// Get returns a ticket by id subject to role visibility.
func (s *TicketService) Get(userID, role, ticketID string) (*TicketView, error) {
	if userID == "" {
		return nil, apperr.ErrUnauthorized
	}
	ticketID = strings.TrimSpace(ticketID)
	if ticketID == "" {
		return nil, apperr.ErrInvalidRequest
	}

	ticket, err := s.tickets.GetByID(ticketID)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrNotFound
		}
		return nil, apperr.ErrDatabase
	}

	if !canViewTicket(userID, role, ticket) {
		return nil, apperr.ErrNotFound
	}

	view := toTicketView(ticket)
	return &view, nil
}

// Patch applies a partial update with field-level role checks and status machine.
func (s *TicketService) Patch(userID, role, ticketID, requestID string, in PatchTicketInput) (*TicketView, error) {
	if userID == "" {
		return nil, apperr.ErrUnauthorized
	}
	ticketID = strings.TrimSpace(ticketID)
	if ticketID == "" {
		return nil, apperr.ErrInvalidRequest
	}
	if in.Title == nil && in.Description == nil && in.Priority == nil && in.Status == nil && in.AssigneeID == nil && in.Analysis == nil && in.Resolution == nil {
		return nil, apperr.ErrInvalidRequest
	}

	ticket, err := s.tickets.GetByID(ticketID)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrNotFound
		}
		return nil, apperr.ErrDatabase
	}

	support := isSupportRole(role)
	if !support {
		if ticket.RequesterID != userID {
			return nil, apperr.ErrForbidden
		}
		// Employee may only update title/description/priority, and may resume
		// WAITING_USER → IN_PROGRESS after supplementing. analysis/resolution/assignee are Support-only.
		if in.AssigneeID != nil || in.Resolution != nil || in.Analysis != nil {
			return nil, apperr.ErrForbidden
		}
	}

	fields := map[string]interface{}{}
	now := time.Now().UTC()

	if in.Title != nil {
		title := strings.TrimSpace(*in.Title)
		if title == "" || utf8.RuneCountInString(title) > 200 {
			return nil, apperr.ErrInvalidRequest
		}
		fields["title"] = title
	}
	if in.Description != nil {
		description := strings.TrimSpace(*in.Description)
		if description == "" {
			return nil, apperr.ErrInvalidRequest
		}
		fields["description"] = description
	}
	if in.Priority != nil {
		priority, ok := normalizePriority(*in.Priority)
		if !ok {
			return nil, apperr.ErrInvalidRequest
		}
		fields["priority"] = priority
	}

	newStatus := ticket.Status
	if in.Status != nil {
		target, ok := normalizeTicketStatus(*in.Status)
		if !ok {
			return nil, apperr.ErrInvalidRequest
		}
		if !support {
			// Requester: only resume from waiting_user after providing more info.
			if ticket.Status != model.TicketStatusWaitingUser || target != model.TicketStatusInProgress {
				return nil, apperr.ErrForbidden
			}
		}
		if !canTransition(ticket.Status, target) {
			return nil, apperr.ErrConflict
		}
		// Support must leave a note in analysis when asking the user to act.
		if support && target == model.TicketStatusWaitingUser {
			nextAnalysis := ticket.Analysis
			if in.Analysis != nil {
				nextAnalysis = optionalTrimmedText(in.Analysis)
			}
			if nextAnalysis == nil {
				return nil, apperr.ErrInvalidRequest
			}
		}
		fields["status"] = target
		newStatus = target
		if target == model.TicketStatusResolved {
			fields["resolved_at"] = now
		}
		if target == model.TicketStatusClosed {
			fields["closed_at"] = now
		}
	}

	if in.AssigneeID != nil {
		if !support {
			return nil, apperr.ErrForbidden
		}
		assigneeID := strings.TrimSpace(*in.AssigneeID)
		if assigneeID == "" {
			return nil, apperr.ErrInvalidRequest
		}
		assignee, err := s.users.GetByID(assigneeID)
		if err != nil {
			if repository.IsNotFound(err) {
				return nil, apperr.ErrInvalidRequest
			}
			return nil, apperr.ErrDatabase
		}
		if assignee.Status != model.UserStatusActive {
			return nil, apperr.ErrInvalidRequest
		}
		fields["assignee_id"] = assigneeID
	} else if in.Status != nil && newStatus == model.TicketStatusAssigned && ticket.AssigneeID == nil {
		// Transition into ASSIGNED without assignee_id: default to current support user.
		fields["assignee_id"] = userID
	}

	if in.Analysis != nil {
		if !support {
			return nil, apperr.ErrForbidden
		}
		if v := optionalTrimmedText(in.Analysis); v == nil {
			fields["analysis"] = nil
		} else {
			fields["analysis"] = *v
		}
	}
	if in.Resolution != nil {
		if !support {
			return nil, apperr.ErrForbidden
		}
		if v := optionalTrimmedText(in.Resolution); v == nil {
			fields["resolution"] = nil
		} else {
			fields["resolution"] = *v
		}
	}

	if len(fields) == 0 {
		return nil, apperr.ErrInvalidRequest
	}
	fields["updated_at"] = now

	if err := s.tickets.UpdateFields(ticketID, fields); err != nil {
		return nil, apperr.ErrDatabase
	}

	// Phase 6 Lite: append audit after successful write (no ticket transaction refactor).
	if err := appendAuditLog(s.audits, userID, requestID, auditActionTicketUpdate, auditResourceTicket, ticketID); err != nil {
		return nil, apperr.ErrDatabase
	}

	updated, err := s.tickets.GetByID(ticketID)
	if err != nil {
		return nil, apperr.ErrDatabase
	}
	view := toTicketView(updated)
	return &view, nil
}

func canViewTicket(userID, role string, ticket *model.Ticket) bool {
	if isSupportRole(role) {
		return true
	}
	return ticket.RequesterID == userID
}

func isSupportRole(role string) bool {
	switch strings.ToUpper(strings.TrimSpace(role)) {
	case model.RoleCodeITSupport, model.RoleCodeAdmin:
		return true
	default:
		return false
	}
}

func toTicketView(t *model.Ticket) TicketView {
	return TicketView{
		ID:          t.ID,
		TicketNo:    t.TicketNo,
		Title:       t.Title,
		Description: t.Description,
		Status:      statusToAPI(t.Status),
		Priority:    priorityToAPI(t.Priority),
		CreatorID:   t.RequesterID,
		AssigneeID:  t.AssigneeID,
		ServiceID:   t.ServiceID,
		Analysis:    t.Analysis,
		CreatedAt:   t.CreatedAt,
		UpdatedAt:   t.UpdatedAt,
	}
}

func normalizePriority(raw string) (string, bool) {
	switch strings.ToUpper(strings.TrimSpace(raw)) {
	case "":
		return model.TicketPriorityMedium, true
	case model.TicketPriorityLow:
		return model.TicketPriorityLow, true
	case model.TicketPriorityMedium:
		return model.TicketPriorityMedium, true
	case model.TicketPriorityHigh:
		return model.TicketPriorityHigh, true
	case model.TicketPriorityUrgent:
		return model.TicketPriorityUrgent, true
	default:
		return "", false
	}
}

func normalizeTicketStatus(raw string) (string, bool) {
	status := strings.ToUpper(strings.TrimSpace(raw))
	if !isKnownTicketStatus(status) {
		return "", false
	}
	return status, true
}

func statusToAPI(status string) string {
	return strings.ToLower(status)
}

func priorityToAPI(priority string) string {
	return strings.ToLower(priority)
}

func generateTicketNo() string {
	var b [4]byte
	if _, err := rand.Read(b[:]); err != nil {
		return fmt.Sprintf("OPS-%d", time.Now().UTC().UnixNano())
	}
	return fmt.Sprintf("OPS-%s-%s", time.Now().UTC().Format("20060102"), hex.EncodeToString(b[:]))
}

// Phase 6 Lite fixed action strings (do not invent synonyms).
const (
	auditActionTicketCreate         = "ticket.create"
	auditActionTicketUpdate         = "ticket.update"
	auditActionAccessRequestCreate  = "access_request.create"
	auditActionAccessRequestApprove = "access_request.approve"
	auditActionAccessRequestReject  = "access_request.reject"
)

const (
	auditResourceTicket        = "ticket"
	auditResourceAccessRequest = "access_request"
)

// appendAuditLog writes one SUCCESS audit row via AuditLogRepository (no AuditService).
func appendAuditLog(repo *repository.AuditLogRepository, actorID, requestID, action, resourceType, resourceID string) error {
	actor := actorID
	resource := resourceID
	log := &model.AuditLog{
		ActorID:      &actor,
		ActorType:    model.ActorTypeUser,
		Action:       action,
		ResourceType: resourceType,
		ResourceID:   &resource,
		Result:       model.AuditResultSuccess,
		CreatedAt:    time.Now().UTC(),
	}
	if rid := strings.TrimSpace(requestID); rid != "" {
		log.RequestID = &rid
	}
	return repo.Create(log)
}

func optionalTrimmedText(in *string) *string {
	if in == nil {
		return nil
	}
	v := strings.TrimSpace(*in)
	if v == "" {
		return nil
	}
	return &v
}
