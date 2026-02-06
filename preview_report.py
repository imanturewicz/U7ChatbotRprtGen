import sys
import jinja2
import os
import subprocess
import modules
from datetime import datetime

# 1. SETUP THE JINJA ENVIRONMENT
template_loader = jinja2.FileSystemLoader(searchpath="./")
template_env = jinja2.Environment(
    block_start_string=r'\BLOCK{',
    block_end_string='}',           # Removed 'r' prefix to match main
    variable_start_string=r'\VAR{',
    variable_end_string='}',        # Removed 'r' prefix to match main
    comment_start_string=r'\#{',
    comment_end_string='}',         # Removed 'r' prefix to match main
    trim_blocks=True,               # <--- THIS WAS MISSING
    autoescape=False,
    loader=template_loader
)

# 2. DEFINE FAKE/TEST DATA (Matches your real variables)
context = {
    # Header Data
    "title_var": "Raport z Działania Chatbota U7 AI",
    "period": "1 Grudnia - 31 Grudnia 2025",
    "period_short": "01.12 - 31.12", # Used in the metric subheader
    
    # Section 1: Overview Text (The text paragraph from your screenshot)
    "overview_text": "Kolejny miesiąc działania chatbota U7 przebiegł pomyślnie",

    # Key Metrics Table Data
    "unique_users": "120",  # Formatted as string for spacing if needed
    "interactions": "230",
    "sensible_count": 200,
    "avg_duration": "100 sekund",
    "firm_forms": 5,
    "bday_forms": 0,
    
    # Data for Pie Charts (Keeping these for later sections)
    "num_good": 190,
    "num_bad": 5,
    # Neutral calculated in template
    
    "topics_text": "Najczęstszymi zapytaniami pozostają te dotyczące rezerwacji oraz promocji.",
    "topic_counts": {
        "Pytania o rezerwacje": 450,
        "Godziny Otwarcia": 150,
        "Cennik": 100,
        "Urodziny": 50,
        "Inne": 100
    },

    "quality_text": "Jakość odpowiedzi chatbota utrzymuje się na wysokim poziomie.",

    "generation_date": datetime.now().strftime("%d.%m.%Y"), 
    "author_name": "Ignacy Manturewicz"
}

script_dir = os.path.dirname(os.path.abspath(__file__))

modules.generate_pdf_from_template(
    env=template_env,
    template_name='reportTemplate.tex.j2',
    context=context,
    output_dir=script_dir,
    output_filename="preview_report"
)

# sys.exit("STOPPING SCRIPT FOR TESTING")
