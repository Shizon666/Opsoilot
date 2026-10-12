package service

import "testing"

func TestCanTransitionOpenToInProgress(t *testing.T) {
	if !canTransition("OPEN", "IN_PROGRESS") {
		t.Fatal("OPEN → IN_PROGRESS must be allowed")
	}
}

func TestCanTransitionOpenToClosedForbidden(t *testing.T) {
	if canTransition("OPEN", "CLOSED") {
		t.Fatal("OPEN → CLOSED must be forbidden")
	}
}

func TestCanTransitionOpenToAssignedStillAllowed(t *testing.T) {
	if !canTransition("OPEN", "ASSIGNED") {
		t.Fatal("OPEN → ASSIGNED must remain allowed")
	}
}
