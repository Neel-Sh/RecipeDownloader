import os
import logging
import requests
from flask import Flask, render_template, request, flash
from bs4 import BeautifulSoup
import json
from recipe_scrapers import scrape_me, WebsiteNotImplementedError
from extruct import extract
from w3lib.html import get_base_url
import re
from readability.readability import Document

app = Flask(__name__)
# Use an env var for SECRET_KEY in prod; random for dev
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# Basic console logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_recipe(url):
    """Fetch URL, parse Recipe via JSON‑LD or HTML fallback."""
    # 0) Try site-specific parsing via recipe-scrapers
    try:
        scraper = scrape_me(url)
        title = scraper.title()
        ingredients = scraper.ingredients()
        # instructions is a single string with newlines
        raw_instr = scraper.instructions() or ""
        steps = [s.strip() for s in raw_instr.split("\n") if s.strip()]
        if ingredients and steps:
            return title, ingredients, steps
    except WebsiteNotImplementedError:
        pass  # scraper not implemented for this site
    except Exception as e:
        logger.info(f"recipe-scrapers failed: {e}")
    resp = requests.get(url, headers={"User-Agent": "recipe-scraper"}, timeout=10)
    resp.raise_for_status()
    # 1) Try Extruct for JSON-LD, Microdata, RDFa
    try:
        html = resp.text
        base = get_base_url(html, resp.url)
        meta = extract(html, base_url=base)
        # JSON-LD entries
        for data in meta.get("json-ld", []):
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Recipe":
                    title = item.get("name") or _fallback_title(BeautifulSoup(html, "html.parser"))
                    ingredients = item.get("recipeIngredient") or item.get("ingredients") or []
                    raw_instr = item.get("recipeInstructions", [])
                    steps = _normalize_instructions(raw_instr)
                    if ingredients and steps:
                        return title, ingredients, steps
        # Microdata entries
        for entry in meta.get("microdata", {}).get("items", []):
            types = entry.get("type", [])
            if "Recipe" in types or "http://schema.org/Recipe" in types:
                props = entry.get("properties", {})
                title = props.get("name", [None])[0] or _fallback_title(BeautifulSoup(html, "html.parser"))
                ingredients = props.get("recipeIngredient") or props.get("ingredients") or []
                raw_instr = props.get("recipeInstructions") or []
                steps = []
                if isinstance(raw_instr, list):
                    for pt in raw_instr:
                        if isinstance(pt, str):
                            steps.append(pt.strip())
                        elif isinstance(pt, dict):
                            text = pt.get("text") or pt.get("name")
                            if text: steps.append(text.strip())
                elif isinstance(raw_instr, str):
                    steps = [s.strip() for s in raw_instr.split(".") if s.strip()]
                if ingredients and steps:
                    return title, ingredients, steps
    except Exception as e:
        logger.info(f"extruct parsing failed: {e}")

    # Let BeautifulSoup sniff encoding
    soup = BeautifulSoup(resp.content, "html.parser")

    # 2) Try JSON‑LD
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        raw = tag.string or tag.get_text()
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        if "@graph" in data:
            items = data["@graph"]
        elif isinstance(data, list):
            items = data
        else:
            items = [data]
        for item in items:
            if item.get("@type") == "Recipe":
                title = item.get("name") or _fallback_title(soup)
                ingredients = item.get("recipeIngredient") or item.get("ingredients") or []
                steps = _normalize_instructions(item.get("recipeInstructions", []))
                if ingredients and steps:
                    return title, ingredients, steps

    # 3) Fallback: scrape HTML
    title, ingredients, steps = _scrape_html_fallback(soup)
    if ingredients and steps:
        return title, ingredients, steps

    # 4) Readability + regex fallback
    read_result = super_generic_extractor(url)
    if read_result:
        ingredients, steps = read_result
        title = _fallback_title(soup)
        return title, ingredients, steps

    raise ValueError("No Recipe data found on that page.")


def _fallback_title(soup):
    """Use <title> or first <h1> if JSON‑LD has no name."""
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    return h1.get_text().strip() if h1 else "Recipe"


def _normalize_instructions(raw):
    """Turn JSON‑LD instructions into a list of strings."""
    steps = []
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, str):
                steps.append(entry.strip())
            elif isinstance(entry, dict):
                text = entry.get("text") or entry.get("name")
                if text:
                    steps.append(text.strip())
    elif isinstance(raw, str):
        # split on periods, drop empties
        steps = [s.strip() for s in raw.split(".") if s.strip()]
    return steps


def _scrape_html_fallback(soup):
    """Combined simple (list-only) and generic fallback parsing for recipes."""
    title = _fallback_title(soup)

    # --- Simple fallback: strict list parsing ---
    ingredients_simple = []
    steps_simple = []

    # Simple ingredients from the first list after a heading containing 'ingredient'
    ingr_hdr = soup.find(lambda tag:
        tag.name in ["h1","h2","h3","h4","strong","b"] and
        "ingredient" in tag.get_text().lower()
    )
    if ingr_hdr:
        for sib in ingr_hdr.next_siblings:
            if getattr(sib, "name", None) in ["ul", "ol"]:
                for li in sib.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        ingredients_simple.append(text)
                break

    # Simple steps from the first list or paragraph after a heading containing 'instruction'
    instr_hdr = soup.find(lambda tag:
        tag.name in ["h1","h2","h3","h4","strong","b"] and
        any(k in tag.get_text().lower() for k in ["instruction","direction","method","step"])
    )
    if instr_hdr:
        for sib in instr_hdr.next_siblings:
            if getattr(sib, "name", None) in ["ul", "ol"]:
                for li in sib.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        steps_simple.append(text)
                break
            if getattr(sib, "name", None) == "p":
                text = sib.get_text(strip=True)
                if text:
                    steps_simple.append(text)
        # Note: stops after first paragraph or list

    # If both simple lists found, return them
    if ingredients_simple and steps_simple:
        return title, ingredients_simple, steps_simple

    # --- Generic helper to grab lists or paragraphs until next heading ---
    def extract_section_text(start_tag):
        content = []
        for sibling in start_tag.find_all_next():
            if sibling.name and sibling.name.startswith("h"):
                break
            if sibling.name in ["ul", "ol"]:
                for li in sibling.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        content.append(text)
                break
            if sibling.name in ["p", "div"]:
                text = sibling.get_text(strip=True)
                if text:
                    content.append(text)
        return content

    # Generic ingredients section
    ingredients = []
    ingr_heading = soup.find(lambda tag:
        tag.name and tag.name.startswith("h") and
        "ingredient" in tag.get_text().lower()
    )
    if ingr_heading:
        ingredients = extract_section_text(ingr_heading)

    # Generic steps section
    steps = []
    step_heading = soup.find(lambda tag:
        tag.name and tag.name.startswith("h") and
        any(k in tag.get_text().lower() for k in ["instruction","method","direction","preparation","steps"])
    )
    if step_heading:
        steps = extract_section_text(step_heading)

    return title, ingredients, steps

def super_generic_extractor(url):
    """Use Readability + regex to extract ingredients and steps from unstructured pages."""
    resp = requests.get(url, headers={"User-Agent": "recipe-scraper"}, timeout=10)
    resp.raise_for_status()
    html = resp.text
    # Clean article HTML
    article_html = Document(html).summary()
    text = BeautifulSoup(article_html, "html.parser").get_text("\n")
    text = re.sub(r'\r', '', text)
    # Split on "ingredients"
    parts = re.split(r'\bingredients\b', text, flags=re.I)
    if len(parts) < 2:
        return None
    rest = parts[1]
    # Split into ingredients vs method
    split_instr = re.split(
        r'\b(method|instructions|directions|preparation|steps)\b',
        rest, flags=re.I
    )
    ing = split_instr[0]
    tail = split_instr[1:] if len(split_instr) > 1 else []
    ingredients = [line.strip('-• \t') for line in ing.splitlines() if line.strip()]
    steps_text = "\n".join(tail)
    steps = [s.strip() for s in re.split(r'[\n\.]', steps_text) if s.strip()]
    if ingredients and steps:
        return ingredients, steps
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            flash("Please enter a recipe URL.", "error")
        else:
            try:
                title, ingredients, steps = parse_recipe(url)
                return render_template(
                    "recipe.html",
                    title=title,
                    url=url,
                    ingredients=ingredients,
                    steps=steps
                )
            except Exception as e:
                logger.error(f"Error parsing recipe: {e}")
                flash(f"Could not parse recipe: {e}", "error")
    return render_template("index.html")


if __name__ == "__main__":
    # Set host='0.0.0.0' if you want external access
    app.run(debug=True, port=5000)