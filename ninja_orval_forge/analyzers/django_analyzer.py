"""
Django プロジェクト解析器
"""

import ast
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class DjangoAnalyzer:
    """Djangoプロジェクトとモデルを解析"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        
    def analyze_model(self, model_name: str) -> Dict[str, Any]:
        """指定されたモデルを解析"""
        model_info = self._find_model(model_name)
        if not model_info:
            raise ValueError(f"モデル '{model_name}' が見つかりません")
            
        return model_info
    
    def get_project_apps(self) -> List[str]:
        """プロジェクト内のDjangoアプリケーションを取得"""
        apps = []
        
        for item in self.project_path.iterdir():
            if item.is_dir() and self._is_django_app(item):
                apps.append(item.name)
                
        return apps
    
    def _find_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """モデルを検索"""
        for app_dir in self.project_path.iterdir():
            if not app_dir.is_dir() or not self._is_django_app(app_dir):
                continue
                
            models_file = app_dir / "models.py"
            if models_file.exists():
                model_info = self._parse_models_file(models_file, model_name)
                if model_info:
                    return model_info
                    
            # models/ディレクトリの場合
            models_dir = app_dir / "models"
            if models_dir.is_dir():
                for model_file in models_dir.glob("*.py"):
                    if model_file.name == "__init__.py":
                        continue
                    model_info = self._parse_models_file(model_file, model_name)
                    if model_info:
                        return model_info
        
        return None
    
    def _is_django_app(self, path: Path) -> bool:
        """Djangoアプリケーションかどうかを判定"""
        # apps.pyまたはmodels.pyが存在するかチェック
        return (
            (path / "apps.py").exists() or
            (path / "models.py").exists() or
            (path / "models").is_dir()
        )
    
    def _parse_models_file(self, file_path: Path, target_model: str) -> Optional[Dict[str, Any]]:
        """models.pyファイルを解析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if (isinstance(node, ast.ClassDef) and 
                    node.name == target_model and
                    self._is_model_class(node)):
                    
                    return self._extract_model_info(node, file_path)
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return None
    
    def _is_model_class(self, class_node: ast.ClassDef) -> bool:
        """Django Modelクラスかどうかを判定"""
        for base in class_node.bases:
            if isinstance(base, ast.Attribute):
                if (isinstance(base.value, ast.Name) and 
                    base.value.id == 'models' and 
                    base.attr == 'Model'):
                    return True
            elif isinstance(base, ast.Name) and base.id == 'Model':
                return True
                
        return False
    
    def _extract_model_info(self, class_node: ast.ClassDef, file_path: Path) -> Dict[str, Any]:
        """モデル情報を抽出"""
        fields = []
        meta_info = {}
        
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                # フィールドの解析
                field_info = self._extract_field_info(node)
                if field_info:
                    fields.append(field_info)
                    
            elif isinstance(node, ast.ClassDef) and node.name == 'Meta':
                # Metaクラスの解析
                meta_info = self._extract_meta_info(node)
        
        return {
            'model_class': class_node.name,
            'file_path': file_path,
            'fields': fields,
            'meta': meta_info,
            'description': self._extract_docstring(class_node),
        }
    
    def _extract_field_info(self, assign_node: ast.Assign) -> Optional[Dict[str, Any]]:
        """フィールド情報を抽出"""
        if len(assign_node.targets) != 1:
            return None
            
        target = assign_node.targets[0]
        if not isinstance(target, ast.Name):
            return None
            
        field_name = target.id
        
        # 特殊フィールドをスキップ
        if field_name.startswith('_') or field_name in ['objects', 'DoesNotExist']:
            return None
        
        field_type = self._extract_field_type(assign_node.value)
        if not field_type:
            return None
            
        field_options = self._extract_field_options(assign_node.value)
        
        return {
            'name': field_name,
            'type': field_type,
            **field_options
        }
    
    def _extract_field_type(self, value_node: ast.AST) -> Optional[str]:
        """フィールドタイプを抽出"""
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Attribute):
                if (isinstance(value_node.func.value, ast.Name) and 
                    value_node.func.value.id == 'models'):
                    return value_node.func.attr
                    
        return None
    
    def _extract_field_options(self, value_node: ast.AST) -> Dict[str, Any]:
        """フィールドオプションを抽出"""
        options = {}
        
        if isinstance(value_node, ast.Call):
            # キーワード引数の解析
            for keyword in value_node.keywords:
                if keyword.arg:
                    try:
                        options[keyword.arg] = ast.literal_eval(keyword.value)
                    except (ValueError, TypeError):
                        # 複雑な値の場合は文字列として保存
                        options[keyword.arg] = ast.unparse(keyword.value)
                        
        return options
    
    def _extract_meta_info(self, meta_node: ast.ClassDef) -> Dict[str, Any]:
        """Metaクラス情報を抽出"""
        meta = {}
        
        for node in meta_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        try:
                            meta[target.id] = ast.literal_eval(node.value)
                        except (ValueError, TypeError):
                            meta[target.id] = ast.unparse(node.value)
                            
        return meta
    
    def _extract_docstring(self, class_node: ast.ClassDef) -> str:
        """クラスのdocstringを抽出"""
        if (class_node.body and 
            isinstance(class_node.body[0], ast.Expr) and
            isinstance(class_node.body[0].value, ast.Constant)):
            return class_node.body[0].value.value
            
        return ""