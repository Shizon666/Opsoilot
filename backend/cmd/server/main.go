package main

import (
	"log"
	"net/http"

	"github.com/gin-gonic/gin"

	"opspilot/internal/config"
	"opspilot/internal/database"
	"opspilot/internal/handler"
	"opspilot/internal/middleware"
	"opspilot/internal/pkg/jwt"
	"opspilot/internal/repository"
	"opspilot/internal/router"
	"opspilot/internal/service"
)

// OpsPilot Go Business API.
// Phase 6 Lite: append-only audit on Ticket / Permission write paths.
func main() {
	cfg := config.Load()

	db, err := database.Connect(cfg.Database.URL)
	if err != nil {
		log.Fatalf("database connect failed: %v", err)
	}

	jwtManager, err := jwt.NewManager(cfg.JWT.Secret, cfg.JWT.ExpireHours)
	if err != nil {
		log.Fatalf("jwt init failed: %v", err)
	}

	userRepo := repository.NewUserRepository(db)
	ticketRepo := repository.NewTicketRepository(db)
	serviceRepo := repository.NewServiceRepository(db)
	accessRequestRepo := repository.NewAccessRequestRepository(db)
	approvalRepo := repository.NewApprovalRepository(db)
	auditRepo := repository.NewAuditLogRepository(db)

	authSvc := service.NewAuthService(userRepo, jwtManager)
	userSvc := service.NewUserService(userRepo)
	ticketSvc := service.NewTicketService(ticketRepo, serviceRepo, userRepo, auditRepo)
	catalogSvc := service.NewCatalogService(serviceRepo, auditRepo)
	auditSvc := service.NewAuditService(auditRepo)
	accessRequestSvc := service.NewAccessRequestService(db, accessRequestRepo, approvalRepo, serviceRepo)

	deps := router.Deps{
		JWT:         jwtManager,
		Auth:        handler.NewAuthHandler(authSvc),
		Users:       handler.NewUserHandler(userSvc),
		Tickets:     handler.NewTicketHandler(ticketSvc),
		Services:    handler.NewServiceHandler(catalogSvc),
		Audits:      handler.NewAuditHandler(auditSvc),
		Permissions: handler.NewPermissionHandler(accessRequestSvc),
	}

	r := gin.New()
	r.Use(middleware.RequestID(), middleware.Recovery(), gin.Logger())
	router.Register(r, db, deps)

	addr := cfg.Host + ":" + cfg.Port
	log.Printf("backend listening on %s", addr)
	if err := http.ListenAndServe(addr, r); err != nil {
		log.Fatal(err)
	}
}
