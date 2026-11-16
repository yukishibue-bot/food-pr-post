#!/usr/bin/env python3
"""食PRポスト 静的サイト生成スクリプト（Python標準ライブラリのみ、依存なし）

使い方: python3 src/build.py
入力:   data/content.json（サイト情報・企業・カテゴリ・地域・リリース）
出力:   dist/ 以下に全ページ、sitemap.xml、robots.txt、llms.txt、feed.xml、assets/style.css

日次自律ループの一部として設計:
- リリースが追加されれば、詳細/企業/業種/地域/キーワードページとsitemapが自動で再生成される
- 日次ダイジェスト（その日の新着まとめ）を自動生成する。投稿ゼロの日でも、
  既存データの再構成ダイジェスト（カテゴリ別まとめ／企業動向）を生成できる
  ※外部サイトの転載・複製はしない。生成はすべて自サイト内データの再構成のみ
"""
import json
import os
import re
import shutil
from datetime import date
from html import escape
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "content.json")
DIST = os.path.join(ROOT, "dist")

CSS = """
:root{--ink:#181a16;--muted:#5c6055;--accent:#f26545;--accent-dark:#cf4526;--green:#3d6212;--lime:#bee83e;--violet:#7b5bd6;--line:#e2e5d5;--bg:#f6f7ef;--card:#ffffff;--adbg:#eef0e0;--shadow:5px 5px 0 rgba(24,26,22,.07);--shadow-lg:8px 8px 0 rgba(24,26,22,.12)}
*{box-sizing:border-box}
body{margin:0;font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Noto Sans JP",system-ui,-apple-system,sans-serif;color:var(--ink);background:var(--bg);line-height:1.85;-webkit-font-smoothing:antialiased}
a{color:var(--green)}
.wrap{max-width:920px;margin:0 auto;padding:0 20px}
header.site{position:sticky;top:0;z-index:20;border-bottom:3px solid var(--ink);background:rgba(246,247,239,.96);backdrop-filter:blur(8px)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;padding:12px 20px;flex-wrap:wrap;gap:8px}
.logo{font-size:24px;font-weight:900;color:var(--ink);text-decoration:none;letter-spacing:.01em}
.logo small{display:block;font-size:11px;color:var(--muted);font-weight:400;letter-spacing:.04em}
nav.main a{margin-left:18px;font-size:14px;text-decoration:none;color:var(--ink);font-weight:600}
nav.main a:hover{color:var(--accent)}
nav.main a:last-child{background:var(--ink);color:var(--lime);padding:8px 18px;border-radius:999px;font-weight:900;box-shadow:3px 3px 0 rgba(24,26,22,.35)}
nav.main a:last-child:hover{background:var(--accent);color:#fff}
.hero{text-align:left;padding:56px 28px 0;background:var(--lime);border:3px solid var(--ink);border-radius:20px;margin-top:8px;overflow:hidden}
.kicker{font-weight:900;letter-spacing:.14em;font-size:13px;color:var(--ink);margin:14px 0 10px}
.hero-img{display:block;width:calc(100% + 56px);max-width:none;margin:26px -28px 0;height:auto}
.badge{display:inline-block;background:var(--ink);border:none;color:var(--lime);font-weight:900;font-size:13px;border-radius:999px;padding:6px 16px;margin-bottom:6px;letter-spacing:.06em}
.hero h1{font-size:52px;line-height:1.28;margin:0 0 16px;font-weight:900;letter-spacing:-.01em}
.hero p{color:#2c2e26;max-width:700px;margin:0 0 22px;font-weight:600}
.btn{display:inline-block;background:var(--accent);color:#fff;padding:13px 30px;border-radius:999px;text-decoration:none;font-weight:900;border:2px solid var(--ink);cursor:pointer;font-size:15px;box-shadow:4px 4px 0 var(--ink);transition:transform .15s ease,box-shadow .15s ease}
.btn:hover{transform:translate(-1px,-1px);box-shadow:5px 5px 0 var(--ink)}
.btn.sub{background:#fff;color:var(--ink);border:2px solid var(--ink);box-shadow:4px 4px 0 var(--ink)}
main{padding:28px 0 56px}
h2.sec{font-size:23px;font-weight:900;border-left:10px solid var(--lime);border-bottom:3px solid var(--ink);padding:0 0 8px 12px;margin:46px 0 18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:0 0 14px;box-shadow:var(--shadow);transition:transform .15s ease,box-shadow .15s ease}
.card:hover{transform:translateY(-2px);box-shadow:var(--shadow-lg)}
.card h3{margin:4px 0 6px;font-size:17px;line-height:1.6}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a:hover{color:var(--accent-dark)}
.meta{font-size:12px;color:var(--muted)}
.tag{display:inline-block;background:#eef3cf;color:var(--green);border-radius:999px;padding:2px 11px;font-size:12px;margin:2px 4px 2px 0;text-decoration:none;font-weight:700}
.tag:hover{background:var(--lime);color:var(--ink)}
.type-badge{display:inline-block;background:var(--lime);color:var(--ink);border:2px solid var(--ink);border-radius:999px;padding:1px 12px;font-size:12px;font-weight:900;margin:2px 6px 2px 0;text-decoration:none;letter-spacing:.03em}
.type-badge:hover{background:var(--accent);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.grid .card{margin:0}
.ad-slot{background:var(--adbg);border:1px solid var(--line);color:#8a846e;text-align:center;padding:24px 10px 14px;border-radius:12px;font-size:12px;margin:20px 0;min-height:120px;overflow:hidden;position:relative}
.ad-slot .ad-label{position:absolute;top:6px;left:8px;background:#fff;border:1px solid #c9c2ae;border-radius:4px;padding:0 6px;font-size:10px;line-height:1.6;color:#8a846e;letter-spacing:.08em}
.ad-slot.is-placeholder{border-style:dashed;border-color:#c9c2ae;display:flex;align-items:center;justify-content:center}
.ad-slot img,.ad-slot iframe,.ad-slot ins,.ad-slot object,.ad-slot embed{max-width:100%}
.ad-slot[data-ad-slot="infeed"]{min-height:110px}
.ad-slot[data-ad-slot="footer"]{min-height:110px;margin:28px 0 0}
article.release h1{font-size:28px;line-height:1.5;font-weight:900}
article.release .body p{margin:0 0 16px}
table.spec{border-collapse:collapse;width:100%;font-size:14px;background:#fff}
table.spec th,table.spec td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}
table.spec th{background:#faf5ec;width:32%}
footer.site{border-top:3px solid var(--ink);background:var(--ink);padding:32px 0;font-size:13px;color:#c9ccba}
footer.site a{color:#c9ccba;margin-right:14px}
form.netlify-form label{display:block;margin:14px 0 4px;font-weight:700;font-size:14px}
form.netlify-form input,form.netlify-form textarea,form.netlify-form select{width:100%;padding:10px;border:1px solid var(--line);border-radius:8px;font-size:15px;background:#fff}
.note{font-size:13px;color:var(--muted)}
ul.plain{padding-left:20px}
.pr-form label{display:block;margin:18px 0 6px;font-weight:700;font-size:14px}
.pr-form input[type="text"],.pr-form input[type="email"],.pr-form input[type="url"],.pr-form textarea,.pr-form select{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:10px;font-size:15px;background:#fff;font-family:inherit}
.pr-form textarea{line-height:1.7}
.pr-form .req{background:var(--accent);color:#fff;font-size:11px;border-radius:4px;padding:1px 7px;margin-left:4px;vertical-align:2px}
.pr-form .count{font-size:12px;margin:4px 0 0;text-align:right}
.pr-form .agree{font-weight:400;display:flex;gap:8px;align-items:flex-start;margin-top:20px;font-size:14px}
.pr-form .agree input{margin-top:6px}
.pr-form .btn{width:100%;margin-top:18px;font-size:16px;padding:15px}
.cta-band{text-align:center;background:var(--lime);border:3px solid var(--ink);border-radius:16px;padding:38px 20px;margin-top:46px;box-shadow:6px 6px 0 var(--ink)}
.cta-band h2{margin:0 0 8px;font-size:24px;font-weight:900}
.cta-band p{color:#2c2e26;font-weight:600}
.form-error{background:#fdeee7;border:1px solid var(--accent);color:var(--accent-dark);border-radius:10px;padding:10px 14px;font-size:14px}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi .card{flex:1;min-width:180px;text-align:center;padding:26px 18px}
.kpi b{font-size:26px;display:block;color:var(--accent-dark);margin-bottom:4px;font-weight:900}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.qa-list{display:grid;gap:12px}.qa{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}.qa-q{font-weight:700;margin:0 0 8px;color:var(--ink)}.qa-a{margin:0;color:var(--sub);line-height:1.8}
.step{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px;box-shadow:var(--shadow)}
.step .num{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:var(--lime);color:var(--ink);font-weight:900;margin-bottom:10px;border:2px solid var(--ink)}
.step h3{margin:0 0 6px;font-size:16px}
.step p{margin:0;font-size:14px;color:var(--muted)}
@media (max-width:640px){.hero{padding:36px 18px 0}.hero h1{font-size:33px}.hero-img{width:calc(100% + 36px);margin:20px -18px 0}nav.main a{margin-left:12px;font-size:13px}.btn{padding:12px 22px;font-size:14px}}
"""


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def rel_url(base, path):
    return base.rstrip("/") + path


def kw_slug(kw):
    return re.sub(r"[^0-9A-Za-zぁ-んァ-ヶー一-龠]+", "-", kw).strip("-").lower()


def page(site, path, title, description, body, jsonld=None, og_type="website", image=None):
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False) + "</script>"
    # 画像は絶対URL（http/https）の場合のみ og:image / twitter:image に使う。相対・未設定なら summary カードに落とす
    img = image if image and image.startswith(("http://", "https://")) else None
    og_image = f'\n<meta property="og:image" content="{img}">' if img else ""
    twitter_card = "summary_large_image" if img else "summary"
    twitter_image = f'\n<meta name="twitter:image" content="{img}">' if img else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | {escape(site['name'])}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{rel_url(site['base_url'], path)}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{rel_url(site['base_url'], path)}">{og_image}
<meta name="twitter:card" content="{twitter_card}">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(description)}">{twitter_image}
<link rel="stylesheet" href="/assets/style.css">
<link rel="alternate" type="application/rss+xml" title="{escape(site['name'])} 新着プレスリリース" href="/feed.xml">
{ld}
{ad_head_tags()}
</head>
<body>
<header class="site"><div class="wrap">
<a class="logo" href="/">{escape(site['name'])}<small>{escape(site['tagline'])}</small></a>
<nav class="main">
<a href="/releases/">プレスリリース</a><a href="/categories/">業種</a><a href="/areas/">地域</a><a href="/type/">発表タイプ</a><a href="/companies/">企業</a><a href="/digest/">日次まとめ</a><a href="/submit/">無料で投稿する</a>
</nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<div class="wrap">{ad_slot('footer')}</div>
<footer class="site"><div class="wrap">
<p><a href="/about/">運営者情報</a><a href="/review-policy/">審査基準</a><a href="/terms/">利用規約</a><a href="/privacy/">プライバシーポリシー</a><a href="/contact/">お問い合わせ</a></p>
<p>© 2026 {escape(site['operator'])}（{escape(site['name'])} 運営）</p>
</div></footer>
</body>
</html>
"""


# ---------- 広告枠（data/content.json の "ads" セクションで設定） ----------
# 枠の種類(kind): top（トップ）/ article-top / article-bottom（記事詳細の本文前・本文下）/
#   infeed（一覧のインフィード）/ footer（全ページ共通・フッター上部）
# 各ネットワークは enabled=true かつ tag が空でない場合のみ使われ、priority の若い順に
# 枠の種類（slots、省略時は全枠対象）が合う最初の1つが差し込まれる。
# 差し込める広告が無い枠はプレースホルダ表示のままになる。すべての枠に「PR」表記を付ける。
ADS = {"enabled": False, "infeed_interval": 4, "priority": [], "networks": {}}


def init_ads(data):
    global ADS
    cfg = data.get("ads") or {}
    ADS = {
        "enabled": bool(cfg.get("enabled", False)),
        "infeed_interval": int(cfg.get("infeed_interval") or 4),
        "priority": list(cfg.get("priority") or []),
        "networks": cfg.get("networks") or {},
    }


def active_network(kind):
    """枠 kind に差し込む広告ネットワークを priority 順に探す。なければ None。"""
    if not ADS["enabled"]:
        return None
    for key in ADS["priority"]:
        net = ADS["networks"].get(key) or {}
        if not net.get("enabled"):
            continue
        if not (net.get("tag") or "").strip():
            continue
        slots = net.get("slots")
        if slots is not None and kind not in slots:
            continue
        return key, net
    return None


def ad_slot(kind="infeed"):
    label = '<span class="ad-label">PR</span>'
    found = active_network(kind)
    if found:
        key, net = found
        return (
            f'<div class="ad-slot" data-ad-slot="{kind}" data-ad-network="{key}">'
            f"{label}{net['tag'].strip()}</div>"
        )
    return f'<div class="ad-slot is-placeholder" data-ad-slot="{kind}">{label}広告枠（準備中）</div>'


def ad_head_tags():
    """有効なネットワークの head_tag を <head> 用に集める（AdSense の adsbygoogle.js 読込など）。"""
    if not ADS["enabled"]:
        return ""
    tags = []
    for key in ADS["priority"]:
        net = ADS["networks"].get(key) or {}
        if net.get("enabled") and (net.get("head_tag") or "").strip():
            tags.append(net["head_tag"].strip())
    return "\n".join(tags)


def cards_with_ads(cards):
    """カードHTMLのリストに、infeed_interval 件ごとにインフィード広告枠を差し込む。

    件数が interval 以下の場合は末尾に1枠だけ置く（枠ゼロの一覧ページを作らないため）。
    """
    if not cards:
        return ""
    interval = ADS["infeed_interval"]
    if interval <= 0:
        return "".join(cards)
    out = []
    inserted = False
    for i, card in enumerate(cards, 1):
        out.append(card)
        if i % interval == 0 and i < len(cards):
            out.append(ad_slot("infeed"))
            inserted = True
    if not inserted:
        out.append(ad_slot("infeed"))
    return "".join(out)


def write(path, content):
    full = os.path.join(DIST, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def release_card(r, companies, categories):
    comp = companies[r["company"]]
    cats = " ".join(
        f'<a class="tag" href="/categories/{c}/">{escape(categories[c]["name"])}</a>' for c in r["categories"]
    )
    return f"""<div class="card">
<p class="meta">{escape(r['published_at'])} ｜ {escape(comp['name'])}</p>
<h3><a href="/releases/{r['slug']}/">{escape(r['title'])}</a></h3>
<p>{escape(r['summary'])}</p>
<p>{type_badge(r)}{cats}</p>
</div>"""


# 発表タイプ（slug -> 定義）。main() で content.json の "types" から読み込む
TYPES = {}


def type_badge(r):
    """リリースの発表タイプバッジ（/type/<slug>/ へのリンク）。未設定・不明なら空文字。"""
    t = TYPES.get(r.get("type") or "")
    if not t:
        return ""
    return f'<a class="type-badge" href="/type/{t["slug"]}/">{escape(t["name"])}</a>'


def build_digest(releases, companies, categories):
    """日次ダイジェスト生成。
    その日に公開されたリリースがあれば「新着まとめ」を作る。
    投稿ゼロの日は、既存データの再構成（カテゴリ別まとめ／企業動向）で代替する設計
    （実装は運用フェーズ。ここでは最新公開日のダイジェストをモックとして生成する）。
    """
    dates = sorted({r["published_at"] for r in releases}, reverse=True)
    if not dates:
        return None
    d = dates[0]
    todays = [r for r in releases if r["published_at"] == d]
    items = "".join(
        f'<li><a href="/releases/{r["slug"]}/">{escape(r["title"])}</a>（{escape(companies[r["company"]]["name"])}）</li>'
        for r in todays
    )
    cat_names = sorted({categories[c]["name"] for r in todays for c in r["categories"]})
    paras = [
        f"{d}に公開された食ビジネスのプレスリリースは{len(todays)}件です。",
        "業種別では「" + "」「".join(cat_names) + "」の発表がありました。",
        "本ダイジェストは、当サイトに掲載されたプレスリリースのみを再構成して自動生成しています。外部サイトの記事の転載は行っていません。",
    ]
    return {
        "date": d,
        "slug": d,
        "title": f"{d}の食ビジネス発表まとめ（{len(todays)}件）",
        "items_html": f"<ul class='plain'>{items}</ul>",
        "paras": paras,
        "count": len(todays),
    }


def main():
    data = load()
    init_ads(data)
    site = data["site"]
    companies = {c["slug"]: c for c in data["companies"]}
    categories = {c["slug"]: c for c in data["categories"]}
    areas = {a["slug"]: a for a in data["areas"]}
    types = {t["slug"]: t for t in data.get("types", [])}
    TYPES.update(types)
    releases = sorted(data["releases"], key=lambda r: r["published_at"], reverse=True)

    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    write("/assets/style.css", CSS)
    import base64
    hero_src = os.path.join(ROOT, "assets-src", "hero-fresh.webp")
    hero_uri = ""
    if os.path.exists(hero_src):
        hero_uri = "data:image/webp;base64," + base64.b64encode(open(hero_src, "rb").read()).decode()
    # Cloudflare Pages用ヘッダ（ホスティング非依存の補助ファイル。他ホスティングでは無視される）
    write("/_headers", "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n")

    urls = []

    def add(path, html, lastmod=None):
        write(path, html)
        urls.append((path, lastmod))

    org_ld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site["name"],
        "description": site["description"],
        "url": site["base_url"] + "/",
        "founder": {"@type": "Organization", "name": site["operator"]},
    }
    website_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site["name"],
        "url": site["base_url"] + "/",
        "inLanguage": "ja",
    }

    faq_html = """
<h2 class="sec">よくある質問</h2>
<div class="card"><h3>本当に無料ですか？入会費や年会費はかかりますか？</h3><p>完全無料です。掲載料・配信料・年会費は一切かかりません。運営費はサイト内の広告収益でまかなっています。</p></div>
<div class="card"><h3>会員登録は必要ですか？</h3><p>不要です。投稿フォームからそのまま送信できます。</p></div>
<div class="card"><h3>審査はどのように行われますか？</h3><p>すべての投稿にAI審査を行い、スパム・誇大表現・景表法・公序良俗・重複投稿をチェックします。通過したものから順次公開します。基準は<a href="/review-policy/">審査基準</a>で公開しています。</p></div>
<div class="card"><h3>公開までどれくらいかかりますか？</h3><p>投稿は朝・夕の2回、取り込み・審査します。通過したものは最短で当日中、遅くとも翌朝までに公開されます（状況により前後します）。</p></div>
<div class="card"><h3>誰でも投稿できますか？</h3><p>法人・個人事業主・団体など、どなたでも投稿できます。食に関わる事業の発表が主役ですが、他業種の投稿も受け付けています。</p></div>
"""

    # ---------- トップ ----------
    latest = cards_with_ads([release_card(r, companies, categories) for r in releases[:10]])
    if not latest:
        latest = """
<div class="card"><p class="note" style="text-align:center">新着リリースはまだありません。<a href="/submit/">最初の1件を無料で投稿する</a>（登録不要・完全無料。通過したものは朝・夕の公開タイミングで、最短当日中に掲載されます）</p></div>
<h3 style="margin:22px 0 10px">掲載イメージ（例）</h3>
<p class="note">掲載されると、このようなカードと専用ページで公開されます。以下は表示イメージを確認するための架空のサンプルで、実在の企業の発表ではありません。</p>
<div class="grid">
<div class="card"><p class="note">（例）飲食店・レストラン ｜ 東京都</p><h3>（サンプル）地元野菜のランチコースを開始</h3><p style="margin:0 0 6px"><a class="type-badge" href="/type/new-product/">新商品・新メニュー</a></p><p class="note">サンプル食堂（例）｜新店・新メニューの発表は、業種と地域、発表タイプのページにも自動で並びます。</p></div>
<div class="card"><p class="note">（例）食品・飲料メーカー ｜ 全国</p><h3>（サンプル）季節限定の新商品を発売</h3><p style="margin:0 0 6px"><a class="type-badge" href="/type/campaign/">キャンペーン</a></p><p class="note">サンプル食品（例）｜専用ページが作られ、検索エンジンとAI検索の対象になります。</p></div>
<div class="card"><p class="note">（例）フードイベント ｜ 大阪府</p><h3>（サンプル）週末マルシェの出店者を募集</h3><p style="margin:0 0 6px"><a class="type-badge" href="/type/event/">イベント</a></p><p class="note">サンプルイベント事務局（例）｜記事ページにはSNSシェアボタンが付きます。</p></div>
</div>
"""
    cat_cards = "".join(
        f'<div class="card"><h3><a href="/categories/{c["slug"]}/">{escape(c["name"])}</a></h3><p class="note">{escape(c["description"])}</p></div>'
        for c in data["categories"]
    )
    type_cards = "".join(
        f'<div class="card"><h3><a href="/type/{t["slug"]}/">{escape(t["name"])}</a></h3><p class="note">{escape(t["description"])}</p></div>'
        for t in data.get("types", [])
    )
    area_links = " ".join(f'<a class="tag" href="/areas/{a["slug"]}/">{escape(a["name"])}</a>' for a in data["areas"])
    body = f"""
<section class="hero">
<span class="badge">AI審査でスピード掲載</span>
<p class="kicker">GOOD FOOD. BIG NEWS.</p>
<h1>食の新しいニュースは、<br>ここから。</h1>
<p>{escape(site['description'])}</p>
<p><a class="btn" href="/submit/">無料でプレスリリースを投稿する</a> <a class="btn sub" href="/releases/">新着リリースを見る</a></p>
<p class="note">掲載料・配信料・年会費は一切かかりません。投稿回数は無制限です。すべての投稿に<strong>AI審査</strong>を行い、通過したものから順次公開します（<a href="/review-policy/">審査基準</a>）。</p>
<img class="hero-img" src="{hero_uri}" alt="色鮮やかな野菜と食材" width="1400" height="255">
</section>
<div class="kpi">
<div class="card"><b>¥0</b>掲載・配信・年会費</div>
<div class="card"><b>AI審査</b>スパム・誇大表現・法令を自動チェック</div>
<div class="card"><b>無制限</b>投稿回数</div>
</div>
<h2 class="sec">AI審査の流れ</h2>
<div class="steps">
<div class="step"><span class="num">1</span><h3>投稿する</h3><p>無料フォームから会社情報と発表内容を送るだけ。登録料・掲載料は一切かかりません。</p></div>
<div class="step"><span class="num">2</span><h3>AI審査</h3><p>AIがスパム・誇大表現・景表法・公序良俗・重複投稿を自動でチェックします。</p></div>
<div class="step"><span class="num">3</span><h3>掲載</h3><p>審査を通過したものから順次公開。検索エンジンとAI検索に届く形で掲載します。</p></div>
</div>
{ad_slot('top')}
<h2 class="sec">掲載後の広がり</h2>
<div class="steps">
<div class="step"><h3>専用ページで公開</h3><p>1件ごとに専用ページが作られ、検索エンジンとAI検索に届く形（構造化データ付き）で掲載されます。</p></div>
<div class="step"><h3>業種・地域・発表タイプのページにも掲載</h3><p>トップの新着に加えて、業種ページ・地域ページ・発表タイプのページにも自動で並ぶので、探している人の目に触れます。</p></div>
<div class="step"><h3>RSSで新着配信</h3><p>新着リリースはRSSフィードでも配信されます。あわせて日次ダイジェストにも収録されます。</p></div>
<div class="step"><h3>SNSで自社発信にも</h3><p>記事ページにはシェアボタン（X・LINE・Facebook）があります。自社のSNS発信のリンク先としても使えます。</p></div>
</div>
<h2 class="sec">新着プレスリリース</h2>
{latest}
<h2 class="sec">業種から探す（食が主軸です）</h2>
<div class="grid">{cat_cards}</div>
<h2 class="sec">発表タイプから探す</h2>
<div class="grid">{type_cards}</div>
<h2 class="sec">地域から探す</h2>
<p>{area_links}</p>
{faq_html}
<h2 class="sec">このサイトについて</h2>
<p>「{escape(site['name'])}」は、食に関わる事業者のための無料プレスリリース掲載サイトです。大手配信サービスでは1件数万円かかる発表を、予算のない中小企業・店舗・個人事業主でも出せるようにしました。投稿はすべてAI審査を行い、食ビジネスの現場に届く形で情報を発信します。他業種の投稿も受け付けますが、サイトの主役は食ビジネスです。</p>
<section class="cta-band">
<h2>あなたのお知らせを、食PRポストへ。</h2>
<p>登録不要・完全無料。AI審査を経て、最短当日で記事として公開されます。</p>
<p><a class="btn" href="/submit/">プレスリリースを投稿する →</a></p>
</section>
"""
    add("/index.html", page(site, "/", site["name"] + "｜" + site["tagline"], site["description"], body, [org_ld, website_ld]), releases[0]["published_at"] if releases else None)

    # ---------- リリース一覧 ----------
    items = cards_with_ads([release_card(r, companies, categories) for r in releases])
    if not items:
        items = '<div class="card"><p class="note" style="text-align:center">プレスリリースはまだありません。<a href="/submit/">最初の1件を無料で投稿する</a></p></div>' 
    list_ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": rel_url(site["base_url"], f"/releases/{r['slug']}/")}
            for i, r in enumerate(releases)
        ],
    }
    add("/releases/index.html", page(site, "/releases/", "プレスリリース一覧", "食ビジネスのプレスリリース一覧です。", f"<h1>プレスリリース一覧</h1>{items}", list_ld))

    # ---------- リリース詳細 ----------
    for r in releases:
        comp = companies[r["company"]]
        paras = "".join(f"<p>{escape(p)}</p>" for p in r["body"])
        cat_tags = " ".join(f'<a class="tag" href="/categories/{c}/">{escape(categories[c]["name"])}</a>' for c in r["categories"])
        area_tags = " ".join(f'<a class="tag" href="/areas/{a}/">{escape(areas[a]["name"])}</a>' for a in r["areas"])
        kw_tags = " ".join(f'<a class="tag" href="/keywords/{kw_slug(kw)}/">{escape(kw)}</a>' for kw in r["keywords"])
        ld = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": r["title"],
            "description": r["summary"],
            "datePublished": r["published_at"],
            "dateModified": r["published_at"],
            "inLanguage": "ja",
            "author": {"@type": "Organization", "name": comp["name"], "url": comp.get("website", site["base_url"])},
            "publisher": {"@type": "Organization", "name": site["name"], "url": site["base_url"] + "/"},
            "mainEntityOfPage": rel_url(site["base_url"], f"/releases/{r['slug']}/"),
            "keywords": r["keywords"],
        }
        if r.get("type") in types:
            ld["articleSection"] = types[r["type"]]["name"]
        qa_items = [x for x in (r.get("qa") or []) if x.get("q") and x.get("a")]
        qa_html = ""
        jsonld_out = ld
        if qa_items:
            qa_html = '<h2 class="sec">Q&A</h2><div class="qa-list">' + "".join(
                f'<div class="qa"><p class="qa-q">Q. {escape(x["q"])}</p><p class="qa-a">A. {escape(x["a"])}</p></div>' for x in qa_items
            ) + '</div>'
            faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in qa_items
            ]}
            jsonld_out = [ld, faq_ld]
        body = f"""
<article class="release">
<p class="meta">{escape(r['published_at'])} ｜ <a href="/companies/{comp['slug']}/">{escape(comp['name'])}</a></p>
<h1>{escape(r['title'])}</h1>
<p>{type_badge(r)} {cat_tags} {area_tags}</p>
{ad_slot('article-top')}
<div class="body">{paras}</div>
<p class="share" style="margin:20px 0">この発表をシェア：
<a href="https://twitter.com/intent/tweet?text={quote(r['title'])}&url={quote(site['base_url'] + '/releases/' + r['slug'] + '/')}" target="_blank" rel="noopener">Xでシェア</a> ｜
<a href="https://social-plugins.line.me/lineit/share?url={quote(site['base_url'] + '/releases/' + r['slug'] + '/')}" target="_blank" rel="noopener">LINEで送る</a> ｜
<a href="https://www.facebook.com/sharer/sharer.php?u={quote(site['base_url'] + '/releases/' + r['slug'] + '/')}" target="_blank" rel="noopener">Facebookでシェア</a></p>
{qa_html}
<p class="note">キーワード：{kw_tags}</p>
{ad_slot('article-bottom')}
<h2 class="sec">発表企業について</h2>
<div class="card"><h3><a href="/companies/{comp['slug']}/">{escape(comp['name'])}</a></h3><p>{escape(comp['description'])}</p></div>
<p class="note">※本ページは発表企業から投稿されたプレスリリースを、審査のうえ掲載したものです。内容の正確性は発表企業に帰属します。</p>
</article>
"""
        add(f"/releases/{r['slug']}/index.html", page(site, f"/releases/{r['slug']}/", r["title"], r["summary"], body, jsonld_out, "article"), r["published_at"])

    # ---------- 企業ページ ----------
    comp_cards = "".join(
        f'<div class="card"><h3><a href="/companies/{c["slug"]}/">{escape(c["name"])}</a></h3><p>{escape(c["description"])}</p></div>'
        for c in data["companies"]
    )
    add("/companies/index.html", page(site, "/companies/", "掲載企業一覧", "プレスリリースを掲載している企業の一覧です。", f"<h1>掲載企業一覧</h1>{comp_cards}"))
    for c in data["companies"]:
        own = [r for r in releases if r["company"] == c["slug"]]
        own_html = cards_with_ads([release_card(r, companies, categories) for r in own])
        facts = "".join(f"<li>{escape(x)}</li>" for x in c.get("facts", []))
        web = f'<p>公式サイト：<a href="{escape(c["website"])}" rel="nofollow noopener" target="_blank">{escape(c["website"])}</a></p>' if c.get("website") else ""
        ld = {"@context": "https://schema.org", "@type": "Organization", "name": c["name"], "description": c["description"], "url": c.get("website", "")}
        body = f"""<h1>{escape(c['name'])}</h1>
<p>{escape(c['description'])}</p>
{web}
<h2 class="sec">企業データ</h2><ul class="plain">{facts}</ul>
<h2 class="sec">この企業のプレスリリース（{len(own)}件）</h2>
{own_html if own_html else '<p class="note">まだプレスリリースがありません。</p>'}
"""
        add(f"/companies/{c['slug']}/index.html", page(site, f"/companies/{c['slug']}/", c["name"], c["description"], body, ld))

    # ---------- カテゴリ ----------
    add("/categories/index.html", page(site, "/categories/", "業種カテゴリ一覧", "食ビジネスを中心とした業種カテゴリ一覧です。", "<h1>業種カテゴリ一覧</h1><div class='grid'>" + cat_cards + "</div>"))
    for slug, c in categories.items():
        own = [r for r in releases if slug in r["categories"]]
        own_html = cards_with_ads([release_card(r, companies, categories) for r in own])
        body = f"""<h1>{escape(c['name'])}のプレスリリース</h1>
<p>{escape(c['description'])}</p>
{own_html if own_html else '<p class="note">このカテゴリのプレスリリースはまだありません。<a href="/submit/">最初の1件を無料で投稿する</a></p>'}
"""
        add(f"/categories/{slug}/index.html", page(site, f"/categories/{slug}/", c["name"] + "のプレスリリース", c["description"], body))

    # ---------- 地域 ----------
    area_cards = "".join(
        f'<div class="card"><h3><a href="/areas/{a["slug"]}/">{escape(a["name"])}</a></h3><p class="note">{escape(a["description"])}</p></div>' for a in data["areas"]
    )
    add("/areas/index.html", page(site, "/areas/", "地域一覧", "地域別のプレスリリース一覧です。", "<h1>地域一覧</h1><div class='grid'>" + area_cards + "</div>"))
    for slug, a in areas.items():
        own = [r for r in releases if slug in r["areas"]]
        own_html = cards_with_ads([release_card(r, companies, categories) for r in own])
        body = f"""<h1>{escape(a['name'])}の食ビジネス・プレスリリース</h1>
<p>{escape(a['description'])}</p>
{own_html if own_html else '<p class="note">この地域のプレスリリースはまだありません。</p>'}
"""
        add(f"/areas/{slug}/index.html", page(site, f"/areas/{slug}/", a["name"] + "のプレスリリース", a["description"], body))

    # ---------- 発表タイプ ----------
    add("/type/index.html", page(site, "/type/", "発表タイプ一覧", "発表タイプ別のプレスリリース一覧です。新商品・新メニュー、イベント、キャンペーン、開店・リニューアルなど。", "<h1>発表タイプ一覧</h1><div class='grid'>" + type_cards + "</div>"))
    for slug, t in types.items():
        own = [r for r in releases if r.get("type") == slug]
        own_html = cards_with_ads([release_card(r, companies, categories) for r in own])
        body = f"""<h1>{escape(t['name'])}のプレスリリース</h1>
<p>{escape(t['description'])}</p>
{own_html if own_html else '<p class="note">このタイプのプレスリリースはまだありません。<a href="/submit/">最初の1件を無料で投稿する</a></p>'}
"""
        add(f"/type/{slug}/index.html", page(site, f"/type/{slug}/", t["name"] + "のプレスリリース", t["description"], body))

    # ---------- キーワード ----------
    kw_map = {}
    for r in releases:
        for kw in r["keywords"]:
            kw_map.setdefault(kw, []).append(r)
    kw_links = " ".join(f'<a class="tag" href="/keywords/{kw_slug(kw)}/">{escape(kw)}（{len(v)}）</a>' for kw, v in sorted(kw_map.items()))
    add("/keywords/index.html", page(site, "/keywords/", "キーワード一覧", "プレスリリースのキーワード一覧です。", f"<h1>キーワード一覧</h1><p>{kw_links}</p>"))
    for kw, rs in kw_map.items():
        own_html = cards_with_ads([release_card(r, companies, categories) for r in rs])
        body = f"<h1>「{escape(kw)}」のプレスリリース</h1>{own_html}"
        add(f"/keywords/{kw_slug(kw)}/index.html", page(site, f"/keywords/{kw_slug(kw)}/", f"「{kw}」のプレスリリース", f"{kw}に関するプレスリリースの一覧です。", body))

    # ---------- 日次ダイジェスト ----------
    digest = build_digest(releases, companies, categories)
    digest_index_body = "<h1>日次まとめ（ダイジェスト）</h1><p>その日に公開されたプレスリリースのまとめと、カテゴリ別の動向を自動生成しています。投稿がない日も、掲載済みデータの再構成による特集ページを更新します。</p>"
    if digest:
        digest_index_body += f'<div class="card"><h3><a href="/digest/{digest["slug"]}/">{escape(digest["title"])}</a></h3></div>'
        paras = "".join(f"<p>{escape(p)}</p>" for p in digest["paras"])
        ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": digest["title"], "datePublished": digest["date"], "publisher": {"@type": "Organization", "name": site["name"]}}
        dbody = f"""<article class="release"><h1>{escape(digest['title'])}</h1>
{paras}
<h2 class="sec">本日の新着リリース</h2>
{digest['items_html']}
{ad_slot()}
</article>"""
        add(f"/digest/{digest['slug']}/index.html", page(site, f"/digest/{digest['slug']}/", digest["title"], digest["title"], dbody, ld, "article"), digest["date"])
    add("/digest/index.html", page(site, "/digest/", "日次まとめ", "日次ダイジェストの一覧です。", digest_index_body))

    # ---------- 投稿案内（フォーム仕様込み／ホスティング非依存） ----------
    cat_options = "".join(f'<option value="{c["slug"]}">{escape(c["name"])}</option>' for c in data["categories"])
    cat_options_form = "".join(f'<option>{escape(c["name"])}</option>' for c in data["categories"])
    type_options_form = "".join(f'<option>{escape(t["name"])}</option>' for t in data.get("types", []))
    submit_body = f"""
<h1>プレスリリースを無料で投稿する</h1>
<p>掲載料・配信料・年会費は一切かかりません。投稿回数は無制限、会員登録も不要です。送信後、<strong>AI審査</strong>（スパム・誇大表現・法令・公序良俗チェック）を行い、通過したものから順次公開します。基準は<a href="/review-policy/">審査基準</a>をご覧ください。</p>
{ad_slot()}
<h2 class="sec">投稿フォーム</h2>
<form id="pr-form" class="pr-form">
<label>会社名・団体名・屋号 <span class="req">必須</span></label>
<input type="text" name="会社名・団体名・屋号" required autocomplete="organization">
<label>担当者名 <span class="req">必須</span></label>
<input type="text" name="担当者名" required autocomplete="name">
<label>連絡先メールアドレス <span class="req">必須</span> <span class="note">（非公開。審査・掲載の連絡にのみ使用します）</span></label>
<input type="email" name="連絡先メールアドレス" required autocomplete="email">
<label>公式サイトURL <span class="note">（任意）</span></label>
<input type="url" name="公式サイトURL" placeholder="https://">
<label>業種カテゴリ <span class="req">必須</span></label>
<select name="業種カテゴリ" required>
<option value="">選択してください</option>
{cat_options_form}
</select>
<label>発表タイプ <span class="req">必須</span></label>
<select name="発表タイプ" required>
<option value="">選択してください</option>
{type_options_form}
</select>
<label>地域 <span class="req">必須</span></label>
<select name="地域" required>
<option value="">選択してください</option>
<option>東京都</option>
<option>港区</option>
<option>全国</option>
<option>その他</option>
</select>
<label>タイトル <span class="req">必須</span> <span class="note">（60文字以内目安）</span></label>
<input type="text" name="タイトル" required maxlength="80">
<label>要約 <span class="req">必須</span> <span class="note">（120文字以内目安）</span></label>
<textarea name="要約" rows="3" required maxlength="160"></textarea>
<label>本文 <span class="req">必須</span> <span class="note">（300文字以上）</span></label>
<textarea id="pr-body" name="本文" rows="12" required></textarea>
<p class="count" id="pr-body-count">0文字（300文字以上）</p>
<label>キーワード <span class="note">（任意・カンマ区切りで最大5つ）</span></label>
<input type="text" name="キーワード">
<h2 class="sec">Q&A <span class="note">（任意・最大3組）</span></h2>
<p class="note">読者の疑問に答える形で書くと、検索やAIの回答に取り上げられやすくなります。記事ページにそのまま掲載されます。</p>
<label>質問1</label>
<input type="text" name="質問1" maxlength="120">
<label>回答1</label>
<textarea name="回答1" rows="3" maxlength="600"></textarea>
<label>質問2</label>
<input type="text" name="質問2" maxlength="120">
<label>回答2</label>
<textarea name="回答2" rows="3" maxlength="600"></textarea>
<label>質問3</label>
<input type="text" name="質問3" maxlength="120">
<label>回答3</label>
<textarea name="回答3" rows="3" maxlength="600"></textarea>
<label class="agree"><input type="checkbox" required> <span><a href="/terms/" target="_blank" rel="noopener">利用規約</a>と<a href="/review-policy/" target="_blank" rel="noopener">審査基準</a>に同意します</span></label>
<input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">
<p id="form-error" class="form-error" hidden></p>
<button class="btn" type="submit" id="pr-submit">AI審査へ送信する（無料）</button>
<p class="note">送信内容は朝・夕の2回取り込み、AI審査・整形のうえ公開します。通過したものは最短で当日中、遅くとも翌朝までに公開されます。</p>
</form>
"""
    submit_body += """
<script>
(function(){
var form = document.getElementById('pr-form');
var bodyEl = document.getElementById('pr-body');
var count = document.getElementById('pr-body-count');
function upd(){ var n = bodyEl.value.length; count.textContent = n + '文字（300文字以上）'; count.style.color = n >= 300? '#2f5d3a': '#bc4718';}
bodyEl.addEventListener('input', upd); upd();
form.addEventListener('submit', function(e){
e.preventDefault();
var err = document.getElementById('form-error');
err.hidden = true;
if (!form.checkValidity()) { form.reportValidity(); return;}
if (bodyEl.value.trim().length < 300) { err.textContent = '本文は300文字以上で入力してください。'; err.hidden = false; bodyEl.focus(); return;}
var btn = document.getElementById('pr-submit');
btn.disabled = true; btn.textContent = '送信中…';
var data = {};
new FormData(form).forEach(function(v, k){ data[k] = v;});
data['_subject'] = '新規投稿：' + (data['タイトル'] || '');
data['_template'] = 'table';
data['_captcha'] = 'false';
data['_replyto'] = data['連絡先メールアドレス'] || '';
fetch('https://formsubmit.co/ajax/563542deb0de6c6b25d51ec977c38894', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, body: JSON.stringify(data)})
.then(function(r){ if (!r.ok) { throw new Error('bad response');} return r.json();})
.then(function(){ location.href = '/submit/thanks/';})
.catch(function(){ btn.disabled = false; btn.textContent = 'AI審査へ送信する（無料）'; err.textContent = '送信に失敗しました。時間をおいて再度お試しください。'; err.hidden = false;});
});
})();
</script>
"""
    submit_body += f"""
<h2 class="sec">公開までの流れ</h2>
<ol>
<li>フォーム送信（受付は自動）</li>
<li>AI審査：スパム／誇大表現・景表法／公序良俗／重複投稿をチェック。通過は自動公開キューへ、疑義があるものは保留します（個別の判断依頼は行いません）</li>
<li>整形・カテゴリ／地域／発表タイプ／キーワード付けをして公開。企業ページ・カテゴリページ・タイプ別ページも自動更新</li>
<li>公開URLをご自身のSNS・自社サイトで共有いただくと、より多くの読者に届きます</li>
</ol>
{faq_html}
"""
    add("/submit/index.html", page(site, "/submit/", "無料で投稿する", "プレスリリースを完全無料・回数無制限で投稿できます。フォーム項目仕様と公開までの流れ。", submit_body))
    add("/submit/thanks/index.html", page(site, "/submit/thanks/", "送信を受け付けました", "投稿を受け付けました。", "<h1>送信を受け付けました</h1><p>審査のうえ、通過したものから順次公開します。結果は公開をもってお知らせに代えさせていただきます。</p>"))

    # ---------- 静的ページ群 ----------
    add("/about/index.html", page(site, "/about/", "運営者情報", "運営者情報です。", f"""
<h1>運営者情報</h1>
<table class="spec">
<tr><th>サイト名</th><td>{escape(site['name'])}（{escape(site['name_note'])}）</td></tr>
<tr><th>運営者</th><td>{escape(site['operator'])}</td></tr>
<tr><th>事業内容</th><td>{escape(site['operator_description'])}</td></tr>
<tr><th>連絡先</th><td>{escape(site['contact_note'])}</td></tr>
<tr><th>料金</th><td>プレスリリースの掲載・配信は完全無料です。有料プランはありません。運営費はサイト内の広告収益でまかないます。</td></tr>
</table>
""", org_ld))

    add("/review-policy/index.html", page(site, "/review-policy/", "審査基準", "AI審査の公開・保留・却下基準です。", """
<h1>審査基準（AI審査のルール）</h1>
<p>投稿はすべて自動審査（AI審査＋ルールベース）を行います。審査結果は「公開」「保留」「却下」の3区分で、個別の交渉や判断依頼は行いません。</p>
<p><strong>安全側に倒すのが原則です。少しでも疑わしい投稿は公開せず、保留または却下にします。</strong>「載せてから問題になる」ことを最も避けるべき事態と考え、判定に迷うものは公開側に倒しません。</p>
<h2 class="sec">公開するもの</h2>
<ul class="plain"><li>発表主体（会社・団体・店舗・個人事業主）が実在し、連絡先が確認できるもの</li><li>新商品・新サービス・新店・イベント・キャンペーンなど、事実に基づく発表</li><li>価格・日程・数量などの数値に根拠があり、公式情報と矛盾しないもの</li></ul>
<h2 class="sec">保留するもの（自動で保留フォルダへ）</h2>
<ul class="plain"><li>「日本一」「最高」「絶対」など根拠の確認できない最上級・断定表現を含むもの</li><li>健康・美容・ダイエット等の効能効果を示唆し、裏付けが確認できないもの</li><li>価格・割引率・比較表現が景品表示法上問題になり得るもの</li><li>同一・類似内容の重複投稿、キーワードの詰め込みなどSEO目的とみられるもの</li></ul>
<h2 class="sec">絶対に掲載しないもの（却下）</h2>
<ul class="plain"><li>違法行為・犯罪の助長、公序良俗に反する内容、アダルト・ギャンブルに関するもの</li><li>食の安全を軽んじる内容、衛生・安全性について根拠のない主張をするもの</li><li>「病気が治る」など、健康被害や法令違反（薬機法等）につながる効能効果の断定</li><li>虚偽の実績・受賞歴・認証・売上などの数字、第三者の権利侵害、誹謗中傷</li><li>個人情報を含むもの、反社会的勢力と関わりのある主体のもの</li><li>プレスリリースの体裁を取らない広告文のみの投稿、リンク集目的の投稿</li><li>マルチ商法・投資・情報商材など、消費者トラブルの多い業態の勧誘</li></ul>
<p class="note">保留・却下の判定は自動で行い、個別の理由開示や再審査の依頼には対応しません（運営コストをゼロに保ち、無料掲載を継続するための設計です）。明らかな誤判定はお問い合わせフォームからご連絡ください。</p>
"""))

    add("/terms/index.html", page(site, "/terms/", "利用規約", "利用規約です。", """
<h1>利用規約</h1>
<p>本規約は、本サイト（以下「本サイト」）が提供するプレスリリース掲載サービスの利用条件を定めます。</p>
<h2 class="sec">第1条（サービス内容）</h2><p>本サイトは、投稿者から受け付けたプレスリリースを審査のうえ掲載するサービスを、無料で提供します。掲載の可否・掲載順・掲載期間は運営者が定める審査基準に従います。メディアへの記事化・取材・問い合わせの発生を保証するものではありません。</p>
<h2 class="sec">第2条（料金）</h2><p>掲載・配信に関する料金は一切かかりません。有料プランは存在しません。本サイトは広告収益により運営されます。</p>
<h2 class="sec">第3条（投稿内容の責任）</h2><p>投稿内容の正確性・適法性（景品表示法、食品表示、薬機法その他関係法令を含みます）については投稿者が一切の責任を負います。虚偽・誇大な内容により第三者に損害が生じた場合、運営者は責任を負いません。</p>
<h2 class="sec">第4条（禁止事項）</h2><p>虚偽の発表、第三者の権利を侵害する内容、法令・公序良俗に反する内容、同一内容の大量投稿、自動化ツールによる機械的投稿を禁止します。</p>
<h2 class="sec">第5条（掲載の停止・削除）</h2><p>運営者は、審査基準に反すると判断した掲載を、事前の通知なく非公開化・削除できます。</p>
<h2 class="sec">第6条（免責）</h2><p>本サイトの利用により生じた損害について、運営者の故意・重過失による場合を除き責任を負いません。サービスは予告なく変更・中断・終了する場合があります。</p>
<h2 class="sec">第7条（規約の変更）</h2><p>本規約は必要に応じて変更します。変更後の規約は本サイトへの掲載をもって効力を生じます。</p>
<p class="note">制定日：2026年11月16日（ドラフト。公開前に正式化します）</p>
"""))

    add("/privacy/index.html", page(site, "/privacy/", "プライバシーポリシー", "プライバシーポリシーです。", """
<h1>プライバシーポリシー</h1>
<h2 class="sec">取得する情報</h2><p>投稿フォーム・お問い合わせフォームで入力された会社名、担当者名、メールアドレス、投稿内容を取得します。メールアドレス等の連絡先は公開しません。</p>
<h2 class="sec">利用目的</h2><p>審査・掲載・運営上の連絡のためにのみ利用します。マーケティング目的で第三者へ提供することはありません。</p>
<h2 class="sec">広告について</h2><p>本サイトは第三者配信の広告サービス（Google AdSense等）を利用する場合があります。広告配信事業者はCookieを使用して、利用者の興味に応じた広告を表示することがあります。Cookieの利用はブラウザ設定で無効化できます。</p>
<h2 class="sec">アクセス解析</h2><p>サイト改善のため、個人を特定しない形でアクセス情報を計測する場合があります。</p>
<h2 class="sec">開示・削除の請求</h2><p>ご自身の情報の開示・訂正・削除はお問い合わせフォームからご請求ください。本人確認のうえ対応します。</p>
<p class="note">制定日：2026年11月16日（ドラフト。公開前に正式化します）</p>
"""))

    contact_body = """
<h1>お問い合わせ</h1>
<p>掲載内容の訂正・削除、誤判定のご連絡、その他運営へのお問い合わせはこちらからお願いします。審査の個別結果に関するお問い合わせには対応していません（<a href="/review-policy/">審査基準</a>をご確認ください）。</p>
<p>お問い合わせは投稿フォームから受け付けます。タイトルのはじめに【お問い合わせ】とご記入ください（審査・公開の対象にはなりません）。</p>
<p><a class="btn" href="/submit/">投稿フォームへ</a></p>
"""
    add("/contact/index.html", page(site, "/contact/", "お問い合わせ", "お問い合わせフォームです。", contact_body))

    # ---------- sitemap / robots / llms / feed ----------
    today = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod in urls:
        loc = rel_url(site["base_url"], path.replace("index.html", ""))
        sm.append(f"<url><loc>{escape(loc)}</loc><lastmod>{lastmod or today}</lastmod></url>")
    sm.append("</urlset>")
    write("/sitemap.xml", "\n".join(sm))

    write("/robots.txt", f"""User-agent: *
Allow: /
Sitemap: {site['base_url']}/sitemap.xml
""")

    llms_lines = [f"# {site['name']}", "", f"> {site['description']}", "", "## プレスリリース"]
    for r in releases:
        llms_lines.append(f"- [{r['title']}]({site['base_url']}/releases/{r['slug']}/): {r['summary']}")
    llms_lines += ["", "## 発表タイプ"]
    for t in data.get("types", []):
        llms_lines.append(f"- [{t['name']}]({site['base_url']}/type/{t['slug']}/): {t['description']}")
    llms_lines += ["", "## 企業"]
    for c in data["companies"]:
        llms_lines.append(f"- [{c['name']}]({site['base_url']}/companies/{c['slug']}/): {c['description']}")
    llms_lines += ["", "## 投稿", f"- [無料で投稿する]({site['base_url']}/submit/): 完全無料・回数無制限。AI審査のうえ公開。"]
    write("/llms.txt", "\n".join(llms_lines) + "\n")

    feed_items = "".join(
        f"<item><title>{escape(r['title'])}</title><link>{site['base_url']}/releases/{r['slug']}/</link>"
        f"<guid>{site['base_url']}/releases/{r['slug']}/</guid><pubDate>{r['published_at']}</pubDate>"
        f"<description>{escape(r['summary'])}</description></item>"
        for r in releases
    )
    write("/feed.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{escape(site['name'])}</title><link>{site['base_url']}/</link><description>{escape(site['description'])}</description>{feed_items}</channel></rss>
""")

    print(f"built {len(urls)} pages + sitemap({len(urls)} urls) + robots.txt + llms.txt + feed.xml")
    for p, _ in urls:
        print(" ", p)


if __name__ == "__main__":
    main()
