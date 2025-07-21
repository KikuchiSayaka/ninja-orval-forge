"""
API生成コマンド実装
"""

from pathlib import Path
from typing import List, Optional

import click
import questionary
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils.file_manager import FileManager
from ..generators.api_generator import APIGenerator
from ..analyzers.django_analyzer import DjangoAnalyzer

console = Console()

@click.command()
@click.argument("feature_name")
@click.option(
    "--model", "-m",
    required=True,
    help="対象のDjangoモデル名"
)
@click.option(
    "--operations", "-o",
    multiple=True,
    type=click.Choice(["list", "retrieve", "create", "update", "delete"]),
    help="生成するAPI操作 (複数指定可能)"
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    default=True,
    help="対話モードで実行"
)
@click.option(
    "--force",
    is_flag=True,
    help="既存ファイルを上書き"
)
@click.pass_context
def generate_command(
    ctx: click.Context,
    feature_name: str,
    model: str,
    operations: tuple,
    interactive: bool,
    force: bool
):
    """新しいAPI機能を生成します
    
    FEATURE_NAME: 生成する機能名 (例: users, products)
    """
    
    current_dir = Path.cwd()
    
    console.print(f"\n[bold green]API機能生成: {feature_name}[/bold green]")
    console.print(f"対象モデル: [cyan]{model}[/cyan]")
    
    # Djangoプロジェクトの分析
    analyzer = DjangoAnalyzer(current_dir)
    
    try:
        model_info = analyzer.analyze_model(model)
        console.print(f"✅ モデル '{model}' を発見しました")
    except Exception as e:
        console.print(f"[red]❌ エラー: {str(e)}[/red]")
        return
    
    # 操作の選択
    if interactive and not operations:
        operations = _select_operations()
    elif not operations:
        operations = ("list", "retrieve", "create", "update", "delete")
    
    # 設定の確認
    config = _load_project_config(current_dir)
    if not config:
        console.print("[red]❌ プロジェクトが初期化されていません。先にninja-orval-forge initを実行してください。[/red]")
        return
    
    # 生成処理の実行
    _generate_api_feature(
        current_dir, 
        feature_name, 
        model_info, 
        operations, 
        config, 
        force
    )
    
    console.print(f"\n[bold green]✅ API機能 '{feature_name}' の生成が完了しました！[/bold green]")
    _show_generated_files(current_dir, feature_name, config)

def _select_operations() -> tuple:
    """操作を対話的に選択"""
    operations = questionary.checkbox(
        "生成するAPI操作を選択してください:",
        choices=[
            {"name": "📋 一覧取得 (list)", "value": "list", "checked": True},
            {"name": "🔍 詳細取得 (retrieve)", "value": "retrieve", "checked": True},
            {"name": "➕ 作成 (create)", "value": "create", "checked": True},
            {"name": "✏️ 更新 (update)", "value": "update", "checked": True},
            {"name": "🗑️ 削除 (delete)", "value": "delete", "checked": False},
        ]
    ).ask()
    
    if not operations:
        console.print("[yellow]⚠️ 操作が選択されませんでした。デフォルトでCRUD操作を生成します。[/yellow]")
        operations = ["list", "retrieve", "create", "update"]
    
    return tuple(operations)

def _load_project_config(project_dir: Path):
    """プロジェクト設定を読み込み"""
    from ..config import get_config_path
    import yaml
    
    config_path = get_config_path(project_dir)
    if not config_path.exists():
        return None
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _generate_api_feature(
    project_dir: Path,
    feature_name: str,
    model_info: dict,
    operations: tuple,
    config: dict,
    force: bool
):
    """API機能を生成"""
    
    generator = APIGenerator()
    file_manager = FileManager()
    
    app_name = config["project"]["django_app"]
    feature_dir = project_dir / app_name / "apis" / "ninja" / "api_views" / feature_name
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # ディレクトリ作成
        task1 = progress.add_task("ディレクトリを作成中...", total=None)
        feature_dir.mkdir(parents=True, exist_ok=True)
        (feature_dir / "__init__.py").write_text("", encoding="utf-8")
        progress.update(task1, completed=100)
        
        # スキーマファイル生成
        task2 = progress.add_task("Pydanticスキーマを生成中...", total=None)
        schema_content = generator.generate_schema(
            feature_name, model_info, operations, config
        )
        schema_path = feature_dir / "schema.py"
        
        if schema_path.exists() and not force:
            if not questionary.confirm(f"'{schema_path}' が既に存在します。上書きしますか？").ask():
                console.print("[yellow]スキーマファイルの生成をスキップしました。[/yellow]")
            else:
                file_manager.write_file(schema_path, schema_content)
        else:
            file_manager.write_file(schema_path, schema_content)
        progress.update(task2, completed=100)
        
        # ビューファイル生成
        task3 = progress.add_task("Django Ninjaビューを生成中...", total=None)
        views_content = generator.generate_views(
            feature_name, model_info, operations, config
        )
        views_path = feature_dir / "views.py"
        
        if views_path.exists() and not force:
            if not questionary.confirm(f"'{views_path}' が既に存在します。上書きしますか？").ask():
                console.print("[yellow]ビューファイルの生成をスキップしました。[/yellow]")
            else:
                file_manager.write_file(views_path, views_content)
        else:
            file_manager.write_file(views_path, views_content)
        progress.update(task3, completed=100)
        
        # メインAPIファイルの更新
        task4 = progress.add_task("APIルーターを登録中...", total=None)
        _update_main_api_file(project_dir, feature_name, config, force)
        progress.update(task4, completed=100)

def _update_main_api_file(
    project_dir: Path, 
    feature_name: str, 
    config: dict, 
    force: bool
):
    """メインのapi.pyファイルにルーターを追加"""
    
    app_name = config["project"]["django_app"]
    api_file = project_dir / app_name / "apis" / "ninja" / "api.py"
    
    if not api_file.exists():
        console.print(f"[yellow]⚠️ {api_file} が見つかりません。手動でルーターを追加してください。[/yellow]")
        return
    
    content = api_file.read_text(encoding="utf-8")
    
    # インポート文の追加
    import_line = f"from {app_name}.apis.ninja.api_views.{feature_name}.views import router as {feature_name}_router"
    if import_line not in content:
        # インポートセクションに追加
        lines = content.split("\n")
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith("from") and "import router as" in line:
                insert_index = i + 1
            elif line.startswith("api = NinjaAPI"):
                break
        
        lines.insert(insert_index, import_line)
        content = "\n".join(lines)
    
    # ルーター追加
    router_line = f'api.add_router("", {feature_name}_router)'
    if router_line not in content:
        # api.add_router行の後に追加
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "api.add_router(" in line:
                lines.insert(i + 1, router_line)
                break
        else:
            # 見つからない場合は最後に追加
            lines.append("")
            lines.append(router_line)
        
        content = "\n".join(lines)
    
    api_file.write_text(content, encoding="utf-8")

def _show_generated_files(project_dir: Path, feature_name: str, config: dict):
    """生成されたファイルを表示"""
    app_name = config["project"]["django_app"]
    base_path = f"{app_name}/apis/ninja/api_views/{feature_name}"
    
    console.print(f"\n[bold blue]📁 生成されたファイル:[/bold blue]")
    console.print(f"  [cyan]{base_path}/schema.py[/cyan] - Pydanticスキーマ")
    console.print(f"  [cyan]{base_path}/views.py[/cyan] - Django Ninjaビュー")
    console.print(f"  [cyan]{app_name}/apis/ninja/api.py[/cyan] - ルーター登録 (更新)")
    
    console.print(f"\n[bold blue]🔄 次のステップ:[/bold blue]")
    console.print("1. Django開発サーバーを起動")
    console.print("2. http://localhost:8000/ninja_api/docs でSwagger UIを確認")
    console.print("3. [cyan]npm run ninja:generate[/cyan] でTypeScriptクライアントを生成")