"""Model registry.

Import every ORM model here so Base.metadata knows about it before
init_db() calls create_all. No models exist yet.
"""

from app.db.base import Base

__all__ = ["Base"]
