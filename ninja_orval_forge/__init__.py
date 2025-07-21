"""
ninja-orval-forge: Django Ninja + Orval統合環境構築ツール

DRFからDjango Ninjaへの移行とフルスタック型安全開発を支援するCLIツール
"""

__version__ = "0.1.0"
__author__ = "Sayaka"
__email__ = "your-email@example.com"
__description__ = "Django Ninja + Orval統合環境構築ツール"

from .cli import main

__all__ = ["main"]