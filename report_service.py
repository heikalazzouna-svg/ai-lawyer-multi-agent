import os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from langchain_core.messages import AIMessage

def generate_report(user_queries: list[str], ai_responses: list[AIMessage | str]) -> str:
    """
    Generate a downloadable Microsoft Word (.docx) report of the user's conversation 
    with the AI Lawyer.

    Args:
        user_queries (list[str]): The list of questions the user asked.
        ai_responses (list[AIMessage | str]): The corresponding responses from the AI.

    Returns:
        str: The local file path to the generated DOCX report.
    """
    docx_path = "AI_Lawyer_Report.docx"
    
    # Create a new Word document
    doc = Document()
    
    # Title
    title = doc.add_heading('AI Lawyer Consultation Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Subtitle
    subtitle = doc.add_paragraph('Below is a verified record of your conversation with the AI Lawyer.')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph('_' * 60) # Divider
    
    for question, answer in zip(user_queries, ai_responses):
        # Extract string content if answer is an AIMessage object
        answer_text = str(answer.content) if hasattr(answer, 'content') else str(answer)
        
        # User Question
        q_heading = doc.add_heading(level=2)
        q_run = q_heading.add_run("Q: " + question)
        q_run.font.size = Pt(12)
        
        # AI Answer
        a_paragraph = doc.add_paragraph()
        a_run = a_paragraph.add_run("AI Lawyer:\n")
        a_run.bold = True
        a_paragraph.add_run(answer_text)
        
        # Spacing
        doc.add_paragraph()
        
    # Save the document
    doc.save(docx_path)
    return docx_path
