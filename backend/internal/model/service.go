package model

import "time"

// Service status values (MVP). Catalog enablement; orthogonal to health.
const (
	ServiceStatusActive   = "ACTIVE"
	ServiceStatusInactive = "INACTIVE"
)

// Service health values (Phase B simulated health; not Prometheus).
const (
	ServiceHealthHealthy  = "HEALTHY"
	ServiceHealthDegraded = "DEGRADED"
	ServiceHealthDown     = "DOWN"
)

// Service maps to table services (docs/DATABASE.md §7 + Phase B health).
type Service struct {
	ID             string     `gorm:"column:id;type:uuid;primaryKey"`
	Code           string     `gorm:"column:code;type:varchar(50);uniqueIndex;not null"`
	Name           string     `gorm:"column:name;type:varchar(100);not null"`
	Description    *string    `gorm:"column:description;type:text"`
	Category       string     `gorm:"column:category;type:varchar(50);not null"`
	Status         string     `gorm:"column:status;type:varchar(20);not null"`
	HealthStatus   string     `gorm:"column:health_status;type:varchar(20);not null"`
	HealthSummary  *string    `gorm:"column:health_summary;type:text"`
	LastCheckedAt  *time.Time `gorm:"column:last_checked_at;type:timestamptz"`
	CreatedAt      time.Time  `gorm:"column:created_at;type:timestamptz;not null"`
	UpdatedAt      time.Time  `gorm:"column:updated_at;type:timestamptz;not null"`
}

func (Service) TableName() string {
	return "services"
}
