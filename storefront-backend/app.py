from __future__ import annotations

import json
from io import BytesIO
import mimetypes
import re
import secrets
import sys
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

BASE_DIR = Path(__file__).resolve().parent
LOCAL_VENDOR_DIR = BASE_DIR / "_vendor"
if LOCAL_VENDOR_DIR.exists():
    sys.path.insert(0, str(LOCAL_VENDOR_DIR))


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
        if key and key not in __import__("os").environ:
            __import__("os").environ[key] = value


load_env_file(BASE_DIR / ".env")

from flask import Flask, g, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash
try:
    import boto3
except Exception:  # noqa: BLE001
    boto3 = None

from db import (
    cancel_order,
    count_products,
    count_units_in_stock,
    create_order,
    get_homepage_config,
    get_product_by_slug,
    get_store_user_by_email,
    get_store_user_by_id,
    ensure_database_ready,
    list_category_labels,
    list_orders,
    list_products,
    verify_database_connection,
)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = Flask(__name__)
CORS(app)

F = TypeVar("F", bound=Callable[..., Any])
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_PUBLIC_BASE_URL = __import__("os").environ.get("UPLOAD_PUBLIC_BASE_URL", "").strip().rstrip("/")
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
SESSIONS_FILE = DATA_DIR / "sessions.json"
SUPPORTED_LANGS = {"zh", "en"}
DEFAULT_LANG = "en"
HOME_SECTION_KEYS = ("bestSeller", "newArrival", "specialPrice")
R2_ACCOUNT_ID = __import__("os").environ.get("R2_ACCOUNT_ID", "").strip()
R2_ACCESS_KEY_ID = __import__("os").environ.get("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY = __import__("os").environ.get("R2_SECRET_ACCESS_KEY", "").strip()
R2_BUCKET = __import__("os").environ.get("R2_BUCKET", "").strip()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_FILE.exists():
        write_json(SESSIONS_FILE, [])


def frontend_ready() -> bool:
    return (FRONTEND_DIST / "index.html").exists()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_upload_url(filename: str) -> str:
    if UPLOAD_PUBLIC_BASE_URL:
        return f"{UPLOAD_PUBLIC_BASE_URL}/{filename}"
    return f"{request.url_root.rstrip('/')}/uploads/{filename}"


def r2_enabled() -> bool:
    return bool(
        boto3
        and R2_ACCOUNT_ID
        and R2_ACCESS_KEY_ID
        and R2_SECRET_ACCESS_KEY
        and R2_BUCKET
    )


def upload_file_to_r2(file_storage: Any) -> str:
    if not r2_enabled():
        raise RuntimeError("R2 is not configured")

    file_name = str(file_storage.filename or "").strip() or f"upload-{secrets.token_hex(4)}.jpg"
    suffix = Path(file_name).suffix.lower() or ".jpg"
    content_type = file_storage.mimetype or mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    file_bytes = file_storage.read()
    file_storage.stream.seek(0)
    if not file_bytes:
        raise ValueError("Empty file")

    key = f"storefront/{datetime.now(UTC):%Y/%m/%d}/{secrets.token_hex(12)}{suffix}"
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    client.put_object(Bucket=R2_BUCKET, Key=key, Body=file_bytes, ContentType=content_type)
    return build_upload_url(key)


def pick_language() -> str:
    lang = request.args.get("lang", request.headers.get("X-Lang", DEFAULT_LANG))
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def localize(value: Any, lang: str) -> Any:
    if isinstance(value, dict) and SUPPORTED_LANGS & set(value.keys()):
        return value.get(lang) or value.get(DEFAULT_LANG) or next(iter(value.values()))
    if isinstance(value, list):
        return [localize(item, lang) for item in value]
    if isinstance(value, dict):
        return {key: localize(item, lang) for key, item in value.items()}
    return value


def sanitize_store_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "companyName": user.get("companyName", ""),
        "email": user["email"],
        "status": user["status"],
        "createdAt": user["createdAt"],
    }


def serialize_product(product: dict[str, Any], lang: str) -> dict[str, Any]:
    category_label = product.get("categoryLabel") or product.get("categoryKey", "")
    name = localize(product["name"], lang)
    summary = localize(product["summary"], lang)
    return {
        "id": product["id"],
        "slug": product["slug"],
        "sku": product["sku"],
        "productCode": product.get("productCode", ""),
        "colorGroup": product.get("colorGroup", ""),
        "colorName": product.get("colorName", ""),
        "colorHex": product.get("colorHex", ""),
        "categoryKey": product["categoryKey"],
        "categoryLabel": category_label,
        "price": product["price"],
        "formattedPrice": f"${product['price']}",
        "stock": product["stock"],
        "featured": bool(product.get("featured")),
        "origin": product.get("origin", ""),
        "sizes": product.get("sizes", []),
        "sizePrices": product.get("sizePrices", []),
        "image": product["image"],
        "gallery": product.get("gallery", []),
        "sizeChartImage": product.get("sizeChartImage", ""),
        "descriptionImage": product.get("descriptionImage", ""),
        "colorOptions": product.get("colorOptions", []),
        "name": name,
        "summary": summary,
        "description": localize(product["description"], lang),
        "searchText": " ".join([name, summary, category_label, product["sku"], product.get("productCode", ""), product.get("colorName", "")]).lower(),
    }

def serialize_banner(banner: dict[str, Any], lang: str) -> dict[str, Any]:
    return {
        "id": banner["id"],
        "image": banner["image"],
        "ctaPath": banner.get("ctaPath", "/shop"),
        "title": localize(banner["title"], lang),
        "subtitle": localize(banner["subtitle"], lang),
        "ctaLabel": localize(banner["ctaLabel"], lang),
    }


def build_homepage_payload(lang: str) -> dict[str, Any]:
    config = get_homepage_config()
    products = list_products()
    product_map = {int(item["id"]): item for item in products}
    category_items = list_category_labels(lang)
    category_map = {item["key"]: item["label"] for item in category_items}
    all_categories = [
        {"key": item["key"], "label": item["label"], "imageUrl": item.get("imageUrl", "")}
        for item in category_items
    ]

    selected_banners = []
    for key in HOME_SECTION_KEYS:
        image_url = str(config["heroBanners"].get(key, "") or "").strip()
        if not image_url:
            continue
        selected_banners.append(
            {
                "id": 0,
                "slotKey": key,
                "image": image_url,
                "ctaPath": "/shop",
                "title": "",
                "subtitle": "",
                "ctaLabel": "",
            }
        )

    sections = {}
    for key in HOME_SECTION_KEYS:
        section_items = []
        for product_id in config["sectionProductIds"].get(key, []):
            product = product_map.get(int(product_id))
            if product:
                section_items.append(serialize_product(product, lang))
        sections[key] = section_items

    categories = [
        {
            "key": key,
            "label": category_map[key],
            "imageUrl": next((item.get("imageUrl", "") for item in category_items if item["key"] == key), ""),
        }
        for key in config["displayCategoryKeys"]
        if key in category_map
    ]

    stats = [
        {"label": {"zh": "在线 SKU", "en": "Live SKUs"}[lang], "value": str(count_products())},
        {
            "label": {"zh": "现货库存", "en": "Units in stock"}[lang],
            "value": str(count_units_in_stock()),
        },
    ]

    return {
        "banners": selected_banners,
        "sections": sections,
        # categories: homepage category strip, controlled by Home Config displayCategoryKeys.
        # allCategories: full active admin category list, used by the SHOP dropdown menu.
        "categories": categories,
        "allCategories": all_categories,
        "stats": stats,
        "featured": sections.get("bestSeller", []),
    }


def parse_section_slug(section_slug: str) -> str:
    return {
        "best-seller": "bestSeller",
        "new-arrival": "newArrival",
        "special-price": "specialPrice",
    }.get(str(section_slug or "").strip().lower(), "")


def build_collection_payload(section_slug: str, lang: str) -> dict[str, Any] | None:
    section_key = parse_section_slug(section_slug)
    if not section_key:
        return None

    config = get_homepage_config()
    products = list_products()
    product_map = {int(item["id"]): item for item in products}

    items = []
    for product_id in config.get("collectionProductIds", {}).get(section_key, []):
        product = product_map.get(int(product_id))
        if product:
            items.append(serialize_product(product, lang))

    return {
        "sectionKey": section_key,
        "sectionSlug": section_slug,
        "items": items,
    }


def load_sessions() -> list[dict[str, Any]]:
    return read_json(SESSIONS_FILE)


def save_sessions(items: list[dict[str, Any]]) -> None:
    write_json(SESSIONS_FILE, items)


def next_id(items: list[dict[str, Any]]) -> int:
    return max((item["id"] for item in items), default=0) + 1


def extract_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "", 1).strip()
    return ""


def create_session(user: dict[str, Any]) -> str:
    sessions = [item for item in load_sessions() if item["userId"] != user["id"]]
    token = secrets.token_urlsafe(24)
    sessions.append(
        {
            "id": next_id(sessions),
            "userId": user["id"],
            "token": token,
            "createdAt": utc_now(),
        }
    )
    save_sessions(sessions)
    return token


def remove_session(token: str) -> None:
    save_sessions([item for item in load_sessions() if item["token"] != token])


def require_auth(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = extract_token()
        session = next((item for item in load_sessions() if item["token"] == token), None)
        if not session:
            return jsonify({"message": "Unauthorized"}), 401
        user = get_store_user_by_id(int(session["userId"]), include_password_hash=False)
        if not user or user["status"] != "active":
            return jsonify({"message": "Unauthorized"}), 401
        g.current_user = user
        g.current_token = token
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@app.get("/api/health")
def health() -> Any:
    try:
        verify_database_connection()
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc), "timestamp": utc_now()}), 500
    return jsonify({"status": "ok", "timestamp": utc_now()})


@app.get("/api/home")
def home() -> Any:
    lang = pick_language()
    return jsonify(build_homepage_payload(lang))


@app.post("/api/auth/store/login")
def store_login() -> Any:
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", "")).strip()
    user = get_store_user_by_email(email, include_password_hash=True)
    password_ok = user is not None and check_password_hash(user["passwordHash"], password)
    if not user or user["status"] != "active" or not password_ok:
        return jsonify({"message": "账号或密码错误"}), 401
    token = create_session(user)
    return jsonify({"token": token, "user": sanitize_store_user(user)})


@app.get("/api/auth/me")
@require_auth
def auth_me() -> Any:
    return jsonify({"role": "store", "user": sanitize_store_user(g.current_user)})


@app.post("/api/auth/logout")
@require_auth
def logout() -> Any:
    remove_session(g.current_token)
    return jsonify({"message": "ok"})


@app.get("/api/products")
@require_auth
def products() -> Any:
    lang = pick_language()
    category = request.args.get("category", "").strip().lower()
    keyword = request.args.get("keyword", "").strip().lower()
    items = [serialize_product(item, lang) for item in list_products()]
    if category:
        items = [item for item in items if item["categoryKey"] == category]
    if keyword:
        items = [item for item in items if keyword in item["searchText"]]
    return jsonify({"items": items, "total": len(items)})


@app.get("/api/products/<slug>")
@require_auth
def product_detail(slug: str) -> Any:
    lang = pick_language()
    product = get_product_by_slug(slug)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    related = [
        serialize_product(item, lang)
        for item in list_products()
        if item["categoryKey"] == product["categoryKey"] and item["id"] != product["id"]
    ][:3]
    return jsonify({"product": serialize_product(product, lang), "related": related})


@app.get("/api/collections/<section_slug>")
@require_auth
def collection_products(section_slug: str) -> Any:
    lang = pick_language()
    payload = build_collection_payload(section_slug, lang)
    if not payload:
        return jsonify({"message": "Collection not found"}), 404
    return jsonify(payload)


@app.get("/uploads/<path:filename>")
def serve_upload(filename: str) -> Any:
    local_file = UPLOAD_DIR / filename
    if local_file.exists() and local_file.is_file():
        return send_from_directory(UPLOAD_DIR, filename)
    if r2_enabled():
        client = boto3.client(
            "s3",
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        try:
            obj = client.get_object(Bucket=R2_BUCKET, Key=filename)
        except Exception:  # noqa: BLE001
            return jsonify({"message": "Not found"}), 404
        content = obj["Body"].read()
        content_type = obj.get("ContentType") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return send_file(BytesIO(content), mimetype=content_type, download_name=Path(filename).name)
    return jsonify({"message": "Not found"}), 404


ALLOWED_ORDER_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
ALLOWED_ORDER_ATTACHMENT_MIMES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_ORDER_ATTACHMENT_SIZE = 10 * 1024 * 1024


@app.post("/api/order-attachments")
@require_auth
def upload_order_attachment() -> Any:
    uploaded_files = request.files.getlist("files") or request.files.getlist("file")
    uploaded_files = [item for item in uploaded_files if item and str(item.filename or "").strip()]
    if not uploaded_files:
        return jsonify({"message": "Missing attachment"}), 400
    if len(uploaded_files) > 5:
        return jsonify({"message": "You can upload up to 5 attachments"}), 400

    items = []
    uploader = upload_file_to_r2 if r2_enabled() else None
    for file in uploaded_files:
        filename = str(file.filename or "").strip()
        suffix = Path(filename).suffix.lower()
        mimetype = str(getattr(file, "mimetype", "") or "").lower()
        if suffix not in ALLOWED_ORDER_ATTACHMENT_EXTENSIONS or mimetype not in ALLOWED_ORDER_ATTACHMENT_MIMES:
            return jsonify({"message": "Only PDF, JPG, PNG, or WebP files are allowed"}), 400
        file.stream.seek(0, 2)
        size = file.stream.tell()
        file.stream.seek(0)
        if size > MAX_ORDER_ATTACHMENT_SIZE:
            return jsonify({"message": "Each attachment must be 10MB or smaller"}), 400
        if uploader:
            url = uploader(file)
        else:
            safe_name = f"{secrets.token_hex(8)}_{Path(filename).name}"
            target = UPLOAD_DIR / safe_name
            file.save(target)
            url = build_upload_url(safe_name)
        items.append({"url": url, "filename": filename})

    if len(items) == 1:
        return jsonify({**items[0], "items": items})
    return jsonify({"items": items, "urls": [item["url"] for item in items]})


@app.post("/api/orders")
@require_auth
def create_order_route() -> Any:
    payload = request.get_json(silent=True) or {}
    contact = payload.get("contact") or {}
    delivery = payload.get("delivery") or {}
    items = payload.get("items") or []

    contact_value = str(contact.get("value", "")).strip()
    country = str(delivery.get("country", "")).strip()
    first_name = str(delivery.get("firstName", "")).strip()
    last_name = str(delivery.get("lastName", "")).strip()
    address = str(delivery.get("address", "")).strip()
    apartment = str(delivery.get("apartment", "")).strip()
    city = str(delivery.get("city", "")).strip()
    state = str(delivery.get("state", "")).strip()
    zip_code = str(delivery.get("zip", "")).strip()
    phone = str(delivery.get("phone", "")).strip()
    contact_name = " ".join(part for part in [first_name, last_name] if part).strip() or last_name

    required = {
        "delivery.country": country,
        "delivery.lastName": last_name,
        "delivery.address": address,
        "delivery.city": city,
        "delivery.state": state,
        "delivery.zip": zip_code,
    }
    missing = [field for field, value in required.items() if not value]
    if not contact_value and not phone:
        missing.append("contact.value or delivery.phone")
    if not isinstance(items, list) or not items:
        missing.append("items")
    if missing:
        return jsonify({"message": f"Missing field: {', '.join(missing)}"}), 400
    if contact_value and not (EMAIL_RE.match(contact_value) or phone == contact_value or re.match(r"^[0-9+\-\s()]{6,}$", contact_value)):
        return jsonify({"message": "Invalid field: contact.value"}), 400
    if phone and not re.match(r"^[0-9+\-\s()]{6,}$", phone):
        return jsonify({"message": "Invalid field: delivery.phone"}), 400

    try:
        order = create_order(
            {
                "userId": int(g.current_user["id"]),
                "items": items,
                "contactName": contact_name,
                "contactValue": contact_value,
                "marketingOptIn": bool(contact.get("marketingOptIn")),
                "firstName": first_name,
                "lastName": last_name,
                "phone": phone,
                "country": country,
                "address": address,
                "apartment": apartment,
                "city": city,
                "state": state,
                "zip": zip_code,
                "shippingAddress": ", ".join(part for part in [address, apartment, city, state, zip_code, country] if part),
                "note": str(payload.get("note", "")).strip(),
                "labelImageUrls": payload.get("labelImageUrls") or payload.get("labelImageUrl") or [],
                "labelPdfUrl": str(payload.get("labelPdfUrl", "")).strip(),
            }
        )
    except (TypeError, ValueError, KeyError):
        return jsonify({"message": "Invalid order payload"}), 400
    except LookupError as exc:
        return jsonify({"message": str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({"message": str(exc)}), 400
    return jsonify({"message": "Order submitted successfully", "order": order}), 201


@app.get("/api/store/orders")
@require_auth
def store_orders() -> Any:
    keyword = request.args.get("q", "").strip()
    return jsonify({"items": list_orders(user_id=int(g.current_user["id"]), keyword=keyword)})


@app.post("/api/store/orders/<int:order_id>/cancel")
@require_auth
def cancel_store_order(order_id: int) -> Any:
    try:
        order = cancel_order(order_id, user_id=int(g.current_user["id"]))
    except LookupError as exc:
        return jsonify({"message": str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({"message": str(exc)}), 400
    return jsonify({"message": "Order cancelled successfully", "order": order})


@app.get("/")
def serve_index() -> Any:
    if frontend_ready():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"message": "Storefront frontend build not found"}), 404


@app.get("/assets/<path:filename>")
def serve_assets(filename: str) -> Any:
    if frontend_ready():
        assets_dir = FRONTEND_DIST / "assets"
        file_path = assets_dir / filename
        if file_path.exists():
            return send_from_directory(assets_dir, filename)
    return jsonify({"message": "Not found"}), 404


@app.get("/<path:path>")
def serve_spa(path: str) -> Any:
    if path.startswith("api/") or path.startswith("uploads/"):
        return jsonify({"message": "Not found"}), 404
    if frontend_ready():
        target = FRONTEND_DIST / path
        if target.exists() and target.is_file():
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"message": "Storefront frontend build not found"}), 404


ensure_database_ready()
ensure_storage()
verify_database_connection()


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5301)
