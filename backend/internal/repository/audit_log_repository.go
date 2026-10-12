package repository

import (
	"gorm.io/gorm"

	"opspilot/internal/model"
)

// AuditLogRepository provides append-only audit_logs access (Phase 6 Lite).
// Only Create is exposed; Update / Delete / List are intentionally omitted.
type AuditLogRepository struct {
	db *gorm.DB
}

// NewAuditLogRepository creates an AuditLogRepository.
// Pass a transaction handle when writing inside an existing transaction.
func NewAuditLogRepository(db *gorm.DB) *AuditLogRepository {
	return &AuditLogRepository{db: db}
}

// Create inserts one audit_logs row. ID is omitted so Postgres DEFAULT gen_random_uuid() applies.
func (r *AuditLogRepository) Create(log *model.AuditLog) error {
	return r.db.Omit("ID").Create(log).Error
}

// ListByRequestID returns all audit rows for a request, oldest first.
func (r *AuditLogRepository) ListByRequestID(requestID string) ([]model.AuditLog, error) {
	var items []model.AuditLog
	err := r.db.Where("request_id = ?", requestID).
		Order("created_at ASC").
		Find(&items).Error
	return items, err
}
