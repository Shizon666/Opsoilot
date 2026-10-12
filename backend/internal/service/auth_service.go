package service

import (
	"strings"

	"golang.org/x/crypto/bcrypt"

	"opspilot/internal/model"
	"opspilot/internal/pkg/apperr"
	"opspilot/internal/pkg/jwt"
	"opspilot/internal/repository"
)

// AuthService handles login.
type AuthService struct {
	users *repository.UserRepository
	jwt   *jwt.Manager
}

// NewAuthService creates an AuthService.
func NewAuthService(users *repository.UserRepository, jwtManager *jwt.Manager) *AuthService {
	return &AuthService{users: users, jwt: jwtManager}
}

// LoginResult is returned on successful authentication.
type LoginResult struct {
	Token     string
	ExpiresIn int64
	User      UserView
}

// UserView is the API-facing user summary (no password).
// Phase 12: department / position / employee_level are employee context only —
// not authorization claims (JWT role remains the RBAC source).
type UserView struct {
	ID            string `json:"id"`
	Username      string `json:"username"`
	Name          string `json:"name"`
	Department    string `json:"department,omitempty"`
	Position      string `json:"position,omitempty"`
	EmployeeLevel string `json:"employee_level,omitempty"`
	Role          string `json:"role"`
}

// Login authenticates username(=email) + password and issues a JWT.
func (s *AuthService) Login(username, password string) (*LoginResult, error) {
	username = strings.TrimSpace(username)
	if username == "" || password == "" {
		return nil, apperr.ErrInvalidRequest
	}

	user, err := s.users.GetByEmail(username)
	if err != nil {
		if repository.IsNotFound(err) {
			return nil, apperr.ErrUnauthorized
		}
		return nil, apperr.ErrDatabase
	}

	if user.Status != model.UserStatusActive {
		return nil, apperr.ErrUnauthorized
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		return nil, apperr.ErrUnauthorized
	}

	roleCode := user.Role.Code
	if roleCode == "" {
		return nil, apperr.ErrInternal
	}

	token, err := s.jwt.Sign(user.ID, roleCode)
	if err != nil {
		return nil, apperr.ErrInternal
	}

	return &LoginResult{
		Token:     token,
		ExpiresIn: s.jwt.ExpireSeconds(),
		User:      toUserView(user, false),
	}, nil
}

func toUserView(user *model.User, withEmployeeContext bool) UserView {
	v := UserView{
		ID:       user.ID,
		Username: user.Email,
		Name:     user.Name,
		Role:     roleToAPI(user.Role.Code),
	}
	if withEmployeeContext {
		v.Department = user.Department
		v.Position = user.Position
		v.EmployeeLevel = user.EmployeeLevel
	}
	return v
}

func roleToAPI(code string) string {
	switch strings.ToUpper(code) {
	case model.RoleCodeEmployee:
		return "employee"
	case model.RoleCodeITSupport:
		return "it_support"
	case model.RoleCodeAdmin:
		return "admin"
	default:
		return strings.ToLower(code)
	}
}
