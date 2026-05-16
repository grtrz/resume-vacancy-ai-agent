import logging
from collections.abc import Iterable

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_STRUCTURED_FIELDS = (
    "method",
    "path",
    "status_code",
    "duration_ms",
    "workflow_step",
)


class KeyValueFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str = _DEFAULT_FORMAT,
        structured_fields: Iterable[str] = _STRUCTURED_FIELDS,
    ) -> None:
        super().__init__(fmt=fmt)
        self._structured_fields = tuple(structured_fields)

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        fields = [
            f"{field}={getattr(record, field)}"
            for field in self._structured_fields
            if hasattr(record, field)
        ]
        if not fields:
            return message
        return f"{message} {' '.join(fields)}"


def configure_logging(level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setFormatter(KeyValueFormatter())
        return

    logging.basicConfig(
        level=level,
        handlers=[_stream_handler()],
    )


def _stream_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(KeyValueFormatter())
    return handler
