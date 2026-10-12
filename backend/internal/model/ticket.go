package model

import "time"

// Ticket priority values (MVP).
const (
	TicketPriorityLow    = "LOW"
	TicketPriorityMedium = "MEDIUM"
	TicketPriorityHigh   = "HIGH"
	TicketPriorityUrgent = "URGENT"
)

// Ticket status values (Phase 4 MVP: no REJECTED).
const (
	TicketStatusOpen        = "OPEN"
	TicketStatusAssigned    = "ASSIGNED"
	TicketStatusInProgress  = "IN_PROGRESS"
	TicketStatusWaitingUser = "WAITING_USER"
	TicketStatusResolved    = "RESOLVED"
	TicketStatusClosed      = "CLOSED"
)

// DefaultServiceID is the seeded GENERAL_IT service (migrations/000007).
const DefaultServiceID = "33333333-3333-3333-3333-333333333301"

// Ticket maps to table tickets (docs/DATABASE.md §8).
// API exposes requester_id as creator_id (Plan R4).
type Ticket struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()"`
	TicketNo    string     `gorm:"column:ticket_no;type:varchar(30);uniqueIndex;not null"`
	RequesterID string     `gorm:"column:requester_id;type:uuid;not null;index"`
	AssigneeID  *string    `gorm:"column:assignee_id;type:uuid;index"`
	ServiceID   string     `gorm:"column:service_id;type:uuid;not null;index"`
	Title       string     `gorm:"column:title;type:varchar(200);not null"`
	Description string     `gorm:"column:description;type:text;not null"`
	Priority    string     `gorm:"column:priority;type:varchar(20);not null"`
	Status      string     `gorm:"column:status;type:varchar(30);not null;index"`
	Analysis    *string    `gorm:"column:analysis;type:text"`
	Resolution  *string    `gorm:"column:resolution;type:text"`
	ResolvedAt  *time.Time `gorm:"column:resolved_at;type:timestamptz"`
	ClosedAt    *time.Time `gorm:"column:closed_at;type:timestamptz"`
	CreatedAt   time.Time  `gorm:"column:created_at;type:timestamptz;not null;index"`
	UpdatedAt   time.Time  `gorm:"column:updated_at;type:timestamptz;not null"`
}

func (Ticket) TableName() string {
	return "tickets"
}
