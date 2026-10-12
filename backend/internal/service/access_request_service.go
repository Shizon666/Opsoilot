package service

import (
	"strings"
	"time"
	"unicode/utf8"

	"gorm.io/gorm"

	"opspilot/internal/model"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/repository"
)

// AccessRequestService handles permission request + single-level approval (Phase 5).
type AccessRequestService struct {
	db             *gorm.DB
	accessRequests *repository.AccessRequestRepository
	approvals      *repository.ApprovalRepository
	services       *repository.ServiceRepository
}

// NewAccessRequestService creates an AccessRequestService.
func NewAccessRequestService(
	db *gorm.DB,
	accessRequests *repository.AccessRequestRepository,
	approvals *repository.ApprovalRepository,
	services *repository.ServiceRepository,
) *AccessRequestService {
	return &AccessRequestService{
		db:             db,
		accessRequests: accessRequests,
		approvals:      approvals,
		services:       services,
	}
}

// CreateAccessRequestInput is the service-level create payload (no user identity fields).
type CreateAccessRequestInput struct {
	ServiceID       string
	ResourceType    string
	ResourceName    string
	PermissionLevel string
	Reason          string
}

// AccessRequestView is the API-facing access request representation.
type AccessRequestView struct {
	ID              string    `json:"id"`
	RequesterID     string    `json:"requester_id"`
	ServiceID       string    `json:"service_id"`
	ResourceType    string    `json:"resource_type"`
	ResourceName    string    `json:"resource_name"`
	PermissionLevel string    `json:"permission_level"`
	Reason          string    `json:"reason"`
	Status          string    `json:"status"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

// AccessRequestListResult is a paginated access request list.
type AccessRequestListResult struct {
	Items    []AccessRequestView
	Total    int64
	Page     int
	PageSize int
}

// Create creates an access request + pending approval in one transaction.
func (s *AccessRequestService) Create(requesterID string, in CreateAccessRequestInput) (*AccessRequestView, error) {
	if requesterID == "" {
		return nil, apperr.ErrUnauthorized
	}

	resourceType, ok := normalizeResourceType(in.ResourceType)
	if !ok {
		return nil, apperr.ErrInvalidRequest
	}
	resourceName := strings.TrimSpace(in.ResourceName)
	if resourceName == "" || utf8.RuneCountInString(resourceName) > 200 {
		return nil, apperr.ErrInvalidRequest
	}
	permissionLevel, ok := normalizePermissionLevel(in.PermissionLevel)
	if !ok {
		return nil, apperr.ErrInvalidRequest
	}
	reason := strings.TrimSpace(in.Reason)
	if reason == "" {
		return nil, apperr.ErrInvalidRequest
	}

	serviceID := strings.TrimSpace(in.ServiceID)
	if serviceID == "" {
		serviceID = model.DefaultServiceID
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
	ar := &model.AccessRequest{
		RequesterID:     requesterID,
		ServiceID:       serviceID,
		ResourceType:    resourceType,
		ResourceName:    resourceName,
		PermissionLevel: permissionLevel,
		Reason:          reason,
		Status:          model.AccessRequestStatusPending,
		CreatedAt:       now,
		UpdatedAt:       now,
	}

	err = s.db.Transaction(func(tx *gorm.DB) error {
		arRepo := repository.NewAccessRequestRepository(tx)
		apRepo := repository.NewApprovalRepository(tx)
		auditRepo := repository.NewAuditLogRepository(tx)

		if err := arRepo.Create(ar); err != nil {
			return err
		}
		approval := &model.Approval{
			AccessRequestID: ar.ID,
			ApproverID:      nil,
			Status:          model.ApprovalStatusPending,
			CreatedAt:       now,
			UpdatedAt:       now,
		}
		if err := apRepo.Create(approval); err != nil {
			return err
		}
		return appendAuditLog(auditRepo, requesterID, "", auditActionAccessRequestCreate, auditResourceAccessRequest, ar.ID)
	})
	if err != nil {
		return nil, apperr.ErrDatabase
	}

	view := toAccessRequestView(ar)
	return &view, nil
}

// List returns access requests visible to the current role.
// EMPLOYEE: own requests only. IT_SUPPORT / ADMIN: all.
func (s *AccessRequestService) List(userID, role string, page, pageSize int, status string) (*AccessRequestListResult, error) {
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
		normalized, ok := normalizeAccessRequestStatus(status)
		if !ok {
			return nil, apperr.ErrInvalidRequest
		}
		dbStatus = normalized
	}

	filter := repository.AccessRequestListFilter{
		Status: dbStatus,
		Limit:  pageSize,
		Offset: (page - 1) * pageSize,
	}
	if !isSupportRole(role) {
		filter.RequesterID = userID
	}

	items, total, err := s.accessRequests.List(filter)
	if err != nil {
		return nil, apperr.ErrDatabase
	}

	views := make([]AccessRequestView, 0, len(items))
	for i := range items {
		views = append(views, toAccessRequestView(&items[i]))
	}

	return &AccessRequestListResult{
		Items:    views,
		Total:    total,
		Page:     page,
		PageSize: pageSize,
	}, nil
}

// Get returns an access request by id subject to role visibility.
// Non-owner Employee → 40401 (same as Ticket).
func (s *AccessRequestService) Get(userID, role, id string) (*AccessRequestView, error) {
	if userID == "" {
		return nil, apperr.ErrUnauthorized
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return nil, apperr.ErrInvalidRequest
	}

	ar, err := s.accessRequests.GetByID(id)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrNotFound
		}
		return nil, apperr.ErrDatabase
	}

	if !canViewAccessRequest(userID, role, ar) {
		return nil, apperr.ErrNotFound
	}

	view := toAccessRequestView(ar)
	return &view, nil
}

// Approve approves a pending access request (IT_SUPPORT / ADMIN only).
func (s *AccessRequestService) Approve(userID, role, id string) (*AccessRequestView, error) {
	return s.decide(userID, role, id, model.AccessRequestStatusApproved, model.ApprovalStatusApproved)
}

// Reject rejects a pending access request (IT_SUPPORT / ADMIN only).
func (s *AccessRequestService) Reject(userID, role, id string) (*AccessRequestView, error) {
	return s.decide(userID, role, id, model.AccessRequestStatusRejected, model.ApprovalStatusRejected)
}

func (s *AccessRequestService) decide(userID, role, id, arStatus, apStatus string) (*AccessRequestView, error) {
	if userID == "" {
		return nil, apperr.ErrUnauthorized
	}
	if !isSupportRole(role) {
		return nil, apperr.ErrForbidden
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return nil, apperr.ErrInvalidRequest
	}

	ar, err := s.accessRequests.GetByID(id)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrNotFound
		}
		return nil, apperr.ErrDatabase
	}
	if ar.Status != model.AccessRequestStatusPending {
		return nil, apperr.ErrConflict
	}

	auditAction := auditActionAccessRequestApprove
	if arStatus == model.AccessRequestStatusRejected {
		auditAction = auditActionAccessRequestReject
	}

	now := time.Now().UTC()
	err = s.db.Transaction(func(tx *gorm.DB) error {
		arRepo := repository.NewAccessRequestRepository(tx)
		apRepo := repository.NewApprovalRepository(tx)
		auditRepo := repository.NewAuditLogRepository(tx)

		approval, err := apRepo.GetByAccessRequestID(id)
		if err != nil {
			return err
		}
		if approval.Status != model.ApprovalStatusPending {
			return apperr.ErrConflict
		}

		arRows, err := arRepo.UpdateFieldsIfStatus(id, model.AccessRequestStatusPending, map[string]interface{}{
			"status":     arStatus,
			"updated_at": now,
		})
		if err != nil {
			return err
		}
		if arRows == 0 {
			return apperr.ErrConflict
		}

		apRows, err := apRepo.UpdateFieldsIfStatus(approval.ID, model.ApprovalStatusPending, map[string]interface{}{
			"status":      apStatus,
			"approver_id": userID,
			"decided_at":  now,
			"updated_at":  now,
		})
		if err != nil {
			return err
		}
		if apRows == 0 {
			return apperr.ErrConflict
		}
		return appendAuditLog(auditRepo, userID, "", auditAction, auditResourceAccessRequest, id)
	})
	if err != nil {
		if appErr, ok := err.(apperr.AppError); ok {
			return nil, appErr
		}
		if repository.IsNotFound(err) {
			return nil, apperr.ErrNotFound
		}
		return nil, apperr.ErrDatabase
	}

	updated, err := s.accessRequests.GetByID(id)
	if err != nil {
		return nil, apperr.ErrDatabase
	}
	view := toAccessRequestView(updated)
	return &view, nil
}

func canViewAccessRequest(userID, role string, ar *model.AccessRequest) bool {
	if isSupportRole(role) {
		return true
	}
	return ar.RequesterID == userID
}

func toAccessRequestView(ar *model.AccessRequest) AccessRequestView {
	return AccessRequestView{
		ID:              ar.ID,
		RequesterID:     ar.RequesterID,
		ServiceID:       ar.ServiceID,
		ResourceType:    ar.ResourceType,
		ResourceName:    ar.ResourceName,
		PermissionLevel: ar.PermissionLevel,
		Reason:          ar.Reason,
		Status:          statusToAPI(ar.Status),
		CreatedAt:       ar.CreatedAt,
		UpdatedAt:       ar.UpdatedAt,
	}
}

func normalizeResourceType(raw string) (string, bool) {
	switch strings.ToUpper(strings.TrimSpace(raw)) {
	case model.ResourceTypeGitLab:
		return model.ResourceTypeGitLab, true
	case model.ResourceTypeDatabase:
		return model.ResourceTypeDatabase, true
	case model.ResourceTypeDevEnv:
		return model.ResourceTypeDevEnv, true
	default:
		return "", false
	}
}

func normalizePermissionLevel(raw string) (string, bool) {
	switch strings.ToUpper(strings.TrimSpace(raw)) {
	case model.PermissionLevelRead:
		return model.PermissionLevelRead, true
	case model.PermissionLevelDeveloper:
		return model.PermissionLevelDeveloper, true
	case model.PermissionLevelAdmin:
		return model.PermissionLevelAdmin, true
	default:
		return "", false
	}
}

func normalizeAccessRequestStatus(raw string) (string, bool) {
	status := strings.ToUpper(strings.TrimSpace(raw))
	switch status {
	case model.AccessRequestStatusPending,
		model.AccessRequestStatusApproved,
		model.AccessRequestStatusRejected,
		model.AccessRequestStatusCancelled:
		return status, true
	default:
		return "", false
	}
}
