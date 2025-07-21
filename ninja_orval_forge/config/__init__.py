"""設定モジュール"""

from .settings import (
    DEFAULT_CONFIG,
    DJANGO_TO_PYDANTIC_MAPPING,
    PYDANTIC_IMPORTS,
    NAMING_CONVENTIONS,
    SUPPORTED_FRAMEWORKS,
    SUPPORTED_CLIENT_TYPES,
    TEMPLATE_PATHS,
    CONFIG_FILE_NAME,
    get_template_dir,
    get_config_path,
)

__all__ = [
    "DEFAULT_CONFIG",
    "DJANGO_TO_PYDANTIC_MAPPING", 
    "PYDANTIC_IMPORTS",
    "NAMING_CONVENTIONS",
    "SUPPORTED_FRAMEWORKS",
    "SUPPORTED_CLIENT_TYPES",
    "TEMPLATE_PATHS",
    "CONFIG_FILE_NAME",
    "get_template_dir",
    "get_config_path",
]