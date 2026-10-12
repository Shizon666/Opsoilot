package jwt

import (
	"fmt"
	"time"

	jwtlib "github.com/golang-jwt/jwt/v5"
)

// Claims is the minimal JWT payload for OpsPilot Auth.
type Claims struct {
	Role string `json:"role"`
	jwtlib.RegisteredClaims
}

// Manager signs and parses JWTs.
type Manager struct {
	secret []byte
	ttl    time.Duration
}

// NewManager creates a JWT manager. secret must be non-empty.
func NewManager(secret string, expireHours int) (*Manager, error) {
	if secret == "" {
		return nil, fmt.Errorf("jwt: secret is empty")
	}
	if expireHours <= 0 {
		expireHours = 24
	}
	return &Manager{
		secret: []byte(secret),
		ttl:    time.Duration(expireHours) * time.Hour,
	}, nil
}

// ExpireSeconds returns token lifetime in seconds (for login expires_in).
func (m *Manager) ExpireSeconds() int64 {
	return int64(m.ttl.Seconds())
}

// Sign issues a token with sub=userID and role (DB uppercase code).
func (m *Manager) Sign(userID, role string) (string, error) {
	now := time.Now().UTC()
	claims := Claims{
		Role: role,
		RegisteredClaims: jwtlib.RegisteredClaims{
			Subject:   userID,
			IssuedAt:  jwtlib.NewNumericDate(now),
			ExpiresAt: jwtlib.NewNumericDate(now.Add(m.ttl)),
		},
	}
	token := jwtlib.NewWithClaims(jwtlib.SigningMethodHS256, claims)
	return token.SignedString(m.secret)
}

// Parse validates the token and returns claims.
func (m *Manager) Parse(tokenString string) (*Claims, error) {
	token, err := jwtlib.ParseWithClaims(tokenString, &Claims{}, func(t *jwtlib.Token) (interface{}, error) {
		if t.Method != jwtlib.SigningMethodHS256 {
			return nil, fmt.Errorf("jwt: unexpected signing method")
		}
		return m.secret, nil
	})
	if err != nil {
		return nil, err
	}
	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, fmt.Errorf("jwt: invalid token")
	}
	if claims.Subject == "" {
		return nil, fmt.Errorf("jwt: missing subject")
	}
	return claims, nil
}
