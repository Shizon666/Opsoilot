package service

import (
	"testing"

	"opspilot/internal/model"
)

func TestToUserView_EmployeeContext(t *testing.T) {
	user := &model.User{
		ID:            "22222222-2222-2222-2222-222222222201",
		Name:          "张明",
		Email:         "demo@opspilot.local",
		Department:    "研发部",
		Position:      "后端开发工程师",
		EmployeeLevel: "P5",
		Role:          model.Role{Code: model.RoleCodeEmployee},
	}

	withCtx := toUserView(user, true)
	if withCtx.Department != "研发部" {
		t.Fatalf("department=%q", withCtx.Department)
	}
	if withCtx.Position != "后端开发工程师" {
		t.Fatalf("position=%q", withCtx.Position)
	}
	if withCtx.EmployeeLevel != "P5" {
		t.Fatalf("employee_level=%q", withCtx.EmployeeLevel)
	}
	if withCtx.Role != "employee" {
		t.Fatalf("role=%q", withCtx.Role)
	}
	if withCtx.Username != "demo@opspilot.local" {
		t.Fatalf("username=%q", withCtx.Username)
	}

	loginView := toUserView(user, false)
	if loginView.Department != "" || loginView.Position != "" || loginView.EmployeeLevel != "" {
		t.Fatalf("login view should omit employee context, got %+v", loginView)
	}
}
