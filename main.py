import os
import jinja2
from datetime import datetime, timezone

import voiceflow_api
import convocore_api
import modules
import secrects

# --- CONFIGURATION ---
VF_API_KEY = secrects.VOICEFLOW_API_KEY
VF_PROJECT_ID = secrects.VOICEFLOW_PROJECT_ID

CONVO_API_KEY = secrects.CONVOCORE_API_KEY
CONVO_AGENT_ID = secrects.CONVOCORE_AGENT_ID

#                       YYYY, m, D, h, M, s, UTC
REPORT_START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
REPORT_END   = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

print(f"🚀 Generating Report: {REPORT_START.date()} to before {REPORT_END.date()}")

# --- FETCH VOICEFLOW DATA ---
vf_users = voiceflow_api.get_voiceflow_users(VF_API_KEY, VF_PROJECT_ID, REPORT_START, REPORT_END)
print(f"✅ [Voiceflow] Users found: {vf_users}")

# --- FETCH CONVOCORE DATA ---
convo_goodExample_tags = convocore_api.getConvocoreTagsNo(CONVO_API_KEY, CONVO_AGENT_ID, REPORT_START, REPORT_END, "Good Example")
convo_badExample_tags = convocore_api.getConvocoreTagsNo(CONVO_API_KEY, CONVO_AGENT_ID, REPORT_START, REPORT_END, "Bad Example")

# --- GENERATE PDF ---
script_dir = os.path.dirname(os.path.abspath(__file__))

context = {
    "title_var": "Monthly Integrated Report",
    "report_date": datetime.now().strftime("%B %d, %Y"),
    "period_start": REPORT_START.strftime("%Y-%m-%d"),
    "period_end": REPORT_END.strftime("%Y-%m-%d"),
    "unique_users": vf_users,
    "num_good_examples": convo_goodExample_tags,
    "num_bad_examples": convo_badExample_tags
}

latex_env = jinja2.Environment(
    block_start_string=r'\BLOCK{',
    block_end_string='}',
    variable_start_string=r'\VAR{',
    variable_end_string='}',
    comment_start_string=r'\#{',
    comment_end_string='}',
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(script_dir)
)

modules.generate_pdf_from_template(
    env=latex_env,
    template_name='reportTemplate.tex',
    context=context,
    output_dir=script_dir,
    output_filename="monthlyReport"
)