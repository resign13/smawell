from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
SCHEMA_SQL_CANDIDATES = (
    REPO_DIR / "db" / "postgres" / "init_smawell_admin.sql",
    REPO_DIR.parent / "shopify-admin" / "db" / "postgres" / "init_smawell_admin.sql",
)
SCHEMA_SQL_FILE = next((path for path in SCHEMA_SQL_CANDIDATES if path.exists()), SCHEMA_SQL_CANDIDATES[0])


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(BASE_DIR / ".env")

from psycopg import connect
from psycopg.errors import InvalidCatalogName
from psycopg.rows import dict_row
from psycopg.sql import Identifier, SQL

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("zh", "en")
HOME_SECTION_KEYS = ("bestSeller", "newArrival", "specialPrice")
ORDER_STATUSES = ("pending_payment", "paid", "shipped", "completed", "cancelled")


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")

DB_HOST = os.environ.get("PGHOST", "127.0.0.1")
DB_PORT = int(os.environ.get("PGPORT", "5432"))
DB_NAME = os.environ.get("PGDATABASE", "smawell_admin")
DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASSWORD = os.environ.get("PGPASSWORD") or os.environ.get("POSTGRES_PASSWORD") or ""


def _connect(dbname: str | None = None, *, autocommit: bool = False):
    kwargs: dict[str, Any] = {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": dbname or DB_NAME,
        "user": DB_USER,
        "row_factory": dict_row,
        "autocommit": autocommit,
    }
    if DB_PASSWORD:
        kwargs["password"] = DB_PASSWORD
    return connect(**kwargs)


@contextmanager
def get_connection() -> Iterator[Any]:
    with _connect() as conn:
        yield conn



def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except Exception:
            return [value.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item or "").strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]
    return []


def _serialize_label_image_urls(value: Any, fallback: str = "") -> str:
    urls = _json_list(value)[:5]
    if not urls and fallback:
        urls = [str(fallback).strip()]
    return json.dumps(urls[:5], ensure_ascii=False)


def _parse_label_image_urls(row: dict[str, Any]) -> list[str]:
    urls = _json_list(row.get("label_image_urls"))[:5]
    if not urls and str(row.get("label_pdf_url") or "").strip():
        urls = [str(row.get("label_pdf_url") or "").strip()]
    return urls

def verify_database_connection() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
            _apply_schema_migrations(cur)
        conn.commit()


def ensure_database_ready() -> None:
    try:
        with _connect():
            pass
    except InvalidCatalogName:
        with _connect("postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(SQL("CREATE DATABASE {}").format(Identifier(DB_NAME)))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='products') AS exists"
            )
            row = cur.fetchone()
            if not row or not row["exists"]:
                if not SCHEMA_SQL_FILE.exists():
                    raise FileNotFoundError(f"Database schema file not found: {SCHEMA_SQL_FILE}")
                schema_sql = SCHEMA_SQL_FILE.read_text(encoding="utf-8-sig")
                cur.execute(schema_sql)
            _apply_schema_migrations(cur)
        conn.commit()


def _fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return list(cur.fetchall())


def _fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def _sync_order_status_constraint(cur: Any) -> None:
    cur.execute(
        """
        SELECT con.conname
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = con.connamespace
        WHERE nsp.nspname = 'public'
          AND rel.relname = 'orders'
          AND con.contype = 'c'
          AND pg_get_constraintdef(con.oid) ILIKE '%status%'
        """
    )
    rows = cur.fetchall()
    for row in rows:
        cur.execute(SQL("ALTER TABLE orders DROP CONSTRAINT IF EXISTS {}").format(Identifier(row["conname"])))
    cur.execute(
        """
        ALTER TABLE orders
        ADD CONSTRAINT orders_status_check
        CHECK (status IN ('pending_payment', 'paid', 'shipped', 'completed', 'cancelled'))
        """
    )


def _migrate_order_status_values(cur: Any) -> None:
    cur.execute(
        """
        SELECT con.conname
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = con.connamespace
        WHERE nsp.nspname = 'public'
          AND rel.relname = 'orders'
          AND con.contype = 'c'
          AND pg_get_constraintdef(con.oid) ILIKE '%status%'
        """
    )
    rows = cur.fetchall()
    for row in rows:
        cur.execute(SQL("ALTER TABLE orders DROP CONSTRAINT IF EXISTS {}").format(Identifier(row["conname"])))

    cur.execute("UPDATE orders SET status = 'pending_payment' WHERE status = 'pending'")
    cur.execute("UPDATE orders SET status = 'paid' WHERE status = 'packed'")
    _sync_order_status_constraint(cur)


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return str(value)


def _num(value: Any) -> int | float:
    if isinstance(value, Decimal):
        as_int = int(value)
        return as_int if value == as_int else float(value)
    return value


def _empty_bundle() -> dict[str, str]:
    return {lang: "" for lang in SUPPORTED_LANGS}


def _apply_schema_migrations(cur: Any) -> None:
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS size_chart_image_url TEXT")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS description_image_url TEXT")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS product_code VARCHAR(120) NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS color_group VARCHAR(120) NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS color_name VARCHAR(120) NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS color_hex VARCHAR(32) NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS image_url TEXT")
    cur.execute("UPDATE products SET product_code = COALESCE(NULLIF(product_code, ''), sku), color_group = COALESCE(NULLIF(color_group, ''), sku), color_name = COALESCE(NULLIF(color_name, ''), 'Default'), color_hex = COALESCE(NULLIF(color_hex, ''), '#999999')")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_product_code ON products(product_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_color_group ON products(color_group)")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS product_size_prices (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
          size_code VARCHAR(32) NOT NULL,
          price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
          sort_order INTEGER NOT NULL DEFAULT 0,
          UNIQUE (product_id, size_code)
        )
        """
    )
    cur.execute("ALTER TABLE product_size_prices ADD COLUMN IF NOT EXISTS stock INTEGER NOT NULL DEFAULT 0")
    cur.execute(
        """
        WITH grouped AS (
          SELECT product_id, COUNT(*)::INTEGER AS row_count, COALESCE(SUM(stock), 0)::INTEGER AS current_stock
          FROM product_size_prices
          GROUP BY product_id
        ),
        ranked AS (
          SELECT id, product_id, ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY sort_order, id) AS row_index
          FROM product_size_prices
        )
        UPDATE product_size_prices psp
        SET stock = CASE
          WHEN ranked.row_index = 1
            THEN (products.stock / grouped.row_count) + (products.stock % grouped.row_count)
          ELSE products.stock / grouped.row_count
        END
        FROM ranked
        JOIN grouped ON grouped.product_id = ranked.product_id
        JOIN products ON products.id = ranked.product_id
        WHERE psp.id = ranked.id
          AND grouped.row_count > 0
          AND grouped.current_stock = 0
          AND products.stock > 0
        """
    )
    cur.execute("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS size_code VARCHAR(32)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS contact_email VARCHAR(190)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS first_name VARCHAR(120)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS last_name VARCHAR(120)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS address_line1 TEXT")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS apartment VARCHAR(190)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS city VARCHAR(120)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS state VARCHAR(120)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS postal_code VARCHAR(40)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS tracking_no VARCHAR(120)")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_link TEXT")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_fee NUMERIC(12, 2) NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS label_pdf_url TEXT")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS label_image_urls TEXT NOT NULL DEFAULT '[]'")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipped_at TIMESTAMPTZ")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ")
    _migrate_order_status_values(cur)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS homepage_configs (
          id SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
          hero_banner_ids TEXT NOT NULL DEFAULT '{}',
          hero_banner_images TEXT NOT NULL DEFAULT '{}',
          section_product_ids TEXT NOT NULL DEFAULT '{}',
          collection_product_ids TEXT NOT NULL DEFAULT '{}',
          display_category_keys TEXT NOT NULL DEFAULT '[]',
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    cur.execute("ALTER TABLE homepage_configs ADD COLUMN IF NOT EXISTS hero_banner_images TEXT NOT NULL DEFAULT '{}'")
    cur.execute("ALTER TABLE homepage_configs ADD COLUMN IF NOT EXISTS collection_product_ids TEXT NOT NULL DEFAULT '{}'")


def _build_product_bundles(product_ids: list[int]) -> tuple[
    dict[int, dict[str, str]],
    dict[int, dict[str, str]],
    dict[int, dict[str, str]],
    dict[int, list[str]],
    dict[int, list[str]],
    dict[int, list[dict[str, Any]]],
    dict[int, list[dict[str, Any]]],
]:
    translation_rows = _fetch_all(
        """
        SELECT product_id, lang_code, name, summary, description
        FROM product_translations
        WHERE product_id = ANY(%s)
        ORDER BY product_id, lang_code
        """,
        (product_ids,),
    )
    image_rows = _fetch_all(
        """
        SELECT product_id, image_url
        FROM product_images
        WHERE product_id = ANY(%s)
        ORDER BY product_id, sort_order, id
        """,
        (product_ids,),
    )
    size_rows = _fetch_all(
        """
        SELECT product_id, size_code
        FROM product_sizes
        WHERE product_id = ANY(%s)
        ORDER BY product_id, sort_order, id
        """,
        (product_ids,),
    )
    size_price_rows = _fetch_all(
        """
        SELECT product_id, size_code, price, stock, sort_order
        FROM product_size_prices
        WHERE product_id = ANY(%s)
        ORDER BY product_id, sort_order, id
        """,
        (product_ids,),
    )

    names = {product_id: _empty_bundle() for product_id in product_ids}
    summaries = {product_id: _empty_bundle() for product_id in product_ids}
    descriptions = {product_id: _empty_bundle() for product_id in product_ids}
    galleries = {product_id: [] for product_id in product_ids}
    sizes = {product_id: [] for product_id in product_ids}
    size_prices = {product_id: [] for product_id in product_ids}

    for row in translation_rows:
        product_id = int(row["product_id"])
        lang = row["lang_code"]
        names[product_id][lang] = row["name"] or ""
        summaries[product_id][lang] = row["summary"] or ""
        descriptions[product_id][lang] = row["description"] or ""
    for row in image_rows:
        galleries[int(row["product_id"])].append(row["image_url"])
    for row in size_rows:
        sizes[int(row["product_id"])].append(row["size_code"])
    for row in size_price_rows:
        size_prices[int(row["product_id"])].append(
            {
                "sizeCode": row["size_code"],
                "price": _num(row["price"]),
                "stock": int(row["stock"]),
                "sortOrder": int(row["sort_order"]),
            }
        )
    return names, summaries, descriptions, galleries, sizes, size_prices


def _build_product_result(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    product_ids = [int(row["id"]) for row in rows]
    names, summaries, descriptions, galleries, sizes, size_prices = _build_product_bundles(product_ids)
    items: list[dict[str, Any]] = []
    for row in rows:
        product_id = int(row["id"])
        size_price_list = size_prices[product_id]
        default_price = size_price_list[0]["price"] if size_price_list else _num(row["price"])
        items.append(
            {
                "id": product_id,
                "slug": row["slug"],
                "sku": row["sku"],
                "productCode": row.get("product_code") or "",
                "colorGroup": row.get("color_group") or "",
                "colorName": row.get("color_name") or "",
                "colorHex": row.get("color_hex") or "",
                "categoryKey": row["category_key"],
                "categoryLabel": row.get("category_label", ""),
                "price": default_price,
                "formattedPrice": f"${default_price}",
                "stock": int(row["stock"]),
                "featured": bool(row["featured"]),
                "origin": row["origin"] or "",
                "sizes": sizes[product_id],
                "sizePrices": size_price_list,
                "image": row["main_image_url"],
                "gallery": galleries[product_id],
                "sizeChartImage": row.get("size_chart_image_url") or "",
                "descriptionImage": row.get("description_image_url") or "",
                "name": names[product_id],
                "summary": summaries[product_id],
                "description": descriptions[product_id],
            }
        )
    return items


def _product_base_query() -> str:
    return """
        SELECT
          p.id,
          p.slug,
          p.sku,
          p.product_code,
          p.color_group,
          p.color_name,
          p.color_hex,
          p.price,
          p.stock,
          p.featured,
          p.origin,
          p.main_image_url,
          p.size_chart_image_url,
          p.description_image_url,
          pc.category_key,
          pct.label AS category_label
        FROM products p
        JOIN product_categories pc ON pc.id = p.category_id
        LEFT JOIN product_category_translations pct
          ON pct.category_id = pc.id AND pct.lang_code = %s
    """


def _format_color_options(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": int(row["id"]),
            "slug": row["slug"],
            "productCode": row.get("product_code") or "",
            "colorName": row.get("color_name") or "",
            "colorHex": row.get("color_hex") or "",
            "image": row["main_image_url"],
            "stock": int(row["stock"]),
        }
        for row in rows
    ]


def _product_code_family_prefix(product_code: str) -> str:
    code = str(product_code or "").strip()
    for separator in ("-", "－", "_"):
        if separator in code:
            prefix = code.split(separator, 1)[0].strip()
            if len(prefix) >= 3 and prefix.lower() != code.lower():
                return prefix
    return ""


def _list_color_options(
    color_group: str,
    product_code: str = "",
    category_key: str = "",
    names: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if color_group:
        rows = _fetch_all(
            """
            SELECT id, slug, product_code, color_name, color_hex, main_image_url, stock
            FROM products
            WHERE is_active = TRUE AND color_group = %s
            ORDER BY id
            """,
            (color_group,),
        )

    # Backward compatibility: older edits could accidentally overwrite color_group
    # with each color variant's own product_code. In that case the query above
    # only returns itself, so recover sibling colors by the shared product-code
    # prefix such as CS2010-Black / CS2010-White.
    family_prefix = _product_code_family_prefix(product_code)
    if family_prefix and len(rows) <= 1:
        fallback_rows = _fetch_all(
            """
            SELECT id, slug, product_code, color_name, color_hex, main_image_url, stock
            FROM products
            WHERE is_active = TRUE
              AND (color_group = %s OR product_code = %s OR product_code ILIKE %s)
            ORDER BY id
            """,
            (family_prefix, family_prefix, f"{family_prefix}-%"),
        )
        if len(fallback_rows) > len(rows):
            rows = fallback_rows

    # Some products use plain codes such as ZM4757 for each color, so there is no
    # reliable code prefix to recover from. For those, use the product title
    # inside the same category as the grouping fallback. Different color variants
    # are created with the same title and category but different color_name/images.
    name_values = list(
        dict.fromkeys(
            str(value or "").strip()
            for value in (names or {}).values()
            if str(value or "").strip()
        )
    )
    if category_key and name_values and len(rows) <= 1:
        title_rows = _fetch_all(
            """
            SELECT DISTINCT p.id, p.slug, p.product_code, p.color_name, p.color_hex, p.main_image_url, p.stock
            FROM products p
            JOIN product_categories pc ON pc.id = p.category_id
            JOIN product_translations pt ON pt.product_id = p.id
            WHERE p.is_active = TRUE
              AND pc.category_key = %s
              AND pt.name = ANY(%s)
            ORDER BY p.id
            """,
            (category_key, name_values),
        )
        if len(title_rows) > len(rows):
            rows = title_rows

    return _format_color_options(rows)


def _attach_color_options(product: dict[str, Any] | None) -> dict[str, Any] | None:
    if not product:
        return None
    product["colorOptions"] = _list_color_options(
        product.get("colorGroup", ""),
        product.get("productCode", ""),
        product.get("categoryKey", ""),
        product.get("name") or {},
    )
    return product



def list_products() -> list[dict[str, Any]]:
    rows = _fetch_all(
        _product_base_query() + """
        WHERE p.is_active = TRUE
        ORDER BY p.id
        """,
        (DEFAULT_LANG,),
    )
    return _build_product_result(rows)


def get_product_by_slug(slug: str) -> dict[str, Any] | None:
    rows = _fetch_all(
        _product_base_query() + """
        WHERE p.slug = %s AND p.is_active = TRUE
        """,
        (DEFAULT_LANG, slug),
    )
    items = _build_product_result(rows)
    return _attach_color_options(items[0] if items else None)


def count_products() -> int:
    row = _fetch_one("SELECT COUNT(*) AS total FROM products WHERE is_active = TRUE")
    return int(row["total"]) if row else 0


def count_units_in_stock() -> int:
    row = _fetch_one("SELECT COALESCE(SUM(stock), 0) AS total FROM products WHERE is_active = TRUE")
    return int(row["total"]) if row else 0

def _build_banner_result(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    banner_ids = [int(row["id"]) for row in rows]
    translation_rows = _fetch_all(
        """
        SELECT banner_id, lang_code, title, subtitle, cta_label
        FROM banner_translations
        WHERE banner_id = ANY(%s)
        ORDER BY banner_id, lang_code
        """,
        (banner_ids,),
    )
    titles = {banner_id: _empty_bundle() for banner_id in banner_ids}
    subtitles = {banner_id: _empty_bundle() for banner_id in banner_ids}
    cta_labels = {banner_id: _empty_bundle() for banner_id in banner_ids}
    for row in translation_rows:
        banner_id = int(row["banner_id"])
        lang = row["lang_code"]
        titles[banner_id][lang] = row["title"] or ""
        subtitles[banner_id][lang] = row["subtitle"] or ""
        cta_labels[banner_id][lang] = row["cta_label"] or ""
    return [
        {
            "id": int(row["id"]),
            "image": row["image_url"],
            "ctaPath": row["cta_path"],
            "title": titles[int(row["id"])],
            "subtitle": subtitles[int(row["id"])],
            "ctaLabel": cta_labels[int(row["id"])],
        }
        for row in rows
    ]


def list_banners() -> list[dict[str, Any]]:
    rows = _fetch_all(
        """
        SELECT id, image_url, cta_path
        FROM banners
        WHERE is_active = TRUE
        ORDER BY sort_order, id
        """
    )
    return _build_banner_result(rows)


def _parse_json_text(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _normalize_home_banner_ids(value: Any) -> dict[str, int]:
    result = {key: 0 for key in HOME_SECTION_KEYS}
    if not isinstance(value, dict):
        return result
    for key in HOME_SECTION_KEYS:
        raw = value.get(key)
        try:
            banner_id = int(raw)
        except (TypeError, ValueError):
            banner_id = 0
        result[key] = banner_id if banner_id > 0 else 0
    return result


def _normalize_home_banner_images(value: Any) -> dict[str, str]:
    result = {key: "" for key in HOME_SECTION_KEYS}
    if not isinstance(value, dict):
        return result
    for key in HOME_SECTION_KEYS:
        result[key] = str(value.get(key, "") or "").strip()
    return result


def _normalize_section_product_map(value: Any, *, limit: int | None = None) -> dict[str, list[int]]:
    result = {key: [] for key in HOME_SECTION_KEYS}
    if not isinstance(value, dict):
        return result
    for key in HOME_SECTION_KEYS:
        rows = value.get(key)
        if not isinstance(rows, list):
            continue
        normalized: list[int] = []
        seen: set[int] = set()
        for item in rows:
            try:
                product_id = int(item)
            except (TypeError, ValueError):
                continue
            if product_id < 1 or product_id in seen:
                continue
            seen.add(product_id)
            normalized.append(product_id)
        result[key] = normalized[:limit] if limit is not None else normalized
    return result


def _normalize_home_section_products(value: Any) -> dict[str, list[int]]:
    return _normalize_section_product_map(value, limit=5)


def _normalize_collection_section_products(value: Any) -> dict[str, list[int]]:
    return _normalize_section_product_map(value, limit=None)


def _normalize_home_category_keys(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        key = str(item or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(key)
    return normalized[:5]


def _default_homepage_config() -> dict[str, Any]:
    banners = list_banners()
    return {
        "heroBanners": {
            "bestSeller": str(banners[0]["image"]) if len(banners) > 0 else "",
            "newArrival": str(banners[1]["image"]) if len(banners) > 1 else "",
            "specialPrice": str(banners[2]["image"]) if len(banners) > 2 else "",
        },
        "sectionProductIds": {
            "bestSeller": [],
            "newArrival": [],
            "specialPrice": [],
        },
        "collectionProductIds": {
            "bestSeller": [],
            "newArrival": [],
            "specialPrice": [],
        },
        "displayCategoryKeys": [],
    }


def get_homepage_config() -> dict[str, Any]:
    row = _fetch_one(
        """
        SELECT hero_banner_ids, hero_banner_images, section_product_ids, collection_product_ids, display_category_keys
        FROM homepage_configs
        WHERE id = 1
        """
    )
    defaults = _default_homepage_config()
    if not row:
        return defaults

    hero_banners = _normalize_home_banner_images(
        _parse_json_text(row.get("hero_banner_images"), defaults["heroBanners"])
    )
    legacy_banner_images = {}
    banner_map = {int(item["id"]): item for item in list_banners()}
    for key, banner_id in _normalize_home_banner_ids(_parse_json_text(row.get("hero_banner_ids"), {})).items():
        banner = banner_map.get(banner_id)
        legacy_banner_images[key] = str(banner["image"]) if banner else ""
    section_product_ids = _normalize_home_section_products(
        _parse_json_text(row.get("section_product_ids"), defaults["sectionProductIds"])
    )
    collection_product_ids = _normalize_collection_section_products(
        _parse_json_text(row.get("collection_product_ids"), defaults["collectionProductIds"])
    )
    display_category_keys = _normalize_home_category_keys(
        _parse_json_text(row.get("display_category_keys"), defaults["displayCategoryKeys"])
    )

    for key in HOME_SECTION_KEYS:
        if not hero_banners[key]:
            hero_banners[key] = legacy_banner_images.get(key) or defaults["heroBanners"][key]

    return {
        "heroBanners": hero_banners,
        "sectionProductIds": section_product_ids,
        "collectionProductIds": collection_product_ids,
        "displayCategoryKeys": display_category_keys,
    }


def list_category_labels(lang: str) -> list[dict[str, str]]:
    rows = _fetch_all(
        """
        SELECT pc.category_key, pct.label, pc.image_url
        FROM product_categories pc
        JOIN product_category_translations pct
          ON pct.category_id = pc.id AND pct.lang_code = %s
        WHERE pc.is_active = TRUE
        ORDER BY pc.sort_order, pc.id
        """,
        (lang,),
    )
    return [{"key": row["category_key"], "label": row["label"], "imageUrl": row.get("image_url") or ""} for row in rows]


def _build_store_user(row: dict[str, Any], *, include_password_hash: bool) -> dict[str, Any]:
    item = {
        "id": int(row["id"]),
        "name": row["name"],
        "companyName": row["company_name"] or "",
        "email": row["email"],
        "status": row["status"],
        "createdAt": _iso(row["created_at"]),
    }
    if include_password_hash:
        item["passwordHash"] = row["password_hash"]
    return item


def get_store_user_by_id(user_id: int, *, include_password_hash: bool = True) -> dict[str, Any] | None:
    row = _fetch_one(
        "SELECT id, name, company_name, email, password_hash, status, created_at FROM store_users WHERE id = %s",
        (user_id,),
    )
    return _build_store_user(row, include_password_hash=include_password_hash) if row else None


def get_store_user_by_email(email: str, *, include_password_hash: bool = True) -> dict[str, Any] | None:
    row = _fetch_one(
        "SELECT id, name, company_name, email, password_hash, status, created_at FROM store_users WHERE LOWER(email) = LOWER(%s)",
        (email,),
    )
    return _build_store_user(row, include_password_hash=include_password_hash) if row else None


def _compose_shipping_address(
    *,
    address: str,
    apartment: str,
    city: str,
    state: str,
    postal_code: str,
    country: str,
) -> str:
    return ", ".join(part for part in [address, apartment, city, state, postal_code, country] if part)


def _build_order_search_text(order: dict[str, Any]) -> str:
    parts = [
        order["orderNo"],
        order["contactName"],
        order.get("contactValue", ""),
        order.get("phone", ""),
        order.get("country", ""),
        order.get("shippingAddress", ""),
        order.get("note", ""),
    ]
    for item in order.get("items", []):
        parts.extend([item.get("productName", ""), item.get("sku", ""), item.get("sizeCode", "")])
    return " ".join(part for part in parts if part).lower()


def list_orders(*, user_id: int | None = None, keyword: str = "") -> list[dict[str, Any]]:
    query = """
        SELECT
          o.id,
          o.order_no,
          o.created_at,
          o.updated_at,
          o.status,
          o.store_user_id,
          su.name AS user_name,
          su.company_name,
          su.email AS user_email,
          o.contact_name,
          o.contact_email,
          o.phone,
          o.country,
          o.shipping_address,
          o.note,
          o.total_amount,
          o.marketing_opt_in,
          o.tracking_no,
          o.payment_link,
          o.shipping_fee,
          o.label_pdf_url,
          o.label_image_urls,
          o.shipped_at,
          o.completed_at,
          o.first_name,
          o.last_name,
          o.address_line1,
          o.apartment,
          o.city,
          o.state,
          o.postal_code,
          oi.id AS order_item_id,
          oi.product_id,
          oi.product_name,
          oi.sku,
          oi.size_code,
          oi.quantity,
          oi.unit_price,
          oi.total_price,
          p.main_image_url
        FROM orders o
        JOIN store_users su ON su.id = o.store_user_id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON p.id = oi.product_id
    """
    params: list[Any] = []
    if user_id is not None:
        query += " WHERE o.store_user_id = %s"
        params.append(user_id)
    query += " ORDER BY o.id DESC, oi.id ASC"
    rows = _fetch_all(query, tuple(params))

    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        order_id = int(row["id"])
        if order_id not in grouped:
            grouped[order_id] = {
                "id": order_id,
                "orderNo": row["order_no"],
                "createdAt": _iso(row["created_at"]),
                "updatedAt": _iso(row["updated_at"]),
                "status": row["status"],
                "userId": int(row["store_user_id"]),
                "userName": row["user_name"],
                "companyName": row["company_name"] or "",
                "userEmail": row["user_email"],
                "contactName": row["contact_name"],
                "contactValue": row.get("contact_email") or "",
                "phone": row["phone"],
                "country": row["country"] or "",
                "shippingAddress": row["shipping_address"],
                "note": row["note"] or "",
                "totalAmount": _num(row["total_amount"]),
                "marketingOptIn": bool(row.get("marketing_opt_in")),
                "trackingNo": row.get("tracking_no") or "",
                "paymentLink": row.get("payment_link") or "",
                "shippingFee": _num(row.get("shipping_fee") or 0),
                "labelPdfUrl": row.get("label_pdf_url") or "",
                "labelImageUrls": _parse_label_image_urls(row),
                "shippedAt": _iso(row["shipped_at"]) if row.get("shipped_at") else "",
                "completedAt": _iso(row["completed_at"]) if row.get("completed_at") else "",
                "firstName": row.get("first_name") or "",
                "lastName": row.get("last_name") or "",
                "address": row.get("address_line1") or "",
                "apartment": row.get("apartment") or "",
                "city": row.get("city") or "",
                "state": row.get("state") or "",
                "zip": row.get("postal_code") or "",
                "itemCount": 0,
                "canCancel": row["status"] in {"pending_payment", "paid"},
                "items": [],
            }

        if row["order_item_id"] is not None:
            quantity = int(row["quantity"])
            grouped[order_id]["itemCount"] += quantity
            grouped[order_id]["items"].append(
                {
                    "id": int(row["order_item_id"]),
                    "productId": int(row["product_id"]),
                    "productName": row["product_name"] or "",
                    "sku": row["sku"] or "",
                    "sizeCode": row["size_code"] or "",
                    "quantity": quantity,
                    "unitPrice": _num(row["unit_price"]),
                    "totalPrice": _num(row["total_price"]),
                    "image": row.get("main_image_url") or "",
                }
            )

    items = list(grouped.values())
    search = keyword.strip().lower()
    if search:
        items = [item for item in items if search in _build_order_search_text(item)]
    return items


def get_order_by_id(order_id: int, *, user_id: int | None = None) -> dict[str, Any] | None:
    items = list_orders(user_id=user_id)
    return next((item for item in items if item["id"] == order_id), None)


def create_order(payload: dict[str, Any]) -> dict[str, Any]:
    raw_items = payload.get("items") or []
    if not isinstance(raw_items, list) or not raw_items:
        raise RuntimeError("Order items are required")

    normalized_items: dict[tuple[int, str], dict[str, Any]] = {}
    for raw_item in raw_items:
        product_id = int(raw_item["productId"])
        quantity = int(raw_item["quantity"])
        if product_id <= 0:
            raise RuntimeError("Invalid productId")
        if quantity <= 0:
            raise RuntimeError("Quantity must be greater than 0")
        size_code = str(raw_item.get("sizeCode", "")).strip()
        key = (product_id, size_code)
        if key not in normalized_items:
            normalized_items[key] = {
                "productId": product_id,
                "sizeCode": size_code,
                "quantity": 0,
            }
        normalized_items[key]["quantity"] += quantity

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status
                FROM store_users
                WHERE id = %s
                """,
                (payload["userId"],),
            )
            user = cur.fetchone()
            if not user or user["status"] != "active":
                raise ValueError("Store user not found")

            prepared_items: list[dict[str, Any]] = []
            total_amount = Decimal("0")

            for item in normalized_items.values():
                product_id = item["productId"]
                quantity = item["quantity"]
                size_code = item["sizeCode"]

                cur.execute(
                    """
                    SELECT p.id, p.sku, p.price, p.stock, pt.name
                    FROM products p
                    JOIN product_translations pt
                      ON pt.product_id = p.id AND pt.lang_code = %s
                    WHERE p.id = %s AND p.is_active = TRUE
                    FOR UPDATE
                    """,
                    (DEFAULT_LANG, product_id),
                )
                product = cur.fetchone()
                if not product:
                    raise LookupError("Product not found")
                if quantity > int(product["stock"]):
                    raise RuntimeError("Insufficient stock")

                if size_code:
                    cur.execute(
                        """
                        SELECT price, stock
                        FROM product_size_prices
                        WHERE product_id = %s AND size_code = %s
                        FOR UPDATE
                        """,
                        (product_id, size_code),
                    )
                    size_row = cur.fetchone()
                    if not size_row:
                        raise LookupError("Size price not found")
                    if quantity > int(size_row["stock"]):
                        raise RuntimeError("Insufficient stock")
                    base_price = size_row["price"]
                else:
                    base_price = product["price"]

                unit_price = Decimal(str(base_price))
                line_total = unit_price * quantity
                total_amount += line_total

                prepared_items.append(
                    {
                        "productId": product_id,
                        "productName": product["name"],
                        "sku": product["sku"],
                        "sizeCode": size_code,
                        "quantity": quantity,
                        "unitPrice": unit_price,
                        "totalPrice": line_total,
                    }
                )

            for item in prepared_items:
                cur.execute(
                    "UPDATE products SET stock = stock - %s, updated_at = NOW() WHERE id = %s",
                    (item["quantity"], item["productId"]),
                )
                if item["sizeCode"]:
                    cur.execute(
                        """
                        UPDATE product_size_prices
                        SET stock = stock - %s
                        WHERE product_id = %s AND size_code = %s
                        """,
                        (item["quantity"], item["productId"], item["sizeCode"]),
                    )

            cur.execute(
                """
                INSERT INTO orders (
                  order_no, store_user_id, status, contact_name, contact_email, phone, country,
                  shipping_address, note, label_pdf_url, label_image_urls, total_amount, marketing_opt_in, first_name, last_name,
                  address_line1, apartment, city, state, postal_code, created_at, updated_at
                )
                VALUES (
                  %s, %s, 'pending_payment', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING id
                """,
                (
                    f"TEMP-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    payload["userId"],
                    payload["contactName"],
                    payload.get("contactValue", ""),
                    payload["phone"],
                    payload.get("country", ""),
                    payload["shippingAddress"],
                    payload.get("note", ""),
                    payload.get("labelPdfUrl", ""),
                    _serialize_label_image_urls(payload.get("labelImageUrls"), payload.get("labelPdfUrl", "")),
                    total_amount,
                    bool(payload.get("marketingOptIn")),
                    payload.get("firstName", ""),
                    payload.get("lastName", ""),
                    payload.get("address", ""),
                    payload.get("apartment", ""),
                    payload.get("city", ""),
                    payload.get("state", ""),
                    payload.get("zip", ""),
                ),
            )
            order_id = int(cur.fetchone()["id"])
            cur.execute("UPDATE orders SET order_no = %s WHERE id = %s", (f"LM-{order_id:06d}", order_id))

            for item in prepared_items:
                cur.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, product_name, sku, size_code, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["productId"],
                        item["productName"],
                        item["sku"],
                        item["sizeCode"],
                        item["quantity"],
                        item["unitPrice"],
                        item["totalPrice"],
                    ),
                )
        conn.commit()
    return get_order_by_id(order_id, user_id=int(payload["userId"]))  # type: ignore[return-value]


def cancel_order(order_id: int, *, user_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status
                FROM orders
                WHERE id = %s AND store_user_id = %s
                FOR UPDATE
                """,
                (order_id, user_id),
            )
            order = cur.fetchone()
            if not order:
                raise LookupError("Order not found")

            if order["status"] == "cancelled":
                return get_order_by_id(order_id, user_id=user_id)  # type: ignore[return-value]
            if order["status"] not in {"pending_payment", "paid"}:
                raise RuntimeError("Only pending payment or paid orders can be cancelled before shipment")

            cur.execute(
                """
                SELECT product_id, size_code, quantity
                FROM order_items
                WHERE order_id = %s
                ORDER BY id
                """,
                (order_id,),
            )
            item_rows = cur.fetchall()
            for item in item_rows:
                quantity = int(item["quantity"])
                product_id = int(item["product_id"])
                size_code = item["size_code"] or ""
                cur.execute(
                    "UPDATE products SET stock = stock + %s, updated_at = NOW() WHERE id = %s",
                    (quantity, product_id),
                )
                if size_code:
                    cur.execute(
                        """
                        UPDATE product_size_prices
                        SET stock = stock + %s
                        WHERE product_id = %s AND size_code = %s
                        """,
                        (quantity, product_id, size_code),
                    )

            cur.execute(
                "UPDATE orders SET status = 'cancelled', updated_at = NOW() WHERE id = %s",
                (order_id,),
            )
        conn.commit()
    return get_order_by_id(order_id, user_id=user_id)  # type: ignore[return-value]




