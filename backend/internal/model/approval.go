package model

import "time"

// Approval status values (MVP; align with AccessRequest).
const (
	ApprovalStatusPending   = "PENDING"
	ApprovalStatusApproved  = "APPROVED"
	ApprovalStatusRejected  = "REJECTED"
	ApprovalStatusCancelled = "CANCELLED"
)

// Approval maps to table approvals (docs/DATABASE.md §11).
// ApproverID is nil while PENDING; set on approve/reject.
type Approval struct {
	ID              string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()"`
	AccessRequestID string     `gorm:"column:access_request_id;type:uuid;not null;index"`
	ApproverID      *string    `gorm:"column:approver_id;type:uuid"`
	Status          string     `gorm:"column:status;type:varchar(30);not null;index"`
	Comment         *string    `gorm:"column:comment;type:text"`
	DecidedAt       *time.Time `gorm:"column:decided_at;type:timestamptz"`
	CreatedAt       time.Time  `gorm:"column:created_at;type:timestamptz;not null"`
	UpdatedAt       time.Time  `gorm:"column:updated_at;type:timestamptz;not null"`
}

func (Approval) TableName() string {
	return "approvals"
}
