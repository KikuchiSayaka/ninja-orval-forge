# ninja-orval-forge

[![PyPI version](https://badge.fury.io/py/ninja-orval-forge.svg)](https://badge.fury.io/py/ninja-orval-forge)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Django Ninja + Orval 統合環境構築ツール**

Django REST Framework (DRF) から Django Ninja への移行と、TypeScript 型安全なフロントエンド開発環境を自動構築する CLI ツールです。

## 特徴

- **DRF → Django Ninja 自動移行**: 既存の Serializer と ViewSet を自動変換
- **型安全な API 開発**: Pydantic + OpenAPI + TypeScript の完全統合
- **Orval 自動設定**: TypeScript クライアントと Vue/React コンポーネントの自動生成
- **プロジェクトテンプレート**: 実用的なディレクトリ構造とベストプラクティス
- **Vue 3 統合**: Composition API 対応のコンポーネントと Composable 生成

## インストール

```bash
pip install ninja-orval-forge
```

## クイックスタート

### 1. プロジェクト初期化

```bash
cd your-django-project
ninja-orval-forge init --name "My API Project"
```

対話モードで以下を選択：

- フロントエンドフレームワーク（Vue/React/Angular）
- TypeScript 使用の有無
- 認証設定
- レスポンス形式（キャメルケース）

### 2. API 機能生成

```bash
# 新しいAPIエンドポイントを生成
ninja-orval-forge generate users --model User

# 特定の操作のみ生成
ninja-orval-forge generate products --model Product --operations list create update
```

### 3. DRF からの移行

```bash
# 既存のDRFコードを自動変換
ninja-orval-forge migrate --app myapp --dry-run
ninja-orval-forge migrate --app myapp
```

### 4. TypeScript クライアント生成

```bash
# Django開発サーバー起動
python manage.py runserver

# 別ターミナルでクライアント生成
npm run ninja:generate
```

## 生成されるファイル構造

```
your-project/
├── .ninja-orval-forge.yml          # 設定ファイル
├── orval.config.ts                 # Orval設定
├── main/                           # Djangoアプリ
│   └── apis/
│       └── ninja/
│           ├── api.py              # メインAPI設定
│           ├── base_schemas.py     # API共通の汎用スキーマ
│           ├── api_views/          # 機能別ビュー
│           │   └── users/
│           │       ├── schema.py   # ユーザーAPI専用スキーマ
│           │       └── views.py    # Django Ninjaビュー
│           ├── shared/             # 共通ユーティリティ
│           │   └── pagination_utils.py
│           └── openapi/            # OpenAPIスキーマ（JSON形式）
└── frontend/                       # フロントエンド
    ├── api/                        # Orval出力
    │   ├── client/                 # APIクライアント関数
    │   └── schema/                 # TypeScript型定義
    ├── composables/                # useXXX系Composable関数
    │   └── useUsers.ts
    └── components/
        └── UserList.vue           # 生成されたVueコンポーネント
```

### ディレクトリの役割

- **`openapi/`**: Django Ninja が生成する OpenAPI スキーマ（JSON 形式）
- **`base_schemas.py`**: 全 API 共通の汎用スキーマ（ページネーション等）
- **`api_views/*/schema.py`**: 各 API 専用の入出力スキーマ
- **`shared/`**: 共通ユーティリティ（ページネーション等
- **`frontend/api/client/`**: Orval が生成する API クライアント関数
- **`frontend/api/schema/`**: TypeScript 型定義ファイル
- **`frontend/composables/`**: Vue Composable 関数

## コマンドリファレンス

### `init` - プロジェクト初期化

```bash
ninja-orval-forge init [OPTIONS]

Options:
  --name TEXT        プロジェクト名 [required]
  --app TEXT         Djangoアプリ名 [default: main]
  --frontend CHOICE  フロントエンドフレームワーク [vue|react|angular|none]
  --interactive      対話モード [default: True]
  --force           既存設定を上書き
```

### `generate` - API 機能生成

```bash
ninja-orval-forge generate FEATURE_NAME [OPTIONS]

Arguments:
  FEATURE_NAME  機能名（例: users, products）

Options:
  --model TEXT              対象Djangoモデル [required]
  --operations [list|retrieve|create|update|delete]
                           生成する操作（複数指定可能）
  --interactive            対話モード [default: True]
  --force                  既存ファイルを上書き
```

### `migrate` - DRF 移行

```bash
ninja-orval-forge migrate [OPTIONS]

Options:
  --app TEXT       移行対象アプリ [required]
  --dry-run        実際には変更せず計画のみ表示
  --interactive    対話モード [default: True]
  --backup         既存ファイルをバックアップ [default: True]
```

## 設定ファイル

`.ninja-orval-forge.yml`で詳細な設定をカスタマイズできます：

```yaml
project:
  name: "My API Project"
  django_app: "main"
  api_prefix: "/api/v1"
  api_version: "1.0.0"

ninja:
  auth_enabled: true
  auth_class: "JWTAuth"
  camel_case_response: true

orval:
  output_path: "./src/api"
  client_type: "fetch"
  split_mode: "tags-split"

frontend:
  framework: "vue"
  typescript: true

templates:
  pagination_limit: 20
  max_page_size: 100
  default_ordering: "-id"
```

## 生成されるコード例

### Django Ninja ビュー

```python
from ninja import Router, Query, Path
from .schema import UserSchema, UserListSchema
from main.models import User

router = Router(tags=["users"])

@router.get("/users", response=UserListSchema)
def list_users(
    request,
    pagination: Query[PaginationQuery],
):
    qs = User.objects.all().order_by("-id")
    total_count = qs.count()
    paginated_qs = PaginatorResponseBuilder.paginate_queryset(qs, pagination)
    results = [UserSchema.model_validate(u).model_dump() for u in paginated_qs]
    return PaginatorResponseBuilder.build_response(total_count, results)
```

### Pydantic スキーマ

```python
from pydantic import BaseModel, Field, ConfigDict

class UserSchema(BaseModel):
    id: int
    email: str = Field(..., description="メールアドレス")
    first_name: str = Field(..., description="名前")
    is_active: bool = Field(True, description="アクティブフラグ")

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=lambda field_name: ''.join(
            word.capitalize() if i else word for i, word in enumerate(field_name.split('_'))
        ),
    )
```

### Vue コンポーネント

```vue
<template>
  <div class="user-list">
    <table v-if="!loading && users.length > 0">
      <thead>
        <tr>
          <th>ID</th>
          <th>メール</th>
          <th>名前</th>
          <th>ステータス</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.email }}</td>
          <td>{{ user.firstName }}</td>
          <td>{{ user.isActive ? "アクティブ" : "無効" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useUserList } from "@/composables/useUsers";

const { state, fetchUsers } = useUserList();

onMounted(() => {
  fetchUsers();
});
</script>
```

## 開発ワークフロー

1. **API 設計**: Django モデルを定義
2. **生成**: `ninja-orval-forge generate`で API コードを生成
3. **テスト**: SwaggerUI (`/ninja_api/docs`) で API を確認
4. **クライアント生成**: `npm run ninja:generate`で TypeScript クライアントを生成
5. **フロントエンド開発**: 型安全な API クライアントを使用して UI 開発

## ドキュメント

- [インストールガイド](docs/installation.md)
- [チュートリアル](docs/tutorial.md)
- [設定リファレンス](docs/configuration.md)
- [テンプレートカスタマイズ](docs/templates.md)
- [FAQ](docs/faq.md)

## コントリビューション

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 開発環境セットアップ

```bash
git clone https://github.com/yourusername/ninja-orval-forge.git
cd ninja-orval-forge
poetry install
poetry shell

# テスト実行
pytest

# リント
ruff check .

# フォーマット
black .
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

**ninja-orval-forge** - DRF から Django Ninja への移行と型安全なフルスタック開発を簡単にします。
