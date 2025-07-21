"""
DRF移行コマンド実装
"""

from pathlib import Path
from typing import List, Dict, Any

import click
import questionary
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..analyzers.drf_analyzer import DRFAnalyzer
from ..generators.api_generator import APIGenerator
from ..utils.file_manager import FileManager

console = Console()

@click.command()
@click.option(
    "--app", "-a",
    required=True,
    help="移行対象のDjangoアプリケーション名"
)
@click.option(
    "--dry-run", "-d",
    is_flag=True,
    help="実際には変更せず、移行計画のみ表示"
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    default=True,
    help="対話モードで実行"
)
@click.option(
    "--backup",
    is_flag=True,
    default=True,
    help="既存ファイルをバックアップ"
)
@click.pass_context
def migrate_command(
    ctx: click.Context,
    app: str,
    dry_run: bool,
    interactive: bool,
    backup: bool
):
    """DRFからDjango Ninjaへ移行します
    
    既存のDRF ViewSetとSerializerを分析し、
    対応するDjango Ninja APIに変換します。
    """
    
    current_dir = Path.cwd()
    app_path = current_dir / app
    
    console.print(f"\n[bold green]DRF → Django Ninja 移行ツール[/bold green]")
    console.print(f"対象アプリ: [cyan]{app}[/cyan]")
    
    # アプリケーションの存在確認
    if not app_path.exists():
        console.print(f"[red]❌ アプリケーション '{app}' が見つかりません。[/red]")
        return
    
    # DRFコードの分析
    analyzer = DRFAnalyzer(app_path)
    
    try:
        console.print("\n[blue]🔍 DRFコードを分析中...[/blue]")
        analysis_result = analyzer.analyze_app()
        
        if not analysis_result["serializers"] and not analysis_result["viewsets"]:
            console.print("[yellow]⚠️ DRFのSerializerやViewSetが見つかりませんでした。[/yellow]")
            return
            
    except Exception as e:
        console.print(f"[red]❌ 分析エラー: {str(e)}[/red]")
        return
    
    # 分析結果の表示
    _show_analysis_result(analysis_result)
    
    # 移行計画の確認
    if interactive and not questionary.confirm("この内容で移行を続行しますか？").ask():
        console.print("[yellow]移行をキャンセルしました。[/yellow]")
        return
    
    if dry_run:
        console.print("\n[blue]🧪 ドライラン完了: 実際の変更は行われませんでした。[/blue]")
        return
    
    # 移行の実行
    _execute_migration(current_dir, app, analysis_result, backup)
    
    console.print(f"\n[bold green]✅ {app} の移行が完了しました！[/bold green]")
    _show_migration_summary(app)

def _show_analysis_result(result: Dict[str, Any]):
    """分析結果を表示"""
    
    console.print(f"\n[bold blue]📊 分析結果:[/bold blue]")
    
    # Serializer一覧
    if result["serializers"]:
        table = Table(title="DRF Serializers")
        table.add_column("ファイル", style="cyan")
        table.add_column("クラス名", style="green")
        table.add_column("モデル", style="yellow")
        table.add_column("フィールド数", justify="right")
        
        for serializer in result["serializers"]:
            table.add_row(
                str(serializer["file_path"].name),
                serializer["class_name"],
                serializer.get("model", "不明"),
                str(len(serializer.get("fields", [])))
            )
        
        console.print(table)
    
    # ViewSet一覧
    if result["viewsets"]:
        table = Table(title="DRF ViewSets")
        table.add_column("ファイル", style="cyan")
        table.add_column("クラス名", style="green")
        table.add_column("モデル", style="yellow")
        table.add_column("アクション", style="magenta")
        
        for viewset in result["viewsets"]:
            actions = ", ".join(viewset.get("actions", []))
            table.add_row(
                str(viewset["file_path"].name),
                viewset["class_name"],
                viewset.get("model", "不明"),
                actions
            )
        
        console.print(table)
    
    # 検出された問題
    if result.get("issues"):
        console.print(f"\n[bold yellow]⚠️ 検出された問題:[/bold yellow]")
        for issue in result["issues"]:
            console.print(f"  • {issue}")

def _execute_migration(
    project_dir: Path,
    app_name: str,
    analysis_result: Dict[str, Any],
    backup: bool
):
    """移行を実行"""
    
    generator = APIGenerator()
    file_manager = FileManager()
    
    # プロジェクト設定の読み込み
    config = _load_project_config(project_dir)
    if not config:
        console.print("[red]❌ プロジェクト設定が見つかりません。[/red]")
        return
    
    ninja_base_dir = project_dir / config["project"]["django_app"] / "apis" / "ninja"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # バックアップ作成
        if backup:
            task1 = progress.add_task("既存ファイルをバックアップ中...", total=None)
            _create_backup(project_dir, app_name)
            progress.update(task1, completed=100)
        
        # Serializerの変換
        if analysis_result["serializers"]:
            task2 = progress.add_task("Serializerをスキーマに変換中...", total=len(analysis_result["serializers"]))
            
            for i, serializer in enumerate(analysis_result["serializers"]):
                schema_content = generator.convert_serializer_to_schema(serializer, config)
                
                # 出力先の決定
                feature_name = _extract_feature_name(serializer["class_name"])
                feature_dir = ninja_base_dir / "api_views" / feature_name
                feature_dir.mkdir(parents=True, exist_ok=True)
                
                # スキーマファイル作成
                schema_path = feature_dir / "schema.py"
                file_manager.write_file(schema_path, schema_content)
                
                progress.update(task2, advance=1)
        
        # ViewSetの変換
        if analysis_result["viewsets"]:
            task3 = progress.add_task("ViewSetをビューに変換中...", total=len(analysis_result["viewsets"]))
            
            for i, viewset in enumerate(analysis_result["viewsets"]):
                views_content = generator.convert_viewset_to_views(viewset, config)
                
                # 出力先の決定
                feature_name = _extract_feature_name(viewset["class_name"])
                feature_dir = ninja_base_dir / "api_views" / feature_name
                feature_dir.mkdir(parents=True, exist_ok=True)
                
                # ビューファイル作成
                views_path = feature_dir / "views.py"
                file_manager.write_file(views_path, views_content)
                
                # ルーター登録
                _update_main_api_file(project_dir, feature_name, config)
                
                progress.update(task3, advance=1)

def _create_backup(project_dir: Path, app_name: str):
    """既存ファイルのバックアップを作成"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_dir / f"backup_drf_migration_{timestamp}"
    
    # アプリケーションディレクトリをバックアップ
    app_source = project_dir / app_name
    if app_source.exists():
        shutil.copytree(app_source, backup_dir / app_name)
        console.print(f"[dim]バックアップ作成: {backup_dir}[/dim]")

def _extract_feature_name(class_name: str) -> str:
    """クラス名から機能名を抽出"""
    # UserSerializer -> users
    # ProductViewSet -> products
    import inflect
    
    p = inflect.engine()
    
    # 末尾のSerializer, ViewSetを除去
    name = class_name
    for suffix in ["Serializer", "ViewSet", "View"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    # 複数形に変換
    plural = p.plural(name.lower())
    return plural

def _load_project_config(project_dir: Path):
    """プロジェクト設定を読み込み"""
    from ..config import get_config_path
    import yaml
    
    config_path = get_config_path(project_dir)
    if not config_path.exists():
        return None
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _update_main_api_file(project_dir: Path, feature_name: str, config: dict):
    """メインのapi.pyファイルにルーターを追加"""
    app_name = config["project"]["django_app"]
    api_file = project_dir / app_name / "apis" / "ninja" / "api.py"
    
    if not api_file.exists():
        return
    
    content = api_file.read_text(encoding="utf-8")
    
    # ルーター追加（重複チェック付き）
    import_line = f"from {app_name}.apis.ninja.api_views.{feature_name}.views import router as {feature_name}_router"
    router_line = f'api.add_router("", {feature_name}_router)'
    
    if import_line not in content:
        content = import_line + "\n" + content
    
    if router_line not in content:
        content += "\n" + router_line
    
    api_file.write_text(content, encoding="utf-8")

def _show_migration_summary(app_name: str):
    """移行完了後のサマリーを表示"""
    console.print(f"\n[bold blue]📝 移行サマリー:[/bold blue]")
    console.print(f"  ✅ DRF Serializerをスキーマに変換完了")
    console.print(f"  ✅ DRF ViewSetをビューに変換完了")
    console.print(f"  ✅ ルーター登録完了")
    
    console.print(f"\n[bold blue]🔄 次のステップ:[/bold blue]")
    console.print("1. [cyan]python manage.py runserver[/cyan] でサーバー起動")
    console.print("2. http://localhost:8000/ninja_api/docs でAPIドキュメント確認")
    console.print("3. [cyan]npm run ninja:generate[/cyan] でTypeScriptクライアント生成")
    console.print("4. 既存のDRFコードをテストして段階的に置き換え")
    
    console.print(f"\n[bold yellow]⚠️ 注意事項:[/bold yellow]")
    console.print("  • 生成されたコードは確認・調整が必要です")
    console.print("  • カスタムバリデーションやパーミッションは手動で移行してください")
    console.print("  • テストコードも更新が必要です")