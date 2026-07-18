import os
from werkzeug.utils import secure_filename
from utils.ai_feedback import analyze_resume
from utils.ats_score import calculate_ats_score
from utils.pdf_report import create_pdf
from utils.resume_parser import extract_text_from_pdf
from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import get_db_connection

# ========= Flask App Configuration ========== #

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["SECRET_KEY"] = "resume_analyzer_secret_key"

# ========= Home Route ========== #

@app.route("/")
def home():
    return render_template("index.html")

# ========== Login Route ========== #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]

            return redirect("/dashboard")

        flash("Invalid Email or Password")

    return render_template("login.html")

# ========== Register Route ========== #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users(fullname,email,password)
            VALUES(%s,%s,%s)
            """,
            (fullname, email, password)
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Registration Successful!")

        return redirect("/login")

    return render_template("register.html")

# ========= Dashboard Route ========== #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total resumes analyzed
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM analysis_history
        WHERE user_id = %s
    """, (session["user_id"],))
    total = cursor.fetchone()["total"]

    # Average ATS score
    cursor.execute("""
        SELECT AVG(ats_score) AS average
        FROM analysis_history
        WHERE user_id = %s
    """, (session["user_id"],))
    average = cursor.fetchone()["average"] or 0

    # Highest ATS score
    cursor.execute("""
        SELECT MAX(ats_score) AS highest
        FROM analysis_history
        WHERE user_id = %s
    """, (session["user_id"],))
    highest = cursor.fetchone()["highest"] or 0

    # Recent analyses
    cursor.execute("""
        SELECT resume_name, ats_score
        FROM analysis_history
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 5
    """, (session["user_id"],))
    recent = cursor.fetchall()
    
    # Data for ATS Score Trend Chart
    chart_labels = [item["resume_name"] for item in recent][::-1]
    chart_scores = [item["ats_score"] for item in recent][::-1]
    cursor.close()
    conn.close()

    return render_template(
     "dashboard.html",
     name=session["fullname"],
     total=total,
     average=round(average),
     highest=highest,
     recent=recent,
     chart_labels=chart_labels,
     chart_scores=chart_scores
    )
# ======== Logout Route ========== #

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/test")
def test():
    return "Test Route Working"

# ======== Upload Resume Route ========== #

@app.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        file = request.files["resume"]
        job_description = request.form["job_description"]

        if file:

            filename = secure_filename(file.filename)

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            # Extract resume text
            extracted_text = extract_text_from_pdf(filepath)

            # AI Analysis
            ai_feedback = analyze_resume(
                extracted_text,
                job_description
            )

            # ATS Score
            score, matched, missing = calculate_ats_score(
                extracted_text,
                job_description
            )

            # ---------------- PDF Report ----------------
            pdf_folder = "static/reports"
            os.makedirs(pdf_folder, exist_ok=True)

            pdf_filename = f"{os.path.splitext(filename)[0]}_report.pdf"
            pdf_path = os.path.join(pdf_folder, pdf_filename)

            create_pdf(
                pdf_path,
                score,
                ai_feedback
            )
            # --------------------------------------------

            # Save to database
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO analysis_history
                (user_id, resume_name, ats_score, ai_feedback)
                VALUES (%s, %s, %s, %s)
            """, (
                session["user_id"],
                filename,
                score,
                ai_feedback
            ))

            conn.commit()
            cursor.close()
            conn.close()

            return render_template(
                "result.html",
                ats_score=score,
                matched=matched,
                missing=missing,
                resume_text=extracted_text,
                ai_feedback=ai_feedback,
                pdf_file=pdf_filename
            )

    return render_template("upload_resume.html")

# ========== History Route ========== #

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        cursor.execute("""
            SELECT *
            FROM analysis_history
            WHERE user_id=%s
            AND resume_name LIKE %s
            ORDER BY id DESC
        """, (session["user_id"], f"%{search}%"))
    else:
        cursor.execute("""
            SELECT *
            FROM analysis_history
            WHERE user_id=%s
            ORDER BY id DESC
        """, (session["user_id"],))

    analyses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        analyses=analyses,
        search=search
    )

# ========= View Analysis Route ========= #

@app.route("/view_analysis/<int:id>")
def view_analysis(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM analysis_history
        WHERE id=%s AND user_id=%s
    """, (id, session["user_id"]))

    analysis = cursor.fetchone()

    cursor.close()
    conn.close()

    if not analysis:
        flash("Analysis not found.")
        return redirect("/history")

    return render_template(
        "view_analysis.html",
        analysis=analysis
    )

# ========= Delete History Route ========== #
@app.route("/delete_history/<int:id>")
def delete_history(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM analysis_history
        WHERE id=%s AND user_id=%s
    """, (id, session["user_id"]))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/history")

@app.route("/test123")
def test123():
    return "OK"

if __name__ == "__main__":
    app.run(debug=True)