from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def create_pdf(filename, ats_score, feedback):
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("<b>AI Resume Analyzer Report</b>", styles["Title"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    elements.append(Paragraph(f"<b>ATS Score:</b> {ats_score}%", styles["Heading2"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    feedback = feedback.replace("\n", "<br/>")
    elements.append(Paragraph(feedback, styles["BodyText"]))

    doc.build(elements)