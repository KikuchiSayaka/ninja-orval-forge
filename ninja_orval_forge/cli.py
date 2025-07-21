"""
ninja-orval-forge CLIメインモジュール
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .commands.init import init_command
from .commands.generate import generate_command
from .commands.migrate import migrate_command

console = Console()

def print_banner():
    """CLIバナーを表示"""
    banner_text = Text("ninja-orval-forge", style="bold blue")
    subtitle = Text(f"v{__version__} - Django Ninja + Orval統合環境構築ツール", style="dim")
    
    panel = Panel(
        Text.assemble(banner_text, "\n", subtitle),
        expand=False,
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="ninja-orval-forge")
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="詳細な出力を表示"
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """
    Django Ninja + Orval統合環境構築ツール
    
    DRFからDjango Ninjaへの移行とフルスタック型安全開発を支援します。
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("\n[bold green]使用可能なコマンド:[/bold green]")
        console.print("  [cyan]init[/cyan]     - プロジェクトの初期化")
        console.print("  [cyan]generate[/cyan] - API機能の生成")
        console.print("  [cyan]migrate[/cyan]  - DRFからの移行")
        console.print("\nヘルプ: [dim]ninja-orval-forge --help[/dim]")

# サブコマンドの登録
cli.add_command(init_command, name="init")
cli.add_command(generate_command, name="generate")
cli.add_command(migrate_command, name="migrate")

def main():
    """エントリーポイント"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]処理を中断しました。[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]エラーが発生しました: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()