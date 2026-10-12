CREATE TABLE IF NOT EXISTS tickets (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_no    VARCHAR(30)  NOT NULL,
    requester_id UUID         NOT NULL,
    assignee_id  UUID         NULL,
    service_id   UUID         NOT NULL,
    title        VARCHAR(200) NOT NULL,
    description  TEXT         NOT NULL,
    priority     VARCHAR(20)  NOT NULL,
    status       VARCHAR(30)  NOT NULL,
    resolution   TEXT         NULL,
    resolved_at  TIMESTAMPTZ  NULL,
    closed_at    TIMESTAMPTZ  NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tickets_ticket_no UNIQUE (ticket_no),
    CONSTRAINT fk_tickets_requester_id FOREIGN KEY (requester_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_tickets_assignee_id FOREIGN KEY (assignee_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_tickets_service_id FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_tickets_requester_id ON tickets (requester_id);
CREATE INDEX IF NOT EXISTS idx_tickets_assignee_id ON tickets (assignee_id);
CREATE INDEX IF NOT EXISTS idx_tickets_service_id ON tickets (service_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets (created_at);
