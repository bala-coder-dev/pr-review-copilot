"""
PR Review Copilot — FastAPI entry point.
Week 3: Added database initialization and dashboard route.
"""
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.webhook import router as webhook_router
from app.database import create_tables, get_all_reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on startup — creates database tables if they don't exist
    create_tables()
    print("[main] Database tables created successfully")
    yield


app = FastAPI(
    title="PR Review Copilot",
    description="AI-powered GitHub PR reviewer",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    reviews = get_all_reviews()

    rows = ""
    for r in reviews:
        rows += f"""
        <tr>
            <td>#{r.pr_number}</td>
            <td>{r.repo_name}</td>
            <td>{r.pr_title}</td>
            <td>@{r.author}</td>
            <td>{r.created_at.strftime("%Y-%m-%d %H:%M")}</td>
            <td><a href="/review/{r.id}">View Review</a></td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='6'>No reviews yet. Open a PR to get started!</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PR Review Copilot Dashboard</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 40px auto;
                padding: 20px;
                background: #0d1117;
                color: #c9d1d9;
            }}
            h1 {{
                color: #58a6ff;
                border-bottom: 1px solid #30363d;
                padding-bottom: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background: #161b22;
                padding: 12px;
                text-align: left;
                color: #58a6ff;
                border: 1px solid #30363d;
            }}
            td {{
                padding: 12px;
                border: 1px solid #30363d;
            }}
            tr:hover {{
                background: #161b22;
            }}
            a {{
                color: #58a6ff;
                text-decoration: none;
            }}
            .badge {{
                background: #238636;
                color: white;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <h1>🤖 PR Review Copilot Dashboard</h1>
        <p>Total Reviews: <span class="badge">{len(reviews)}</span></p>
        <table>
            <thead>
                <tr>
                    <th>PR</th>
                    <th>Repository</th>
                    <th>Title</th>
                    <th>Author</th>
                    <th>Reviewed At</th>
                    <th>Review</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


@app.get("/review/{review_id}", response_class=HTMLResponse)
async def view_review(review_id: int):
    from app.database import SessionLocal, Review
    db = SessionLocal()
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            return HTMLResponse("<h1>Review not found</h1>", status_code=404)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Review #{review.pr_number}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 900px;
                    margin: 40px auto;
                    padding: 20px;
                    background: #0d1117;
                    color: #c9d1d9;
                }}
                h1 {{ color: #58a6ff; }}
                .review-box {{
                    background: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 8px;
                    padding: 20px;
                    white-space: pre-wrap;
                    line-height: 1.6;
                }}
                a {{ color: #58a6ff; }}
                .meta {{
                    color: #8b949e;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <a href="/dashboard">← Back to Dashboard</a>
            <h1>🤖 Review for PR #{review.pr_number}</h1>
            <div class="meta">
                <strong>Repo:</strong> {review.repo_name} |
                <strong>Author:</strong> @{review.author} |
                <strong>Date:</strong> {review.created_at.strftime("%Y-%m-%d %H:%M")}
            </div>
            <h2>{review.pr_title}</h2>
            <div class="review-box">{review.review_text}</div>
        </body>
        </html>
        """
        return html
    finally:
        db.close()