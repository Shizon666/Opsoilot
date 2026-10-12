package model

import "time"

// AccessRequest status values (MVP).
const (
	AccessRequestStatusPending   = "PENDING"
	AccessRequestStatusApproved  = "APPROVED"
	AccessRequestStatusRejected  = "REJECTED"
	AccessRequestStatusCancelled = "CANCELLED"
)

// AccessRequest resource_type values (MVP).
const (
	ResourceTypeGitLab  = "GITLAB"
	ResourceTypeDatabase = "DATABASE"
	ResourceTypeDevEnv  = "DEV_ENV"
)

// AccessRequest permission_level values (MVP examples).
const (
	PermissionLevelRead      = "READ"
	PermissionLevelDeveloper = "DEVELOPER"
	PermissionLevelAdmin     = "ADMIN"
)

// AccessRequest maps to table access_requests (docs/DATABASE.md §10).
type AccessRequest struct {
	ID              string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()"`
	RequesterID     string    `gorm:"column:requester_id;type:uuid;not null;index"`
	ServiceID       string    `gorm:"column:service_id;type:uuid;not null"`
	ResourceType    string    `gorm:"column:resource_type;type:varchar(50);not null"`
	ResourceName    string    `gorm:"column:resource_name;type:varchar(200);not null"`
	PermissionLevel string    `gorm:"column:permission_level;type:varchar(50);not null"`
	Reason          string    `gorm:"column:reason;type:text;not null"`
	Status          string    `gorm:"column:status;type:varchar(30);not null;index"`
	CreatedAt       time.Time `gorm:"column:created_at;type:timestamptz;not null"`
	UpdatedAt       time.Time `gorm:"column:updated_at;type:timestamptz;not null"`
}

func (AccessRequest) TableName() string {
	return "access_requests"
}
