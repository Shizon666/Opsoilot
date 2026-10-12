package service

import "opspilot/internal/model"

// canTransition reports whether from → to is a legal ticket status change.
// MVP states only (no REJECTED).
func canTransition(from, to string) bool {
	if from == "" || to == "" || from == to {
		return false
	}
	switch from {
	case model.TicketStatusOpen:
		return to == model.TicketStatusAssigned || to == model.TicketStatusInProgress
	case model.TicketStatusAssigned:
		return to == model.TicketStatusInProgress
	case model.TicketStatusInProgress:
		return to == model.TicketStatusWaitingUser || to == model.TicketStatusResolved
	case model.TicketStatusWaitingUser:
		return to == model.TicketStatusInProgress
	case model.TicketStatusResolved:
		return to == model.TicketStatusClosed
	default:
		// CLOSED and any unknown status: no outgoing transitions.
		return false
	}
}

// isKnownTicketStatus reports whether status is in the MVP ticket set.
func isKnownTicketStatus(status string) bool {
	switch status {
	case model.TicketStatusOpen,
		model.TicketStatusAssigned,
		model.TicketStatusInProgress,
		model.TicketStatusWaitingUser,
		model.TicketStatusResolved,
		model.TicketStatusClosed:
		return true
	default:
		return false
	}
}
