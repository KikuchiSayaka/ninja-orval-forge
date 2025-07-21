"""
初期化コマンド実装
"""

import os
from pathlib import Path
from typing import Dict, Any

import click
import questionary
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import DEFAULT_CONFIG, SUPPORTED_FRAMEWORKS, get_config_path
from ..utils.file_manager import FileManager
from ..generators.api_generator import APIGenerator

console = Console()


@click.command()
@click.option("--name", "-n", prompt="プロジェクト名", help="プロジェクト名")
@click.option(
    "--app",
    "-a",
    prompt="Djangoアプリ名",
    default="main",
    help="DjangoアプリケーションのURL名",
)
@click.option(
    "--frontend",
    "-f",
    type=click.Choice(SUPPORTED_FRAMEWORKS),
    help="フロントエンドフレームワーク",
)
@click.option(
    "--interactive", "-i", is_flag=True, default=True, help="対話モードで実行"
)
@click.option("--force", is_flag=True, help="既存の設定を上書き")
@click.pass_context
def init_command(
    ctx: click.Context,
    name: str,
    app: str,
    frontend: str,
    interactive: bool,
    force: bool,
):
    """Django Ninja + Orval環境を初期化します"""

    current_dir = Path.cwd()
    config_path = get_config_path(current_dir)

    # 既存設定の確認
    if config_path.exists() and not force:
        if not questionary.confirm(
            "既存の設定ファイルが見つかりました。上書きしますか？"
        ).ask():
            console.print("[yellow]初期化をキャンセルしました。[/yellow]")
            return

    console.print(f"\n[bold green]ninja-orval-forge プロジェクト初期化[/bold green]")
    console.print(f"プロジェクト: [cyan]{name}[/cyan]")
    console.print(f"ディレクトリ: [dim]{current_dir}[/dim]\n")

    # 設定の収集
    config = _collect_configuration(name, app, frontend, interactive)

    # プロジェクト初期化の実行
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        task1 = progress.add_task("設定ファイルを作成中...", total=None)
        _create_config_file(config_path, config)
        progress.update(task1, completed=100)

        task2 = progress.add_task("ディレクトリ構造を作成中...", total=None)
        _create_directory_structure(current_dir, config)
        progress.update(task2, completed=100)

        task3 = progress.add_task("基本ファイルを生成中...", total=None)
        _generate_initial_files(current_dir, config)
        progress.update(task3, completed=100)

        if config["frontend"]["framework"] != "none":
            task4 = progress.add_task("フロントエンド設定を生成中...", total=None)
            _setup_frontend(current_dir, config)
            progress.update(task4, completed=100)

    console.print("\n[bold green]✅ プロジェクトの初期化が完了しました！[/bold green]")

    # 次のステップの案内
    _show_next_steps(config)


def _collect_configuration(
    name: str, app: str, frontend: str, interactive: bool
) -> Dict[str, Any]:
    """設定情報を収集"""

    config = DEFAULT_CONFIG.copy()
    config["project"]["name"] = name
    config["project"]["django_app"] = app

    if interactive:
        # フロントエンドフレームワークの選択
        if not frontend:
            frontend = questionary.select(
                "フロントエンドフレームワークを選択してください:",
                choices=[
                    {"name": "Vue 3 (推奨)", "value": "vue"},
                    {"name": "React", "value": "react"},
                    {"name": "Angular", "value": "angular"},
                    {"name": "なし (API のみ)", "value": "none"},
                ],
            ).ask()

        config["frontend"]["framework"] = frontend

        if frontend != "none":
            # TypeScript設定
            use_typescript = questionary.confirm(
                "TypeScriptを使用しますか？ (推奨)", default=True
            ).ask()
            config["frontend"]["typescript"] = use_typescript

        # 認証設定
        use_auth = questionary.confirm(
            "認証機能を有効にしますか？", default=False
        ).ask()
        config["ninja"]["auth_enabled"] = use_auth

        if use_auth:
            auth_type = questionary.select(
                "認証タイプを選択してください:",
                choices=[
                    {"name": "JWT認証", "value": "JWTAuth"},
                    {"name": "セッション認証", "value": "SessionAuth"},
                    {"name": "カスタム認証", "value": "CustomAuth"},
                ],
            ).ask()
            config["ninja"]["auth_class"] = auth_type

        # レスポンス形式
        use_camel_case = questionary.confirm(
            "レスポンスをキャメルケースにしますか？ (推奨)", default=True
        ).ask()
        config["ninja"]["camel_case_response"] = use_camel_case

    else:
        # 非対話モード：デフォルト値を使用
        config["frontend"]["framework"] = frontend or "vue"

    return config


def _create_config_file(config_path: Path, config: Dict[str, Any]):
    """設定ファイルを作成"""
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def _create_directory_structure(project_dir: Path, config: Dict[str, Any]):
    """ディレクトリ構造を作成"""
    app_name = config["project"]["django_app"]

    directories = [
        f"{app_name}/apis/ninja/api_views",
        f"{app_name}/apis/ninja/openapi",
        f"{app_name}/apis/ninja/shared",
        "frontend/api/client",
        "frontend/api/schema",
        "frontend/composables",
        "frontend/components",
    ]

    for directory in directories:
        dir_path = project_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)

        # __init__.pyファイルを作成
        if "apis" in directory:
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")


def _generate_initial_files(project_dir: Path, config: Dict[str, Any]):
    """初期ファイルを生成"""
    generator = APIGenerator()
    file_manager = FileManager()

    app_name = config["project"]["django_app"]
    base_dir = project_dir / app_name / "apis" / "ninja"

    # 基本API設定ファイル
    api_content = generator.generate_base_api(config)
    file_manager.write_file(base_dir / "api.py", api_content)

    # 共通基盤スキーマ
    base_schemas_content = generator.generate_base_schemas(config)
    file_manager.write_file(base_dir / "base_schemas.py", base_schemas_content)

    # ページネーションユーティリティ
    pagination_content = generator.generate_pagination_utils(config)
    file_manager.write_file(
        base_dir / "shared" / "pagination_utils.py", pagination_content
    )


def _setup_frontend(project_dir: Path, config: Dict[str, Any]):
    """フロントエンド設定をセットアップ"""
    generator = APIGenerator()
    file_manager = FileManager()

    # Orval設定ファイル
    orval_config = generator.generate_orval_config(config)
    file_manager.write_file(project_dir / "orval.config.ts", orval_config)

    # Fetchラッパー
    fetch_wrapper = generator.generate_fetch_wrapper(config)
    file_manager.write_file(
        project_dir / "frontend" / "api" / "client" / "fetchWrapper.ts", fetch_wrapper
    )

    # package.jsonスクリプトの提案
    _suggest_package_scripts(config)


def _suggest_package_scripts(config: Dict[str, Any]):
    """package.jsonスクリプトを提案"""
    app_name = config["project"]["django_app"]

    scripts = {
        "prepare:ninja": f"curl http://localhost:8000/ninja_api/openapi.json -o {app_name}/apis/ninja/openapi/ninja_api_schema.json",
        "generate:ninja": f"openapi-typescript {app_name}/apis/ninja/openapi/ninja_api_schema.json -o frontend/api/schema/ninja_api_schema.ts && orval --config ./orval.config.ts",
        "ninja:generate": "npm run prepare:ninja && npm run generate:ninja",
    }

    console.print(
        "\n[bold blue]📦 package.jsonに以下のスクリプトを追加してください:[/bold blue]"
    )
    for name, command in scripts.items():
        console.print(f'  "[cyan]{name}[/cyan]": "[dim]{command}[/dim]"')


def _show_next_steps(config: Dict[str, Any]):
    """次のステップを表示"""
    console.print("\n[bold blue]🚀 次のステップ:[/bold blue]")
    console.print("1. [cyan]ninja-orval-forge generate[/cyan] でAPIを生成")
    console.print("2. Django設定にNinja APIのURLパターンを追加")
    console.print("3. [cyan]python manage.py runserver[/cyan] でサーバー起動")

    if config["frontend"]["framework"] != "none":
        console.print(
            "4. [cyan]npm run ninja:generate[/cyan] でTypeScriptクライアント生成"
        )

    console.print(f"\n設定ファイル: [dim].ninja-orval-forge.yml[/dim]")
    console.print(
        "ドキュメント: [link]https://github.com/yourusername/ninja-orval-forge[/link]"
    )
