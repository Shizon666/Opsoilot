package service

import (
	"strings"
	"time"

	"opspilot/internal/model"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/repository"
)

const auditActionServiceHealthUpdate = "service.health_update"
const auditResourceService = "service"

// CatalogService handles V1 service catalog + simulated health.
type CatalogService struct {
	services *repository.ServiceRepository
	audits   *repository.AuditLogRepository
}

// NewCatalogService creates a CatalogService.
func NewCatalogService(services *repository.ServiceRepository, audits *repository.AuditLogRepository) *CatalogService {
	return &CatalogService{services: services, audits: audits}
}

// ServiceView is the API-facing service representation.
type ServiceView struct {
	ID            string     `json:"id"`
	Code          string     `json:"code"`
	Name          string     `json:"name"`
	Description   *string    `json:"description"`
	Category      string     `json:"category"`
	Status        string     `json:"status"`
	HealthStatus  string     `json:"health_status"`
	HealthSummary *string    `json:"health_summary"`
	LastCheckedAt *time.Time `json:"last_checked_at"`
}

// PatchServiceHealthInput is the partial health update payload.
type PatchServiceHealthInput struct {
	HealthStatus  *string
	HealthSummary *string
	LastCheckedAt *time.Time
}

// ListActive returns ACTIVE services only (no pagination; V1 ≤ 10).
func (s *CatalogService) ListActive() ([]ServiceView, error) {
	items, err := s.services.ListActive()
	if err != nil {
		return nil, apperr.ErrDatabase
	}
	views := make([]ServiceView, 0, len(items))
	for i := range items {
		views = append(views, toServiceView(&items[i]))
	}
	return views, nil
}

// GetActive returns one ACTIVE service; INACTIVE is treated as not found.
func (s *CatalogService) GetActive(id string) (*ServiceView, error) {
	id = strings.TrimSpace(id)
	if id == "" || !isUUID(id) {
		return nil, apperr.ErrInvalidRequest
	}
	svc, err := s.services.GetByID(id)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrNotFound
		}
		return nil, apperr.ErrDatabase
	}
	if svc.Status != model.ServiceStatusActive {
		return nil, apperr.ErrNotFound
	}
	view := toServiceView(svc)
	return &view, nil
}

// PatchHealth updates simulated health fields. Support/Admin only.
func (s *CatalogService) PatchHealth(userID, role, id string, requestID string, in PatchServiceHealthInput) (*ServiceView, error) {
	if userID == "" {
		return nil, apperr.ErrUnauthorized
	}
	if !isSupportRole(role) {
		return nil, apperr.ErrForbidden
	}
	id = strings.TrimSpace(id)
	if id == "" || !isUUID(id) {
		return nil, apperr.ErrInvalidRequest
	}
	if in.HealthStatus == nil && in.HealthSummary == nil && in.LastCheckedAt == nil {
		return nil, apperr.ErrInvalidRequest
	}

	svc, err := s.services.GetByID(id)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrNotFound
		}
		return nil, apperr.ErrDatabase
	}
	if svc.Status != model.ServiceStatusActive {
		return nil, apperr.ErrNotFound
	}

	now := time.Now().UTC()
	fields := map[string]interface{}{
		"updated_at": now,
	}

	if in.HealthStatus != nil {
		status, ok := normalizeHealthStatus(*in.HealthStatus)
		if !ok {
			return nil, apperr.ErrInvalidRequest
		}
		fields["health_status"] = status
	}
	if in.HealthSummary != nil {
		summary := strings.TrimSpace(*in.HealthSummary)
		if summary == "" {
			fields["health_summary"] = nil
		} else {
			fields["health_summary"] = summary
		}
	}
	if in.LastCheckedAt != nil {
		fields["last_checked_at"] = in.LastCheckedAt.UTC()
	} else {
		fields["last_checked_at"] = now
	}

	if err := s.services.UpdateFields(id, fields); err != nil {
		return nil, apperr.ErrDatabase
	}
	if err := appendAuditLog(s.audits, userID, requestID, auditActionServiceHealthUpdate, auditResourceService, id); err != nil {
		return nil, apperr.ErrDatabase
	}

	updated, err := s.services.GetByID(id)
	if err != nil {
		return nil, apperr.ErrDatabase
	}
	view := toServiceView(updated)
	return &view, nil
}

func normalizeHealthStatus(raw string) (string, bool) {
	switch strings.ToUpper(strings.TrimSpace(raw)) {
	case model.ServiceHealthHealthy:
		return model.ServiceHealthHealthy, true
	case model.ServiceHealthDegraded:
		return model.ServiceHealthDegraded, true
	case model.ServiceHealthDown:
		return model.ServiceHealthDown, true
	default:
		return "", false
	}
}

func toServiceView(svc *model.Service) ServiceView {
	return ServiceView{
		ID:            svc.ID,
		Code:          svc.Code,
		Name:          svc.Name,
		Description:   svc.Description,
		Category:      svc.Category,
		Status:        svc.Status,
		HealthStatus:  svc.HealthStatus,
		HealthSummary: svc.HealthSummary,
		LastCheckedAt: svc.LastCheckedAt,
	}
}
