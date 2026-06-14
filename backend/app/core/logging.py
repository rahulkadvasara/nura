"""
Nura - Structured Logging Configuration
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, 'agent_name'):
            log_data["agent_name"] = record.agent_name
            
        if hasattr(record, 'execution_time_ms'):
            log_data["execution_time_ms"] = record.execution_time_ms
        
        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """Configure structured logging for the application"""
    
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create JSON formatter
    formatter = JSONFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger configuration
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        handlers=[console_handler],
        format='%(message)s'
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)