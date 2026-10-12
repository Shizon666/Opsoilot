package repository

import (
	"gorm.io/gorm"

	"opspilot/internal/model"
)

// TicketListFilter holds optional filters for listing tickets.
type TicketListFilter struct {
	RequesterID string
	Status      string
	ServiceID   string
	Q           string
	Limit       int
	Offset      int
}

// TicketRepository provides ticket data access.
type TicketRepository struct {
	db *gorm.DB
}

// NewTicketRepository creates a TicketRepository.
func NewTicketRepository(db *gorm.DB) *TicketRepository {
	return &TicketRepository{db: db}
}

// Create inserts a ticket row and reloads generated fields (id, timestamps).
// ID is omitted so Postgres DEFAULT gen_random_uuid() applies.
func (r *TicketRepository) Create(ticket *model.Ticket) error {
	if err := r.db.Omit("ID").Create(ticket).Error; err != nil {
		return err
	}
	return r.db.Where("ticket_no = ?", ticket.TicketNo).First(ticket).Error
}

// GetByID returns a ticket by primary key, or gorm.ErrRecordNotFound.
func (r *TicketRepository) GetByID(id string) (*model.Ticket, error) {
	var ticket model.Ticket
	if err := r.db.Where("id = ?", id).First(&ticket).Error; err != nil {
		return nil, err
	}
	return &ticket, nil
}

// List returns tickets matching filter, newest first, plus total count.
func (r *TicketRepository) List(filter TicketListFilter) ([]model.Ticket, int64, error) {
	q := r.db.Model(&model.Ticket{})
	if filter.RequesterID != "" {
		q = q.Where("requester_id = ?", filter.RequesterID)
	}
	if filter.Status != "" {
		q = q.Where("status = ?", filter.Status)
	}
	if filter.ServiceID != "" {
		q = q.Where("service_id = ?", filter.ServiceID)
	}
	if filter.Q != "" {
		like := "%" + filter.Q + "%"
		q = q.Where("title ILIKE ? OR description ILIKE ?", like, like)
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

	var items []model.Ticket
	err := q.Order("created_at DESC").Limit(filter.Limit).Offset(filter.Offset).Find(&items).Error
	if err != nil {
		return nil, 0, err
	}
	return items, total, nil
}

// UpdateFields updates the given columns on a ticket by id.
func (r *TicketRepository) UpdateFields(id string, fields map[string]interface{}) error {
	if len(fields) == 0 {
		return nil
	}
	return r.db.Model(&model.Ticket{}).Where("id = ?", id).Updates(fields).Error
}
