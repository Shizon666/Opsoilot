-- approver_id is NULL while status is PENDING; set on approve/reject (Phase 5).
CREATE TABLE IF NOT EXISTS approvals (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_request_id UUID         NOT NULL,
    approver_id       UUID         NULL,
    status            VARCHAR(30)  NOT NULL,
    comment           TEXT         NULL,
    decided_at        TIMESTAMPTZ  NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_approvals_access_request_id FOREIGN KEY (access_request_id) REFERENCES access_requests (id) ON DELETE RESTRICT,
    CONSTRAINT fk_approvals_approver_id FOREIGN KEY (approver_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_approvals_access_request_id ON approvals (access_request_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals (status);
