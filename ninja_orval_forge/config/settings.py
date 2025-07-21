"""
ninja-orval-forge設定モジュール
"""

from pathlib import Path
from typing import Dict, Any, List

# デフォルト設定
DEFAULT_CONFIG = {
    "project": {
        "name": "",
        "django_app": "main",
        "api_prefix": "/api/v1",
        "api_version": "1.0.0",
        "api_description": "Generated API",
    },
    "ninja": {
        "auth_enabled": False,
        "auth_class": "JWTAuth",
        "camel_case_response": True,
        "auto_openapi": True,
    },
    "orval": {
        "output_path": "./frontend/api/client",
        "client_type": "fetch",
        "split_mode": "tags-split",
        "mutator_name": "customFetch",
        "ts_schemas_dir": "frontend/api/schema",
        "composables_dir": "frontend/composables",
    },
    "frontend": {
        "framework": "vue",
        "typescript": True,
        "composition_api": True,
    },
    "templates": {
        "pagination_limit": 20,
        "max_page_size": 100,
        "default_ordering": "-id",
        "include_tests": True,
    },
}

# フィールドタイプマッピング
DJANGO_TO_PYDANTIC_MAPPING: Dict[str, str] = {
    "AutoField": "int",
    "BigAutoField": "int",
    "BigIntegerField": "int",
    "BinaryField": "bytes",
    "BooleanField": "bool",
    "CharField": "str",
    "DateField": "date",
    "DateTimeField": "datetime",
    "DecimalField": "Decimal",
    "DurationField": "timedelta",
    "EmailField": "EmailStr",
    "FileField": "str",
    "FilePathField": "str",
    "FloatField": "float",
    "ImageField": "str",
    "IntegerField": "int",
    "JSONField": "Dict[str, Any]",
    "PositiveBigIntegerField": "int",
    "PositiveIntegerField": "int",
    "PositiveSmallIntegerField": "int",
    "SlugField": "str",
    "SmallAutoField": "int",
    "SmallIntegerField": "int",
    "TextField": "str",
    "TimeField": "time",
    "URLField": "HttpUrl",
    "UUIDField": "UUID",
    "ForeignKey": "int",
    "OneToOneField": "int",
    "ManyToManyField": "List[int]",
}

# 必要なimport文
PYDANTIC_IMPORTS: List[str] = [
    "from pydantic import BaseModel, Field, ConfigDict",
    "from typing import List, Optional, Dict, Any",
    "from datetime import datetime, date, time, timedelta",
    "from decimal import Decimal",
    "from uuid import UUID",
    "from pydantic import EmailStr, HttpUrl",
]

# 命名規則
NAMING_CONVENTIONS = {
    "schema_suffix": "Schema",
    "list_schema_suffix": "ListSchema",
    "create_schema_suffix": "CreateSchema",
    "update_schema_suffix": "UpdateSchema",
    "router_variable_suffix": "_router",
    "api_function_prefix": "",
}

# サポートされているフレームワーク
SUPPORTED_FRAMEWORKS = ["vue", "react", "angular", "none"]

# サポートされているクライアントタイプ
SUPPORTED_CLIENT_TYPES = ["fetch", "axios", "angular", "react-query", "svelte-query"]

# テンプレートファイルパス
TEMPLATE_PATHS = {
    "django_api": "django/api.py.j2",
    "django_schema": "django/schema.py.j2",
    "django_views": "django/views.py.j2",
    "django_base_schemas": "django/base_schemas.py.j2",
    "django_pagination": "django/shared/pagination_utils.py.j2",
    "orval_config": "typescript/orval.config.ts.j2",
    "fetch_wrapper": "typescript/fetch_wrapper.ts.j2",
    "vue_component": "vue/list_component.vue.j2",
    "vue_composable": "vue/composable.ts.j2",
}

# 設定ファイル名
CONFIG_FILE_NAME = ".ninja-orval-forge.yml"


def get_template_dir() -> Path:
    """テンプレートディレクトリのパスを取得"""
    return Path(__file__).parent.parent / "templates"


def get_config_path(project_dir: Path = None) -> Path:
    """設定ファイルのパスを取得"""
    if project_dir is None:
        project_dir = Path.cwd()
    return project_dir / CONFIG_FILE_NAME
