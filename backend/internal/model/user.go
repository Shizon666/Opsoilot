package model

import "time"

// User status values (MVP).
const (
	UserStatusActive   = "ACTIVE"
	UserStatusInactive = "INACTIVE"
)

// User maps to table users (docs/DATABASE.md §5 + Phase 12 employee context).
type User struct {
	ID            string    `gorm:"column:id;type:uuid;primaryKey"`
	Name          string    `gorm:"column:name;type:varchar(100);not null"`
	Email         string    `gorm:"column:email;type:varchar(255);uniqueIndex;not null"`
	PasswordHash  string    `gorm:"column:password_hash;type:varchar(255);not null"`
	Department    string    `gorm:"column:department;type:varchar(100);not null"`
	Position      string    `gorm:"column:position;type:varchar(100);not null"`
	EmployeeLevel string    `gorm:"column:employee_level;type:varchar(50);not null"`
	RoleID        string    `gorm:"column:role_id;type:uuid;not null"`
	Status        string    `gorm:"column:status;type:varchar(20);not null"`
	CreatedAt     time.Time `gorm:"column:created_at;type:timestamptz;not null"`
	UpdatedAt     time.Time `gorm:"column:updated_at;type:timestamptz;not null"`
	Role          Role      `gorm:"foreignKey:RoleID;references:ID"`
}

func (User) TableName() string {
	return "users"
}
