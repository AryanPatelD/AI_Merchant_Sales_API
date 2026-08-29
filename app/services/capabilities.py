"""Registry of API capabilities that are fully implemented and active."""

# Add a capability here only after its route, service, validation, persistence,
# and tests are complete. Discovery intersects this registry with the merchant's
# database configuration to avoid advertising placeholder endpoints.
IMPLEMENTED_CAPABILITIES: frozenset[str] = frozenset(
    {"availability", "catalog", "search"}
)
