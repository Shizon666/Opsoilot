CREATE TABLE IF NOT EXISTS access_requests (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id     UUID         NOT NULL,
    service_id       UUID         NOT NULL,
    resource_type    VARCHAR(50)  NOT NULL,
    resource_name    VARCHAR(200) NOT NULL,
    permission_level VARCHAR(50)  NOT NULL,
    reason           TEXT         NOT NULL,
    status           VARCHAR(30)  NOT NULL,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_access_requests_requester_id FOREIGN KEY (requester_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_access_requests_service_id FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_access_requests_requester_id ON access_requests (requester_id);
CREATE INDEX IF NOT EXISTS idx_access_requests_status ON access_requests (status);
