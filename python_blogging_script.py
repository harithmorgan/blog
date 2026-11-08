"""
Blog site generator.

Folders:
    blog_txtfiles/            -> current posts   (shown in "Recent & Featured Posts")
    archived_blog_txtfiles/   -> archived posts  (shown in "Archived Posts")

To feature an archived post in the Recent & Featured section, add this line
to the top of its text file (next to overwrite_permission):
    featured = yes

Prev/next links stay inside each index section, in date order:
    current posts + featured archived posts link to each other,
    non-featured archived posts link only to each other.

Related posts are shared across both folders.
"""

import os
from datetime import datetime

import bs4

#///////////////////////    SETTINGS   ///////////////////////////////

CURRENT_FOLDER = "blog_txtfiles"
ARCHIVE_FOLDER = "archived_blog_txtfiles"

PAGE_TEMPLATE = "prosetemplate_withcommentfunction.html"
TILE_TEMPLATE = "blogpost_tile_template.html"
INDEX_FILE = "index.html"

RECENT_SECTION = "blog_post_tiles"        # tag in index.html
ARCHIVE_SECTION = "archived_post_tiles"   # tag in index.html

TILE_SEPARATOR = "<!-- ///////// -->"
DATE_FORMAT = "%B %d, %Y"

# Should a featured archived post also stay listed in the Archived section?
SHOW_FEATURED_IN_ARCHIVE_TOO = True

# Max number of related posts per page (None = no limit)
MAX_RELATED_POSTS = None


#///////////////////////    HELPERS   ////////////////////////////////

def replace_placeholders(text, var_dict, prefix=""):
    """Replace prefix+key with its value, longest keys first so that a
    short key (e.g. blog_img) never clobbers a longer one that starts with
    it. blog_content goes last so other keys are never substituted inside
    the post body."""
    keys = sorted(var_dict.keys(), key=len, reverse=True)
    if "blog_content" in keys:
        keys.remove("blog_content")
        keys.append("blog_content")
    for key in keys:
        text = text.replace(prefix + key, var_dict[key])
    return text


def fill_neighbor_placeholders(text, var_dict, word):
    """Template names neighbour placeholders by inserting the word after the
    first underscore: html_filename -> html_previous_filename,
    blog_title -> blog_next_title."""
    keys = sorted((k for k in var_dict if "_" in k and k != "blog_content"),
                  key=len, reverse=True)
    for key in keys:
        head, tail = key.split("_", 1)
        text = text.replace(f"{head}_{word}_{tail}", var_dict[key])
    return text


def load_template(path):
    with open(path, "rb") as f:
        return bs4.BeautifulSoup(f, "html.parser").prettify()


def load_soup(path):
    with open(path, "rb") as f:
        return bs4.BeautifulSoup(f, "html.parser")


def save_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def is_yes(value):
    return str(value).strip().lower() == "yes"


#///////////////////////    READING POSTS   //////////////////////////

def grab_txtfile_variables(path):
    """Read a post text file. `path` includes its folder."""
    var_dict = {"blog_content": ""}
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    is_blog_content = False
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("blog_content"):
            is_blog_content = True
            continue
        if is_blog_content and "]end" in stripped:
            is_blog_content = False
            continue

        if is_blog_content:
            var_dict["blog_content"] += stripped + "<br>"   # keep the whole line
        else:
            parts = stripped.split(" =", 1)                 # split once only
            if len(parts) == 2:
                var_dict[parts[0].strip()] = parts[1].strip()
    return var_dict


def collect_posts(folder):
    """Return a list of post dicts for every text file in `folder`."""
    posts = []
    if not os.path.isdir(folder):
        print(f"WARNING: folder not found, skipping: {folder}")
        return posts

    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if name.startswith(".") or not os.path.isfile(path):
            continue   # skips .DS_Store and subfolders

        var_dict = grab_txtfile_variables(path)
        try:
            date = datetime.strptime(var_dict["blog_date"], DATE_FORMAT)
        except (KeyError, ValueError):
            print(f"WARNING: missing or bad blog_date, skipping: {path}")
            continue

        posts.append({
            "path": path,
            "vars": var_dict,
            "date": date,
            "archived": folder == ARCHIVE_FOLDER,
            "featured": is_yes(var_dict.get("featured", "no")),
        })
    return posts


#///////////////////////    BLOG PAGES   /////////////////////////////

def generate_html_file(var_dict, previous_var_dict, next_var_dict, template_file):
    page_code = load_template(template_file)

    # fill the previous/next placeholders first (html_previous_filename,
    # blog_next_title, ...), then this post's own values
    page_code = fill_neighbor_placeholders(page_code, previous_var_dict, "previous")
    page_code = fill_neighbor_placeholders(page_code, next_var_dict, "next")
    page_code = replace_placeholders(page_code, var_dict)

    # make the prev/next block visible
    soup = bs4.BeautifulSoup(page_code, "html.parser")
    if soup.prev_next_posts is not None:
        soup.prev_next_posts["style"] = "visibility: visible;"

    save_text(var_dict["html_filename"], soup.prettify())


def build_chain(posts, chain_name, start_link, end_link):
    """Generate pages for one folder's posts (oldest -> newest) and link
    each to its neighbours within that same list only."""
    print(f"\n========== {chain_name} ==========")
    for i, post in enumerate(posts):
        var_dict = post["vars"]
        previous_var_dict = start_link if i == 0 else posts[i - 1]["vars"]
        next_var_dict = end_link if i == len(posts) - 1 else posts[i + 1]["vars"]

        html_file = var_dict["html_filename"]
        print(html_file)

        if not os.path.exists(html_file):
            generate_html_file(var_dict, previous_var_dict, next_var_dict, PAGE_TEMPLATE)
            print("  new file generated")
        elif is_yes(var_dict.get("overwrite_permission", "no")):
            generate_html_file(var_dict, previous_var_dict, next_var_dict, PAGE_TEMPLATE)
            print(f"  previous file overwritten: {post['path']}")
        else:
            print(f"  file already exists, will not overwrite: {post['path']}")


#///////////////////////    RELATED POSTS   //////////////////////////

def build_tags_dict(posts_newest_first):
    tags_dict = {}
    for post in posts_newest_first:
        for tag in post["vars"].get("blog_tags", "").split():
            tags_dict.setdefault(tag, []).append(post)
    return tags_dict


def add_related_posts(post, tags_dict, tile_template):
    var_dict = post["vars"]
    file_to_edit = var_dict["html_filename"]
    if not os.path.exists(file_to_edit):
        return

    # unique related posts (one per html page), excluding this page,
    # in newest-first order
    related = []
    seen_pages = {file_to_edit}
    for tag in var_dict.get("blog_tags", "").split():
        for other in tags_dict.get(tag, []):
            page = other["vars"]["html_filename"]
            if page not in seen_pages:
                seen_pages.add(page)
                related.append(other)
    if MAX_RELATED_POSTS is not None:
        related = related[:MAX_RELATED_POSTS]

    related_posts_content = ""
    for other in related:
        tile = replace_placeholders(tile_template, other["vars"])
        tile = tile.replace("col-lg-4", "col-lg-2")
        tile = tile.replace("col-md-6", "col-md-3")
        tile = tile.replace("col-sm-6", "col-sm-3")
        related_posts_content += tile

    page_code = load_soup(file_to_edit)
    if page_code.related_posts is None:
        print(f"  no <related_posts> section in {file_to_edit}, skipped")
        return

    page_code.related_posts.clear()
    page_code.related_posts.extend(bs4.BeautifulSoup(related_posts_content, "html.parser"))
    save_text(file_to_edit, page_code.prettify())


#///////////////////////    INDEX PAGE   /////////////////////////////

def make_tile(var_dict, tile_template):
    tile = replace_placeholders(tile_template, var_dict)
    if TILE_SEPARATOR not in tile:
        tile += TILE_SEPARATOR
    return tile


def unique_pages(posts):
    seen, result = set(), []
    for p in posts:
        page = p["vars"]["html_filename"]
        if page not in seen:
            seen.add(page)
            result.append(p)
    return result


def rebuild_index_page(recent_posts, archive_posts, tile_template):
    """Clear both index sections and refill them from the post lists."""
    index_page_code = load_soup(INDEX_FILE)

    for section_name, posts in [(RECENT_SECTION, recent_posts),
                                (ARCHIVE_SECTION, archive_posts)]:
        section = index_page_code.find(section_name)
        if section is None:
            print(f"WARNING: <{section_name}> not found in {INDEX_FILE}")
            continue

        tiles = "".join(make_tile(p["vars"], tile_template) for p in posts)
        section.clear()
        section.extend(bs4.BeautifulSoup(tiles, "html.parser"))
        print(f"{len(posts)} tiles written to <{section_name}>")

    save_text(INDEX_FILE, index_page_code.prettify())


#///////////////////////    MAIN CODE   //////////////////////////////

def main():
    current_posts = sorted(collect_posts(CURRENT_FOLDER), key=lambda p: p["date"])
    archived_posts = sorted(collect_posts(ARCHIVE_FOLDER), key=lambda p: p["date"])
    all_posts = current_posts + archived_posts

    # warn about two text files producing the same html page
    seen = {}
    for p in all_posts:
        name = p["vars"].get("html_filename")
        if name in seen:
            print(f"WARNING: {p['path']} and {seen[name]} both write {name}")
        seen[name] = p["path"]

    print("Current posts: ", [p["path"] for p in current_posts])
    print("Archived posts:", [p["path"] for p in archived_posts])

    featured_archived = [p for p in archived_posts if p["featured"]]

    # 1. blog pages + prev/next
    #    Recent & Featured chain: current posts + featured archived posts, by date
    #    Archive chain: the remaining (non-featured) archived posts, by date
    recent_chain = unique_pages(
        sorted(current_posts + featured_archived, key=lambda p: p["date"]))
    recent_pages = {p["vars"]["html_filename"] for p in recent_chain}
    archive_chain = [p for p in archived_posts
                     if p["vars"]["html_filename"] not in recent_pages]

    build_chain(recent_chain, "RECENT & FEATURED POSTS",
                start_link={"blog_title": "Main Page", "html_filename": INDEX_FILE},
                end_link={"blog_title": "Coming Soon", "html_filename": INDEX_FILE})
    build_chain(archive_chain, "ARCHIVED POSTS",
                start_link={"blog_title": "Main Page", "html_filename": INDEX_FILE},
                end_link={"blog_title": "Main Page", "html_filename": INDEX_FILE})

    tile_template = load_template(TILE_TEMPLATE)

    # 2. index page: newest first in each section
    recent_section = list(reversed(current_posts)) + list(reversed(featured_archived))

    if SHOW_FEATURED_IN_ARCHIVE_TOO:
        archive_section = list(reversed(archived_posts))
    else:
        archive_section = [p for p in reversed(archived_posts) if not p["featured"]]

    recent_section = unique_pages(recent_section)
    archive_section = unique_pages(archive_section)

    print("\n========== INDEX PAGE ==========")
    rebuild_index_page(recent_section, archive_section, tile_template)

    # 3. related posts on every page, drawn from both folders
    print("\n========== RELATED POSTS ==========")
    all_newest_first = sorted(all_posts, key=lambda p: p["date"], reverse=True)
    tags_dict = build_tags_dict(all_newest_first)
    for post in all_posts:
        add_related_posts(post, tags_dict, tile_template)
    print("related posts updated on", len(all_posts), "pages")


if __name__ == "__main__":
    main()