package auth

import "github.com/google/uuid"

type Principal struct {
	TenantID        uuid.UUID
	RunID           *uuid.UUID
	KeyID           *uuid.UUID
	Scopes          []string
	MaxEventsPerSec int
}

func (p Principal) HasScope(scope string) bool {
	for _, s := range p.Scopes {
		if s == scope || s == "admin" {
			return true
		}
	}
	return false
}
