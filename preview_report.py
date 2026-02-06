import jinja2
import os
import subprocess

# 1. SETUP THE JINJA ENVIRONMENT
template_loader = jinja2.FileSystemLoader(searchpath="./")
template_env = jinja2.Environment(
    block_start_string=r'\BLOCK{',
    block_end_string=r'}',
    variable_start_string=r'\VAR{',
    variable_end_string=r'}',
    comment_start_string=r'\#{',
    comment_end_string=r'}',
    loader=template_loader,
    autoescape=False
)

# 2. DEFINE FAKE/TEST DATA (Matches your real variables)
context = {
    "title_var": "PREVIEW REPORT",
    "report_date": "2026-02-06",
    "project_id": "TEST_PROJECT_ID",
    "status": "Preview Mode",
    "unique_users": 1250,
    
    # Traffic & Filtering
    "sensible_count": 850,
    "num_good": 700,
    "num_bad": 50,
    # Neutral is calculated in template: 850 - 700 - 50 = 100
    
    # Topic Data for Pie Chart
    "topic_counts": {
        "Pytania o rezerwacje i promocje": 450,
        "Godziny Otwarcia": 150,
        "Cennik": 100,
        "Urodziny": 50,
        "Inne": 100
    }
}

# 3. RENDER THE TEMPLATE
template_file = "reportTemplate.tex.j2" # <--- Your template filename
template = template_env.get_template(template_file)
output_tex = "preview_output.tex"

with open(output_tex, "w", encoding="utf-8") as f:
    f.write(template.render(context))

# 4. COMPILE TO PDF (Runs pdflatex automatically)
print("Compiling PDF...")
try:
    # Run pdflatex twice to ensure charts/layout stabilize
    subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True, stdout=subprocess.DEVNULL)
    print(f"✅ Success! Generated {output_tex.replace('.tex', '.pdf')}")
except subprocess.CalledProcessError:
    print("❌ Error during LaTeX compilation. Check 'preview_output.log' for details.")
except FileNotFoundError:
    print("❌ Error: 'pdflatex' command not found. Do you have a LaTeX distribution installed?")