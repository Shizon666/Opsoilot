package repository

import (
	"gorm.io/gorm"
	"gorm.io/gorm/clause"

	"opspilot/internal/model"
)

// AccessRequestListFilter holds optional filters for listing access requests.
type AccessRequestListFilter struct {
	RequesterID string
	Status      string
	Limit       int
	Offset      int
}

// AccessRequestRepository provides access_request data access.
type AccessRequestRepository struct {
	db *gorm.DB
}

// NewAccessRequestRepository creates an AccessRequestRepository.
func NewAccessRequestRepository(db *gorm.DB) *AccessRequestRepository {
	return &AccessRequestRepository{db: db}
}

// Create inserts an access request and reloads generated fields (id, timestamps).
func (r *AccessRequestRepository) Create(ar *model.AccessRequest) error {
	if err := r.db.Clauses(clause.Returning{}).Omit("ID").Create(ar).Error; err != nil {
		return err
	}
	if ar.ID == "" {
		return r.db.Where("requester_id = ? AND created_at = ?", ar.RequesterID, ar.CreatedAt).
			Order("created_at DESC").First(ar).Error
	}
	return nil
}

// GetByID returns an access request by primary key, or gorm.ErrRecordNotFound.
func (r *AccessRequestRepository) GetByID(id string) (*model.AccessRequest, error) {
	var ar model.AccessRequest
	if err := r.db.Where("id = ?", id).First(&ar).Error; err != nil {
		return nil, err
	}
	return &ar, nil
}

// List returns access requests matching filter, newest first, plus total count.
func (r *AccessRequestRepository) List(filter AccessRequestListFilter) ([]model.AccessRequest, int64, error) {
	q := r.db.Model(&model.AccessRequest{})
	if filter.RequesterID != "" {
		q = q.Where("requester_id = ?", filter.RequesterID)
	}
	if filter.Status != "" {
		q = q.Where("status = ?", filter.Status)
	}

	var total int64
	if err := q.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	if filter.Limit <= 0 {
		filter.Limit = 20
	}
	if filter.Offset < 0 {
		filter.Offset = 0
	}

	var items []model.AccessRequest
	err := q.Order("created_at DESC").Limit(filter.Limit).Offset(filter.Offset).Find(&items).Error
	if err != nil {
		return nil, 0, err
	}
	return items, total, nil
}

// UpdateFields updates the given columns on an access request by id.
func (r *AccessRequestRepository) UpdateFields(id string, fields map[string]interface{}) error {
	if len(fields) == 0 {
		return nil
	}
	return r.db.Model(&model.AccessRequest{}).Where("id = ?", id).Updates(fields).Error
}

// UpdateFieldsIfStatus updates columns only when current status matches expected.
// Returns rows affected (0 means conflict / missing).
func (r *AccessRequestRepository) UpdateFieldsIfStatus(id, expectedStatus string, fields map[string]interface{}) (int64, error) {
	if len(fields) == 0 {
		return 0, nil
	}
	result := r.db.Model(&model.AccessRequest{}).
		Where("id = ? AND status = ?", id, expectedStatus).
		Updates(fields)
	return result.RowsAffected, result.Error
}
