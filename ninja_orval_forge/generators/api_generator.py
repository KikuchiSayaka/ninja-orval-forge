"""
API生成器実装
"""

from pathlib import Path
from typing import Dict, Any, List
import inflect
from jinja2 import Environment, FileSystemLoader

from ..config import get_template_dir, TEMPLATE_PATHS


class APIGenerator:
    """Django Ninja API生成器"""

    def __init__(self):
        template_dir = get_template_dir()
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.inflect_engine = inflect.engine()

        # カスタムフィルターの追加
        self.env.filters["kebab_case"] = self._kebab_case
        self.env.filters["camel_case"] = self._camel_case
        self.env.filters["snake_case"] = self._snake_case
        self.env.filters["plural"] = self._plural

    def generate_base_api(self, config: Dict[str, Any]) -> str:
        """基本API設定ファイルを生成"""
        template = self.env.get_template(TEMPLATE_PATHS["django_api"])

        context = {
            "project_name": config["project"]["name"],
            "api_version": config["project"]["api_version"],
            "api_description": config["project"]["api_description"],
            "app_name": config["project"]["django_app"],
            "auth_enabled": config["ninja"]["auth_enabled"],
            "auth_class": config["ninja"]["auth_class"],
            "features": config.get("features", []),
        }

        return template.render(**context)

    def generate_base_schemas(self, config: Dict[str, Any]) -> str:
        """共通Pydanticスキーマを生成"""
        template = self.env.get_template(TEMPLATE_PATHS["django_base_schemas"])

        context = {
            "app_name": config["project"]["django_app"],
            "default_page_size": config["templates"]["pagination_limit"],
            "max_page_size": config["templates"]["max_page_size"],
            "camel_case_enabled": config["ninja"]["camel_case_response"],
        }

        return template.render(**context)

    def generate_pagination_utils(self, config: Dict[str, Any]) -> str:
        """ページネーションユーティリティを生成"""
        template = self.env.get_template(TEMPLATE_PATHS["django_pagination"])

        context = {
            "app_name": config["project"]["django_app"],
            "max_page_size": config["templates"]["max_page_size"],
            "camel_case_enabled": config["ninja"]["camel_case_response"],
        }

        return template.render(**context)

    def generate_schema(
        self,
        feature_name: str,
        model_info: Dict[str, Any],
        operations: tuple,
        config: Dict[str, Any],
    ) -> str:
        """Pydanticスキーマを生成"""
        template = self.env.get_template(TEMPLATE_PATHS["django_schema"])

        model_name = self._to_pascal_case(feature_name.rstrip("s"))  # usersからUser

        context = {
            "model_name": model_name,
            "model_description": model_info.get("description", model_name),
            "app_name": config["project"]["django_app"],
            "fields": self._convert_model_fields(model_info.get("fields", [])),
            "computed_fields": model_info.get("computed_fields", []),
            "camel_case_enabled": config["ninja"]["camel_case_response"],
            "list_schema_needed": "list" in operations,
            "create_schema_needed": "create" in operations,
            "update_schema_needed": "update" in operations,
            "create_fields": self._get_create_fields(model_info.get("fields", [])),
            "update_fields": self._get_update_fields(model_info.get("fields", [])),
            "email_field_used": self._has_email_field(model_info.get("fields", [])),
            "url_field_used": self._has_url_field(model_info.get("fields", [])),
        }

        return template.render(**context)

    def generate_views(
        self,
        feature_name: str,
        model_info: Dict[str, Any],
        operations: tuple,
        config: Dict[str, Any],
    ) -> str:
        """Django Ninjaビューを生成"""
        template = self.env.get_template(TEMPLATE_PATHS["django_views"])

        model_name = self._to_pascal_case(feature_name.rstrip("s"))
        model_class = model_info.get("model_class", model_name)

        context = {
            "model_name": model_name,
            "model_class": model_class,
            "app_name": config["project"]["django_app"],
            "tag_name": feature_name,
            "resource_name": feature_name,
            "resource_path": feature_name,
            "function_name": feature_name,
            "default_ordering": config["templates"]["default_ordering"],
            "list_enabled": "list" in operations,
            "retrieve_enabled": "retrieve" in operations,
            "create_enabled": "create" in operations,
            "update_enabled": "update" in operations,
            "delete_enabled": "delete" in operations,
            "list_description": f"{model_name}の一覧を取得",
            "retrieve_description": f"{model_name}の詳細を取得",
            "create_description": f"新しい{model_name}を作成",
            "update_description": f"{model_name}を更新",
            "delete_description": f"{model_name}を削除",
            "path_params": model_info.get("path_params", []),
            "path_filters": model_info.get("path_filters", []),
            "list_filters": model_info.get("list_filters", []),
            "permissions_enabled": False,  # 今回は簡単のため無効
        }

        return template.render(**context)

    def generate_orval_config(self, config: Dict[str, Any]) -> str:
        """Orval設定ファイルを生成"""
        template = self.env.get_template(TEMPLATE_PATHS["orval_config"])

        app_name = config["project"]["django_app"]

        context = {
            "api_name": "ninjaApi",
            "openapi_path": f"./{app_name}/apis/ninja/openapi/ninja_api_schema.json",
            "output_path": config["orval"]["output_path"],
            "client_type": config["orval"]["client_type"],
            "split_mode": config["orval"]["split_mode"],
            "clean_output": True,
            "prettier_enabled": True,
            "use_mutator": True,
            "mutator_path": f"./frontend/api/client/fetchWrapper.ts",
            "mutator_name": config["orval"]["mutator_name"],
            "ts_schemas_path": config["orval"]["ts_schemas_dir"],
            "hooks": {"afterAllFilesWrite": "prettier --write"},
        }

        return template.render(**context)

    def generate_fetch_wrapper(self, config: Dict[str, Any]) -> str:
        """Fetchラッパーを生成"""
        template = self.env.get_template(TEMPLATE_PATHS["fetch_wrapper"])

        context = {
            "project_name": config["project"]["name"],
            "mutator_name": config["orval"]["mutator_name"],
            "default_timeout": 30000,
            "content_type": "application/json",
            "accept_header": "application/json",
            "credentials_mode": "include",
            "csrf_enabled": True,  # Django用にCSRF有効
            "auth_enabled": config["ninja"]["auth_enabled"],
            "auth_scheme": (
                "Bearer" if config["ninja"]["auth_class"] == "JWTAuth" else "Token"
            ),
            "auth_storage": "localStorage",
            "auth_token_key": "authToken",
        }

        return template.render(**context)

    def convert_serializer_to_schema(
        self, serializer_info: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """DRF SerializerをPydantic Schemaに変換"""
        # TODO: DRF Serializerの解析結果からPydanticスキーマを生成
        pass

    def convert_viewset_to_views(
        self, viewset_info: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """DRF ViewSetをDjango Ninjaビューに変換"""
        # TODO: DRF ViewSetの解析結果からDjango Ninjaビューを生成
        pass

    # ヘルパーメソッド
    def _convert_model_fields(
        self, fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Djangoモデルフィールドを変換"""
        from ..config import DJANGO_TO_PYDANTIC_MAPPING

        converted_fields = []
        for field in fields:
            field_type = field.get("type", "CharField")
            pydantic_type = DJANGO_TO_PYDANTIC_MAPPING.get(field_type, "str")

            converted_fields.append(
                {
                    "name": field["name"],
                    "type_hint": pydantic_type,
                    "optional": field.get("null", False) or field.get("blank", False),
                    "description": field.get("help_text", ""),
                }
            )

        return converted_fields

    def _get_create_fields(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """作成用フィールドを取得"""
        return [
            field
            for field in self._convert_model_fields(fields)
            if field["name"] not in ["id", "created_at", "updated_at"]
        ]

    def _get_update_fields(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """更新用フィールドを取得"""
        return [
            field
            for field in self._convert_model_fields(fields)
            if field["name"] not in ["id", "created_at"]
        ]

    def _has_email_field(self, fields: List[Dict[str, Any]]) -> bool:
        """EmailFieldが含まれているかチェック"""
        return any(field.get("type") == "EmailField" for field in fields)

    def _has_url_field(self, fields: List[Dict[str, Any]]) -> bool:
        """URLFieldが含まれているかチェック"""
        return any(field.get("type") == "URLField" for field in fields)

    def _kebab_case(self, text: str) -> str:
        """kebab-caseに変換"""
        return text.replace("_", "-").lower()

    def _camel_case(self, text: str) -> str:
        """camelCaseに変換"""
        components = text.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def _snake_case(self, text: str) -> str:
        """snake_caseに変換"""
        return text.lower().replace("-", "_")

    def _plural(self, text: str) -> str:
        """複数形に変換"""
        return self.inflect_engine.plural(text)

    def _to_pascal_case(self, text: str) -> str:
        """PascalCaseに変換"""
        return "".join(word.capitalize() for word in text.split("_"))
