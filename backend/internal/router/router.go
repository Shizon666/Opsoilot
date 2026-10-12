package router

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"opspilot/internal/database"
	"opspilot/internal/handler"
	"opspilot/internal/middleware"
	"opspilot/internal/pkg/jwt"
)

// Deps holds HTTP handlers and auth middleware dependencies.
type Deps struct {
	JWT         *jwt.Manager
	Auth        *handler.AuthHandler
	Users       *handler.UserHandler
	Tickets     *handler.TicketHandler
	Services    *handler.ServiceHandler
	Audits      *handler.AuditHandler
	Permissions *handler.PermissionHandler
}

// Register mounts health and /api/v1 routes.
func Register(r *gin.Engine, db *gorm.DB, deps Deps) {
	r.GET("/health", func(c *gin.Context) {
		payload := gin.H{
			"status":  "ok",
			"service": "backend",
		}

		dbStatus := "ok"
		if err := database.Ping(db); err != nil {
			dbStatus = "unavailable"
			payload["status"] = "degraded"
		}
		payload["database"] = dbStatus

		c.JSON(http.StatusOK, payload)
	})

	v1 := r.Group("/api/v1")
	{
		v1.POST("/auth/login", deps.Auth.Login)

		authed := v1.Group("")
		authed.Use(middleware.JWT(deps.JWT))
		{
			authed.GET("/users/me", deps.Users.Me)

			authed.GET("/services", deps.Services.List)
			authed.GET("/services/:id", deps.Services.Get)
			authed.PATCH("/services/:id", deps.Services.Patch)

			authed.POST("/tickets", deps.Tickets.Create)
			authed.GET("/tickets", deps.Tickets.List)
			authed.GET("/tickets/:id", deps.Tickets.Get)
			authed.PATCH("/tickets/:id", deps.Tickets.Patch)

			authed.GET("/audit-logs", deps.Audits.List)

			authed.POST("/permissions", deps.Permissions.Create)
			authed.GET("/permissions", deps.Permissions.List)
			authed.GET("/permissions/:id", deps.Permissions.Get)
			authed.POST("/permissions/:id/approve", deps.Permissions.Approve)
			authed.POST("/permissions/:id/reject", deps.Permissions.Reject)
		}
	}
}
