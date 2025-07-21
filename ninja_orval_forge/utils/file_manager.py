"""
ファイル管理ユーティリティ
"""

import os
import shutil
from pathlib import Path
from typing import Union


class FileManager:
    """ファイル操作を管理するクラス"""
    
    @staticmethod
    def write_file(file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルに内容を書き込み"""
        file_path = Path(file_path)
        
        # ディレクトリが存在しない場合は作成
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
    
    @staticmethod
    def read_file(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
        """ファイルの内容を読み込み"""
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    
    @staticmethod
    def file_exists(file_path: Union[str, Path]) -> bool:
        """ファイルが存在するかチェック"""
        return Path(file_path).exists()
    
    @staticmethod
    def create_directory(dir_path: Union[str, Path]) -> None:
        """ディレクトリを作成"""
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """ファイルをコピー"""
        src_path = Path(src)
        dst_path = Path(dst)
        
        # コピー先のディレクトリが存在しない場合は作成
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(src_path, dst_path)
    
    @staticmethod
    def copy_directory(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """ディレクトリを再帰的にコピー"""
        shutil.copytree(src, dst, dirs_exist_ok=True)
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> None:
        """ファイルを削除"""
        file_path = Path(file_path)
        if file_path.exists():
            file_path.unlink()
    
    @staticmethod
    def delete_directory(dir_path: Union[str, Path]) -> None:
        """ディレクトリを削除"""
        dir_path = Path(dir_path)
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    @staticmethod
    def append_to_file(file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルに内容を追記"""
        file_path = Path(file_path)
        
        # ディレクトリが存在しない場合は作成
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'a', encoding=encoding) as f:
            f.write(content)
    
    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_suffix: str = ".bak") -> Path:
        """ファイルをバックアップ"""
        file_path = Path(file_path)
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        
        if file_path.exists():
            shutil.copy2(file_path, backup_path)
            
        return backup_path
    
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = "*") -> list[Path]:
        """ディレクトリ内のファイルを検索"""
        directory = Path(directory)
        return list(directory.rglob(pattern))
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """ファイルサイズを取得（バイト単位）"""
        return Path(file_path).stat().st_size
    
    @staticmethod
    def is_text_file(file_path: Union[str, Path]) -> bool:
        """テキストファイルかどうかを判定"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # 最初の1KBを読んでみる
            return True
        except UnicodeDecodeError:
            return False
    
    @staticmethod
    def ensure_directory_exists(dir_path: Union[str, Path]) -> None:
        """ディレクトリが存在することを保証"""
        Path(dir_path).mkdir(parents=True, exist_ok=True)