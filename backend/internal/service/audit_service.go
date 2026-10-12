package service

import (
	"strings"

	"opspilot/internal/pkg/apperr"
	"opspilot/internal/repository"
)

// AuditService handles append-only audit queries (Phase B).
type AuditService struct {
	audits *repository.AuditLogRepository
}

// NewAuditService creates an AuditService.
func NewAuditService(audits *repository.AuditLogRepository) *AuditService {
	return &AuditService{audits: audits}
}

// AuditLogView is the API-facing audit row (no secrets / prompt).
type AuditLogView struct {
	ID           string  `json:"id"`
	RequestID    *string `json:"request_id"`
	ActorID      *string `json:"actor_id"`
	ActorType    string  `json:"actor_type"`
	Action       string  `json:"action"`
	ResourceType string  `json:"resource_type"`
	ResourceID   *string `json:"resource_id"`
	Result       string  `json:"result"`
	CreatedAt    string  `json:"created_at"`
}

// ListByRequestID returns the full chain for one request_id. Support/Admin only.
func (s *AuditService) ListByRequestID(role, requestID string) ([]AuditLogView, error) {
	if !isSupportRole(role) {
		return nil, apperr.ErrForbidden
	}
	requestID = strings.TrimSpace(requestID)
	if requestID == "" {
		return nil, apperr.ErrInvalidRequest
	}

	items, err := s.audits.ListByRequestID(requestID)
	if err != nil {
		return nil, apperr.ErrDatabase
	}

	views := make([]AuditLogView, 0, len(items))
	for i := range items {
		created := items[i].CreatedAt.UTC().Format("2006-01-02T15:04:05Z")
		views = append(views, AuditLogView{
			ID:           items[i].ID,
			RequestID:    items[i].RequestID,
			ActorID:      items[i].ActorID,
			ActorType:    items[i].ActorType,
			Action:       items[i].Action,
			ResourceType: items[i].ResourceType,
			ResourceID:   items[i].ResourceID,
			Result:       items[i].Result,
			CreatedAt:    created,
		})
	}
	return views, nil
}
