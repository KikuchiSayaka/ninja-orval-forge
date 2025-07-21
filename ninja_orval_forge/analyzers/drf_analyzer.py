"""
Django REST Framework 解析器
"""

import ast
from pathlib import Path
from typing import Dict, Any, List, Optional


class DRFAnalyzer:
    """DRF Serializer と ViewSet を解析"""
    
    def __init__(self, app_path: Path):
        self.app_path = app_path
        
    def analyze_app(self) -> Dict[str, Any]:
        """アプリケーション全体のDRFコードを解析"""
        result = {
            'serializers': [],
            'viewsets': [],
            'issues': []
        }
        
        # Serializerの解析
        serializers_file = self.app_path / "serializers.py"
        if serializers_file.exists():
            serializers = self._analyze_serializers(serializers_file)
            result['serializers'].extend(serializers)
        
        # ViewSetの解析
        views_file = self.app_path / "views.py"
        if views_file.exists():
            viewsets = self._analyze_viewsets(views_file)
            result['viewsets'].extend(viewsets)
            
        return result
    
    def _analyze_serializers(self, file_path: Path) -> List[Dict[str, Any]]:
        """Serializerファイルを解析"""
        serializers = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if (isinstance(node, ast.ClassDef) and 
                    self._is_serializer_class(node)):
                    
                    serializer_info = self._extract_serializer_info(node, file_path)
                    serializers.append(serializer_info)
                    
        except Exception as e:
            print(f"Error analyzing serializers in {file_path}: {e}")
            
        return serializers
    
    def _analyze_viewsets(self, file_path: Path) -> List[Dict[str, Any]]:
        """ViewSetファイルを解析"""
        viewsets = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if (isinstance(node, ast.ClassDef) and 
                    self._is_viewset_class(node)):
                    
                    viewset_info = self._extract_viewset_info(node, file_path)
                    viewsets.append(viewset_info)
                    
        except Exception as e:
            print(f"Error analyzing viewsets in {file_path}: {e}")
            
        return viewsets
    
    def _is_serializer_class(self, class_node: ast.ClassDef) -> bool:
        """Serializerクラスかどうかを判定"""
        for base in class_node.bases:
            if isinstance(base, ast.Attribute):
                if (isinstance(base.value, ast.Name) and 
                    base.value.id == 'serializers' and 
                    'Serializer' in base.attr):
                    return True
            elif isinstance(base, ast.Name) and 'Serializer' in base.id:
                return True
                
        return False
    
    def _is_viewset_class(self, class_node: ast.ClassDef) -> bool:
        """ViewSetクラスかどうかを判定"""
        for base in class_node.bases:
            if isinstance(base, ast.Attribute):
                if (isinstance(base.value, ast.Name) and 
                    base.value.id == 'viewsets' and 
                    'ViewSet' in base.attr):
                    return True
            elif isinstance(base, ast.Name) and 'ViewSet' in base.id:
                return True
                
        return False
    
    def _extract_serializer_info(self, class_node: ast.ClassDef, file_path: Path) -> Dict[str, Any]:
        """Serializer情報を抽出"""
        fields = []
        model = None
        meta_info = {}
        
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                # フィールドの解析
                field_info = self._extract_serializer_field(node)
                if field_info:
                    fields.append(field_info)
                    
            elif isinstance(node, ast.ClassDef) and node.name == 'Meta':
                # Metaクラスの解析
                meta_info = self._extract_meta_info(node)
                model = meta_info.get('model')
        
        return {
            'class_name': class_node.name,
            'file_path': file_path,
            'model': model,
            'fields': fields,
            'meta': meta_info,
        }
    
    def _extract_viewset_info(self, class_node: ast.ClassDef, file_path: Path) -> Dict[str, Any]:
        """ViewSet情報を抽出"""
        queryset = None
        serializer_class = None
        actions = []
        
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == 'queryset':
                            queryset = ast.unparse(node.value)
                        elif target.id == 'serializer_class':
                            serializer_class = ast.unparse(node.value)
                            
            elif isinstance(node, ast.FunctionDef):
                # カスタムアクションの検出
                if self._has_action_decorator(node):
                    actions.append(node.name)
        
        # 標準的なViewSetアクションを追加
        base_actions = self._get_standard_actions(class_node)
        actions.extend(base_actions)
        
        return {
            'class_name': class_node.name,
            'file_path': file_path,
            'queryset': queryset,
            'serializer_class': serializer_class,
            'actions': list(set(actions)),  # 重複除去
        }
    
    def _extract_serializer_field(self, assign_node: ast.Assign) -> Optional[Dict[str, Any]]:
        """Serializerフィールドを解析"""
        if len(assign_node.targets) != 1:
            return None
            
        target = assign_node.targets[0]
        if not isinstance(target, ast.Name):
            return None
            
        field_name = target.id
        
        # serializersモジュールのフィールドかチェック
        if isinstance(assign_node.value, ast.Call):
            if isinstance(assign_node.value.func, ast.Attribute):
                if (isinstance(assign_node.value.func.value, ast.Name) and 
                    assign_node.value.func.value.id == 'serializers'):
                    
                    field_type = assign_node.value.func.attr
                    return {
                        'name': field_name,
                        'type': field_type,
                    }
        
        return None
    
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
    
    def _has_action_decorator(self, func_node: ast.FunctionDef) -> bool:
        """@actionデコレータがあるかチェック"""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'action':
                return True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'action':
                    return True
                    
        return False
    
    def _get_standard_actions(self, class_node: ast.ClassDef) -> List[str]:
        """標準的なViewSetアクションを取得"""
        # 基底クラスに基づいて標準アクションを判定
        for base in class_node.bases:
            base_name = ''
            if isinstance(base, ast.Attribute):
                base_name = base.attr
            elif isinstance(base, ast.Name):
                base_name = base.id
                
            if 'ModelViewSet' in base_name:
                return ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']
            elif 'ReadOnlyModelViewSet' in base_name:
                return ['list', 'retrieve']
            elif 'ViewSet' in base_name:
                return ['list', 'create', 'retrieve', 'update', 'destroy']
                
        return []