package apperr

// Application error codes aligned with docs/API.md §5.
const (
	CodeOK             = 0
	CodeInvalidRequest = 40001
	CodeUnauthorized   = 40101
	CodeForbidden      = 40301
	CodeNotFound       = 40401
	CodeConflict       = 40901
	CodeInternal       = 50001
	CodeDatabase       = 50002
	CodeAgent          = 50003
)

// AppError is a structured application error (structure only in Phase 1).
type AppError struct {
	Code    int
	Message string
}

func (e AppError) Error() string {
	return e.Message
}

// Predefined errors for common failure cases.
var (
	ErrInvalidRequest = AppError{Code: CodeInvalidRequest, Message: "invalid request"}
	ErrUnauthorized   = AppError{Code: CodeUnauthorized, Message: "unauthorized"}
	ErrForbidden      = AppError{Code: CodeForbidden, Message: "forbidden"}
	ErrNotFound       = AppError{Code: CodeNotFound, Message: "resource not found"}
	ErrConflict       = AppError{Code: CodeConflict, Message: "resource status conflict"}
	ErrInternal       = AppError{Code: CodeInternal, Message: "internal server error"}
	ErrDatabase       = AppError{Code: CodeDatabase, Message: "database error"}
	ErrAgent          = AppError{Code: CodeAgent, Message: "agent service error"}
)

// New returns an AppError with the given code and message.
func New(code int, message string) AppError {
	return AppError{Code: code, Message: message}
}
