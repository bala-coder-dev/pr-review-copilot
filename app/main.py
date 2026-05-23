from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.webhook import router as webhook_router
from app.database import create_tables, get_all_reviews
import re


def extract_score(review_text: str) -> int | None:
    # Match formats: SCORE: 8/10 or SCORE: 8 out of 10
    match = re.search(r'SCORE:\s*(\d+)(?:/10|\s+out\s+of\s+10)', review_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # Also try finding standalone score pattern
    match = re.search(r'(\d+)\s*/\s*10', review_text)
    if match:
        return int(match.group(1))
    return None


def score_color(score: int | None) -> str:
    if score is None:
        return "#8b949e"
    if score >= 8:
        return "#238636"
    if score >= 5:
        return "#d29922"
    return "#da3633"


def score_label(score: int | None) -> str:
    if score is None:
        return "N/A"
    if score >= 8:
        return "Excellent"
    if score >= 5:
        return "Average"
    return "Needs Work"


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/", response_class=HTMLResponse)
async def landing():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PR Review Copilot</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0d1117;
                color: #c9d1d9;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 40px 20px;
            }
            .hero { max-width: 700px; }
            .logo { font-size: 80px; margin-bottom: 20px; }
            h1 {
                font-size: 48px;
                color: #58a6ff;
                margin-bottom: 16px;
                font-weight: 700;
            }
            p {
                font-size: 18px;
                color: #8b949e;
                margin-bottom: 40px;
                line-height: 1.6;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 40px;
                text-align: left;
            }
            .feature {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 20px;
            }
            .feature-icon { font-size: 32px; margin-bottom: 10px; }
            .feature h3 { color: #58a6ff; margin-bottom: 8px; font-size: 16px; }
            .feature p { font-size: 14px; margin-bottom: 0; }
            .btn {
                background: #238636;
                color: white;
                padding: 14px 32px;
                border-radius: 8px;
                text-decoration: none;
                font-size: 16px;
                font-weight: 600;
                display: inline-block;
                transition: background 0.2s;
            }
            .btn:hover { background: #2ea043; }
        </style>
    </head>
    <body>
        <div class="hero">
            <div class="logo">🤖</div>
            <h1>PR Review Copilot</h1>
            <p>AI-powered code reviews automatically posted on your GitHub Pull Requests.
            Powered by Groq AI and Llama 3.3.</p>
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <h3>Instant Reviews</h3>
                    <p>Get AI review seconds after opening a PR</p>
                </div>
                <div class="feature">
                <div class="feature-icon">📊</div>
                    <h3>Score & Insights</h3>
                    <p>Every PR gets scored and tracked over time</p>
                </div>
            </div>
            <a href="/dashboard" class="btn">View Dashboard →</a>
        </div>
    </body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    reviews = get_all_reviews()

    total = len(reviews)
    scores = [extract_score(r.review_text) for r in reviews]
    valid_scores = [s for s in scores if s is not None]
    avg_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else None
    repos = len(set(r.repo_name for r in reviews))

    rows = ""
    for r, score in zip(reviews, scores):
        color = score_color(score)
        label = score_label(score)
        score_display = f"{score}/10" if score else "N/A"
        rows += f"""
        <tr>
            <td><span style="color:#58a6ff">#{r.pr_number}</span></td>
            <td>{r.repo_name}</td>
            <td>{r.pr_title}</td>
            <td>@{r.author}</td>
            <td>
                <span style="background:{color};color:white;padding:3px 10px;
                border-radius:12px;font-size:13px;font-weight:600">
                    {score_display} {label}
                </span>
            </td>
            <td>{r.created_at.strftime("%Y-%m-%d %H:%M")}</td>
            <td><a href="/review/{r.id}" style="color:#58a6ff">View →</a></td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='7' style='text-align:center;padding:40px;color:#8b949e'>No reviews yet. Open a PR to get started!</td></tr>"

    avg_display = f"{avg_score}/10" if avg_score else "N/A"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PR Review Copilot Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0d1117;
                color: #c9d1d9;
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 32px;
                border-bottom: 1px solid #30363d;
                padding-bottom: 20px;
            }}
            .header h1 {{ color: #58a6ff; font-size: 28px; }}
            .header a {{
                margin-left: auto;
                color: #8b949e;
                text-decoration: none;
                font-size: 14px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 32px;
            }}
            .stat-card {{
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 24px;
                text-align: center;
            }}
            .stat-number {{
                font-size: 42px;
                font-weight: 700;
                color: #58a6ff;
                margin-bottom: 8px;
            }}
            .stat-label {{
                color: #8b949e;
                font-size: 14px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
                overflow: hidden;
            }}
            th {{
                background: #21262d;
                padding: 14px 16px;
                text-align: left;
                color: #8b949e;
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid #30363d;
            }}
            td {{
                padding: 14px 16px;
                border-bottom: 1px solid #21262d;
                font-size: 14px;
            }}
            tr:last-child td {{ border-bottom: none; }}
            tr:hover td {{ background: #1c2128; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span style="font-size:28px">🤖</span>
                <h1>PR Review Copilot</h1>
                <a href="/">← Home</a>
            </div>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">Total Reviews</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{avg_display}</div>
                    <div class="stat-label">Average Score</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{repos}</div>
                    <div class="stat-label">Repositories</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>PR</th>
                        <th>Repository</th>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Score</th>
                        <th>Reviewed At</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
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

        score = extract_score(review.review_text)
        color = score_color(score)
        score_display = f"{score}/10" if score else "N/A"

        formatted = review.review_text.replace('\n', '<br>')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Review #{review.pr_number}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #0d1117;
                    color: #c9d1d9;
                    padding: 40px 20px;
                }}
                .container {{ max-width: 900px; margin: 0 auto; }}
                .back {{
                    color: #58a6ff;
                    text-decoration: none;
                    font-size: 14px;
                    display: inline-block;
                    margin-bottom: 24px;
                }}
                .pr-header {{
                    background: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 12px;
                    padding: 24px;
                    margin-bottom: 24px;
                }}
                .pr-title {{
                    font-size: 22px;
                    font-weight: 700;
                    color: #e6edf3;
                    margin-bottom: 12px;
                }}
                .pr-meta {{
                    display: flex;
                    gap: 16px;
                    flex-wrap: wrap;
                    align-items: center;
                }}
                .meta-item {{
                    color: #8b949e;
                    font-size: 14px;
                }}
                .score-badge {{
                    background: {color};
                    color: white;
                    padding: 4px 14px;
                    border-radius: 20px;
                    font-weight: 700;
                    font-size: 15px;
                }}
                .review-box {{
                    background: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 12px;
                    padding: 28px;
                    line-height: 1.8;
                    font-size: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/dashboard" class="back">← Back to Dashboard</a>
                <div class="pr-header">
                    <div class="pr-title">#{review.pr_number} — {review.pr_title}</div>
                    <div class="pr-meta">
                        <span class="meta-item">📁 {review.repo_name}</span>
                        <span class="meta-item">👤 @{review.author}</span>
                        <span class="meta-item">🕐 {review.created_at.strftime("%Y-%m-%d %H:%M")}</span>
                        <span class="score-badge">📊 {score_display}</span>
                    </div>
                </div>
                <div class="review-box">{formatted}</div>
            </div>
        </body>
        </html>
        """
        return html
    finally:
        db.close()