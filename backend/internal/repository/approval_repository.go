package repository

import (
	"gorm.io/gorm"
	"gorm.io/gorm/clause"

	"opspilot/internal/model"
)

// ApprovalRepository provides approval data access.
type ApprovalRepository struct {
	db *gorm.DB
}

// NewApprovalRepository creates an ApprovalRepository.
func NewApprovalRepository(db *gorm.DB) *ApprovalRepository {
	return &ApprovalRepository{db: db}
}

// Create inserts an approval and reloads generated fields (id, timestamps).
func (r *ApprovalRepository) Create(approval *model.Approval) error {
	if err := r.db.Clauses(clause.Returning{}).Omit("ID").Create(approval).Error; err != nil {
		return err
	}
	if approval.ID == "" {
		return r.db.Where("access_request_id = ?", approval.AccessRequestID).
			Order("created_at DESC").First(approval).Error
	}
	return nil
}

// GetByAccessRequestID returns the latest approval for an access request.
func (r *ApprovalRepository) GetByAccessRequestID(accessRequestID string) (*model.Approval, error) {
	var approval model.Approval
	if err := r.db.Where("access_request_id = ?", accessRequestID).
		Order("created_at DESC").First(&approval).Error; err != nil {
		return nil, err
	}
	return &approval, nil
}

// UpdateFields updates the given columns on an approval by id.
func (r *ApprovalRepository) UpdateFields(id string, fields map[string]interface{}) error {
	if len(fields) == 0 {
		return nil
	}
	return r.db.Model(&model.Approval{}).Where("id = ?", id).Updates(fields).Error
}

// UpdateFieldsIfStatus updates columns only when current status matches expected.
func (r *ApprovalRepository) UpdateFieldsIfStatus(id, expectedStatus string, fields map[string]interface{}) (int64, error) {
	if len(fields) == 0 {
		return 0, nil
	}
	result := r.db.Model(&model.Approval{}).
		Where("id = ? AND status = ?", id, expectedStatus).
		Updates(fields)
	return result.RowsAffected, result.Error
}
