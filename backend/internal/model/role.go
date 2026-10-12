package model

import "time"

// Role codes (MVP). Values are persisted as VARCHAR; validation lives in Service.
const (
	RoleCodeEmployee  = "EMPLOYEE"
	RoleCodeITSupport = "IT_SUPPORT"
	RoleCodeAdmin     = "ADMIN"
)

// Role maps to table roles (docs/DATABASE.md §6).
type Role struct {
	ID          string    `gorm:"column:id;type:uuid;primaryKey"`
	Code        string    `gorm:"column:code;type:varchar(30);uniqueIndex;not null"`
	Name        string    `gorm:"column:name;type:varchar(100);not null"`
	Description *string   `gorm:"column:description;type:text"`
	CreatedAt   time.Time `gorm:"column:created_at;type:timestamptz;not null"`
	UpdatedAt   time.Time `gorm:"column:updated_at;type:timestamptz;not null"`
}

func (Role) TableName() string {
	return "roles"
}
