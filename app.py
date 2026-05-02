import re
import requests
from flask import Flask, Response
from datetime import datetime
import xml.etree.ElementTree as ET

app = Flask(__name__)

WP_API = "https://www.gazetaesportiva.com/wp-json/wp/v2"

def get_categories():
    try:
        r = requests.get(f"{WP_API}/categories?per_page=100", timeout=10)
        cats = r.json()
        return {c["id"]: c["name"] for c in cats}
    except:
        return {}

def get_posts(per_page=50):
    try:
        # _embed traz a imagem destacada embutida no JSON
        r = requests.get(
            f"{WP_API}/posts",
            params={
                "per_page": per_page,
                "orderby": "date",
                "order": "desc",
                "_embed": "wp:featuredmedia",
                "_fields": "id,title,link,date,excerpt,categories,featured_media,jetpack_featured_media_url,_embedded,_links"
            },
            timeout=15
        )
        return r.json()
    except Exception as e:
        print(f"Erro ao buscar posts: {e}")
        return []

def get_image_url(post):
    """Tenta extrair a imagem pelo maior número de métodos possível."""

    # Método 1: jetpack_featured_media_url (direto no post)
    img = post.get("jetpack_featured_media_url", "")
    if img:
        return img

    # Método 2: _embedded wp:featuredmedia (via ?_embed)
    try:
        embedded = post.get("_embedded", {})
        media_list = embedded.get("wp:featuredmedia", [])
        if media_list:
            media = media_list[0]
            # Tamanho grande preferido
            sizes = media.get("media_details", {}).get("sizes", {})
            for size in ["large", "medium_large", "medium", "full"]:
                if size in sizes:
                    return sizes[size]["source_url"]
            # Fallback: source_url direto
            src = media.get("source_url", "")
            if src:
                return src
    except:
        pass

    # Método 3: buscar via endpoint /media/{id}
    media_id = post.get("featured_media", 0)
    if media_id:
        try:
            r = requests.get(f"{WP_API}/media/{media_id}?_fields=source_url", timeout=8)
            data = r.json()
            src = data.get("source_url", "")
            if src:
                return src
        except:
            pass

    return ""

def build_rss(posts, categories):
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    rss.set("xmlns:media", "http://search.yahoo.com/mrss/")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")

    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Gazeta Esportiva - Últimas Notícias"
    ET.SubElement(channel, "link").text = "https://www.gazetaesportiva.com"
    ET.SubElement(channel, "description").text = "Feed RSS atualizado - Gazeta Esportiva"
    ET.SubElement(channel, "language").text = "pt-BR"
    ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    for post in posts:
        item = ET.SubElement(channel, "item")

        title = post.get("title", {}).get("rendered", "Sem título")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = post.get("link", "")
        ET.SubElement(item, "guid", isPermaLink="true").text = post.get("link", "")

        # Data
        date_str = post.get("date", "")
        try:
            dt = datetime.fromisoformat(date_str)
            pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except:
            pub_date = date_str
        ET.SubElement(item, "pubDate").text = pub_date

        # Categorias
        for cat_id in post.get("categories", []):
            cat_name = categories.get(cat_id, "")
            if cat_name:
                ET.SubElement(item, "category").text = cat_name

        # Descrição
        excerpt_raw = post.get("excerpt", {}).get("rendered", "")
        excerpt_clean = re.sub(r"<[^>]+>", "", excerpt_raw).strip()
        ET.SubElement(item, "description").text = excerpt_clean

        # Imagem — tenta todos os métodos
        img_url = get_image_url(post)
        if img_url:
            # enclosure (compatível com a maioria dos apps RSS)
            enc = ET.SubElement(item, "enclosure")
            enc.set("url", img_url)
            enc.set("type", "image/jpeg")
            enc.set("length", "0")

            # media:content (padrão Yahoo Media RSS)
            mc = ET.SubElement(item, "media:content")
            mc.set("url", img_url)
            mc.set("medium", "image")
            mc.set("type", "image/jpeg")

            # media:thumbnail (fallback extra)
            mt = ET.SubElement(item, "media:thumbnail")
            mt.set("url", img_url)

    tree = ET.tostring(rss, encoding="unicode", xml_declaration=False)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{tree}'

@app.route("/rss")
@app.route("/feed")
@app.route("/")
def rss_feed():
    posts = get_posts(per_page=50)
    categories = get_categories()
    xml_content = build_rss(posts, categories)
    return Response(xml_content, mimetype="application/rss+xml; charset=utf-8")

@app.route("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
