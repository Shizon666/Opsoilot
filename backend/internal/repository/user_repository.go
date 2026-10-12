package repository

import (
	"errors"

	"gorm.io/gorm"

	"opspilot/internal/model"
)

// UserRepository provides user data access.
type UserRepository struct {
	db *gorm.DB
}

// NewUserRepository creates a UserRepository.
func NewUserRepository(db *gorm.DB) *UserRepository {
	return &UserRepository{db: db}
}

// GetByEmail returns a user with Role preloaded, or gorm.ErrRecordNotFound.
func (r *UserRepository) GetByEmail(email string) (*model.User, error) {
	var user model.User
	err := r.db.Preload("Role").Where("email = ?", email).First(&user).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// GetByID returns a user with Role preloaded, or gorm.ErrRecordNotFound.
func (r *UserRepository) GetByID(id string) (*model.User, error) {
	var user model.User
	err := r.db.Preload("Role").Where("id = ?", id).First(&user).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// IsNotFound reports whether err is a missing-record error.
func IsNotFound(err error) bool {
	return errors.Is(err, gorm.ErrRecordNotFound)
}
