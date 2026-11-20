# Forward to repo root (run `make api` from services/ or services/api/)
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)

FORWARD_TARGETS := api dashboard demo-chat nightshift extension extension-build test setup-api setup-frontends setup-all agent agent-watch

.PHONY: $(FORWARD_TARGETS)

$(FORWARD_TARGETS):
	@$(MAKE) -C $(ROOT) $@