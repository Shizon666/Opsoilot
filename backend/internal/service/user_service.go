package service

import (
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/repository"
)

// UserService handles current-user queries.
type UserService struct {
	users *repository.UserRepository
}

// NewUserService creates a UserService.
func NewUserService(users *repository.UserRepository) *UserService {
	return &UserService{users: users}
}

// Me returns the current user profile for /users/me.
func (s *UserService) Me(userID string) (*UserView, error) {
	if userID == "" {
		return nil, apperr.ErrUnauthorized
	}
	user, err := s.users.GetByID(userID)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrUnauthorized
		}
		return nil, apperr.ErrDatabase
	}
	view := toUserView(user, true)
	return &view, nil
}
