package repository

import (
	"gorm.io/gorm"

	"opspilot/internal/model"
)

// ServiceRepository provides IT service catalog data access.
type ServiceRepository struct {
	db *gorm.DB
}

// NewServiceRepository creates a ServiceRepository.
func NewServiceRepository(db *gorm.DB) *ServiceRepository {
	return &ServiceRepository{db: db}
}

// GetByID returns a service by primary key, or gorm.ErrRecordNotFound.
func (r *ServiceRepository) GetByID(id string) (*model.Service, error) {
	var svc model.Service
	if err := r.db.Where("id = ?", id).First(&svc).Error; err != nil {
		return nil, err
	}
	return &svc, nil
}

// ListActive returns ACTIVE catalog services, newest first, capped for V1 lists.
func (r *ServiceRepository) ListActive() ([]model.Service, error) {
	var items []model.Service
	err := r.db.Where("status = ?", model.ServiceStatusActive).
		Order("code ASC").
		Limit(10).
		Find(&items).Error
	return items, err
}

// UpdateFields updates the given columns on a service by id.
func (r *ServiceRepository) UpdateFields(id string, fields map[string]interface{}) error {
	if len(fields) == 0 {
		return nil
	}
	return r.db.Model(&model.Service{}).Where("id = ?", id).Updates(fields).Error
}
