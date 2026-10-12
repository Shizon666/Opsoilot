package model

import "time"

// Actor types for audit_logs (MVP).
const (
	ActorTypeUser   = "USER"
	ActorTypeAgent  = "AGENT"
	ActorTypeSystem = "SYSTEM"
)

// Audit result values (MVP).
const (
	AuditResultSuccess = "SUCCESS"
	AuditResultFailure = "FAILURE"
	AuditResultDenied  = "DENIED"
)

// AuditLog maps to table audit_logs (docs/DATABASE.md §16).
// Append-only: no UpdatedAt field by design.
type AuditLog struct {
	ID           string    `gorm:"column:id;type:uuid;primaryKey"`
	RequestID    *string   `gorm:"column:request_id;type:varchar(100);index"`
	ActorID      *string   `gorm:"column:actor_id;type:uuid"`
	ActorType    string    `gorm:"column:actor_type;type:varchar(30);not null"`
	Action       string    `gorm:"column:action;type:varchar(100);not null"`
	ResourceType string    `gorm:"column:resource_type;type:varchar(50);not null"`
	ResourceID   *string   `gorm:"column:resource_id;type:uuid"`
	Result       string    `gorm:"column:result;type:varchar(30);not null"`
	CreatedAt    time.Time `gorm:"column:created_at;type:timestamptz;not null;index"`
}

func (AuditLog) TableName() string {
	return "audit_logs"
}
