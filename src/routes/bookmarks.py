
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..extensions import db
from ..models import Bookmark
from sqlalchemy import or_

bookmarks_bp = Blueprint('bookmarks', __name__)

CATEGORIES = [
    ("daily",     "Daily use"),
    ("important", "Important links"),
    ("personal",  "Personal"),
    ("company",   "Company links"),
    ("reference", "Reference links"),
    ("other",     "Others"),
]

@bookmarks_bp.route("/", methods=["GET"], endpoint="dashboard")
@login_required
def dashboard():
    by_cat = {}
    for key, _label in CATEGORIES:
        by_cat[key] = (
            Bookmark.query
            .filter(Bookmark.category == key)
            .order_by(Bookmark.created_at.desc())
            .all()
        )
    counts = {k: len(v) for k, v in by_cat.items()}
    return render_template("bookmarks/dashboard.html",
                           categories=CATEGORIES,
                           by_cat=by_cat,
                           counts=counts)

# Legacy: keep old links working (if your navbar still points here)
@bookmarks_bp.route("/list", methods=["GET"], endpoint="list_bookmarks")
@login_required
def list_bookmarks():
    return redirect(url_for("bookmarks.dashboard"))

@bookmarks_bp.route("/new", methods=["GET", "POST"], endpoint="new_bookmark")
@login_required
def new_bookmark():
    if request.method == "POST":
        b = Bookmark(
            title=request.form["title"].strip(),
            url=request.form["url"].strip(),
            kind=request.form.get("kind", "web"),
            notes=request.form.get("notes", ""),
            category=request.form.get("category", "other"),
        )
        db.session.add(b)
        db.session.commit()
        flash("Bookmark added", "success")
        return redirect(url_for("bookmarks.dashboard"))
    return render_template("bookmarks/form.html", bookmark=None)

@bookmarks_bp.route("/<int:bid>/edit", methods=["GET", "POST"], endpoint="edit_bookmark")
@login_required
def edit_bookmark(bid):
    b = Bookmark.query.get_or_404(bid)
    if request.method == "POST":
        b.title = request.form["title"].strip()
        b.url = request.form["url"].strip()
        b.kind = request.form.get("kind", "web")
        b.notes = request.form.get("notes", "")
        b.category = request.form.get("category", "other")
        db.session.commit()
        flash("Bookmark updated", "success")
        return redirect(url_for("bookmarks.dashboard"))
    return render_template("bookmarks/form.html", bookmark=b)

@bookmarks_bp.route("/<int:bid>/delete", methods=["POST"], endpoint="delete_bookmark")
@login_required
def delete_bookmark(bid):
    b = Bookmark.query.get_or_404(bid)
    db.session.delete(b)
    db.session.commit()
    flash("Bookmark deleted", "info")
    return redirect(url_for("bookmarks.dashboard"))

@bookmarks_bp.route("/manage", methods=["GET"], endpoint="manage")
@login_required
def manage():
    q   = (request.args.get("q") or "").strip()
    cat = (request.args.get("cat") or "all").strip().lower()

    query = Bookmark.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Bookmark.title.ilike(like),
            Bookmark.url.ilike(like),
            Bookmark.notes.ilike(like)
        ))
    if cat and cat != "all":
        query = query.filter(Bookmark.category == cat)

    items = query.order_by(Bookmark.updated_at.desc()).all()
    return render_template(
        "bookmarks/manage.html",
        items=items,
        q=q,
        cat=cat,
        categories=CATEGORIES
    )