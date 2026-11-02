"""codemap: a token-efficient, queryable map of a code repository.

Stdlib only (Python 3.9+). The index is a SQLite database kept in the user's
cache directory, updated incrementally, and queried through a CLI or a
single-tool MCP server.
"""
VERSION = "1.1.0"
SCHEMA_VERSION = 2
