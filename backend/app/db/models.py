"""Model registry.

Import every ORM model here so Base.metadata knows about it before
init_db() calls create_all.
"""

from app.db.base import Base
from app.models.scan import Scan, ScanResult

__all__ = ["Base", "Scan", "ScanResult"]
