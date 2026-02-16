import os
import sys
import jinja2
from datetime import datetime
from zoneinfo import ZoneInfo

import voiceflow_api
import convocore_api
import modules
import secrets
import config

# --- CONFIGURATION ---
OPENAI_KEY = secrets.OPENAI_API_KEY

VF_API_KEY = secrets.VOICEFLOW_API_KEY
VF_PROJECT_ID = secrets.VOICEFLOW_PROJECT_ID
VF_ENV_ID = secrets.VOICEFLOW_ENVIRONMENT_ID
vf_client = voiceflow_api.VoiceflowClient(VF_API_KEY, VF_PROJECT_ID)

CONVO_API_KEY = secrets.CONVOCORE_API_KEY
CONVO_AGENT_ID = secrets.CONVOCORE_AGENT_ID

#Set the report period as needed
#                       YYYY, M, D, h, m, s, UTC
REPORT_START = datetime(2026, 2, 1, 0, 0, 0, tzinfo=ZoneInfo("Europe/Warsaw"))
REPORT_END   = datetime(2026, 2, 14, 23, 59, 59, tzinfo=ZoneInfo("Europe/Warsaw"))

print(f"🚀 Generating Report: {REPORT_START.date()} to before {REPORT_END.date()}")

# --- FETCH VOICEFLOW DATA ---
vf_users = vf_client.get_unique_users__or_interactions(REPORT_START, REPORT_END, metric="unique_users")
print(f"✅ [Voiceflow] Users found: {vf_users}")

vf_interactions = vf_client.get_unique_users__or_interactions(REPORT_START, REPORT_END, metric="interactions")
print(f"✅ [Voiceflow] Interactions found: {vf_interactions}")
# sys.exit("STOPPING SCRIPT FOR TESTING")

print("Downloading transcripts...")
transcripts_list = list(vf_client.fetch_transcripts(REPORT_START, REPORT_END, VF_ENV_ID))
print(f"✅ Downloaded {len(transcripts_list)} transcripts.")

voiceflow_api.end_active_transcripts(vf_client, transcripts_list) # If transcripts are still stuck

sensible_transcripts = modules.filter_sensible_transcripts(transcripts_list)
print(f"✅ Filtered down to {len(sensible_transcripts)} sensownych transcripts.")

topic_counts = modules.process_voiceflow_categories(sensible_transcripts)
print("\n📊 FINAL CATEGORIZATION FOR REPORT:")
for cat, count in topic_counts.items():
    print(f"   📂 {cat}: {count}")

# --- FETCH CONVOCORE DATA ---
convo_goodExample_tags = convocore_api.getConvocoreTagsNo(CONVO_API_KEY, CONVO_AGENT_ID, REPORT_START, REPORT_END, "Good Example")
convo_badExample_tags = convocore_api.getConvocoreTagsNo(CONVO_API_KEY, CONVO_AGENT_ID, REPORT_START, REPORT_END, "Bad Example")
convo_Neutral_tags = convocore_api.getConvocoreTagsNo(CONVO_API_KEY, CONVO_AGENT_ID, REPORT_START, REPORT_END, "Neutral")

# --- GENERATE PDF ---
script_dir = os.path.dirname(os.path.abspath(__file__))

context = {
    # Header Data
    "title_var": config.title_var,
    "period": modules.format_report_range(REPORT_START, REPORT_END),
    # "period_short": "01.12 - 31.12", # Used in the metric subheader
    
    # Section 1: Overview Text (The text paragraph from your screenshot)
    "overview_text": config.overview_text,

    # Key Metrics Table Data
    "unique_users": vf_users,  # Formatted as string for spacing if needed
    "interactions": vf_interactions,
    #"sensible_count": len(sensible_transcripts),       #legacy metric, can be removed if we fully switch to convo tags as proxy for sensible interactions
    "sensible_count": convo_goodExample_tags + convo_badExample_tags + convo_Neutral_tags, # Using convo tags as proxy for sensible interactions
    "avg_duration": config.avg_duration,
    "firm_forms": config.firm_forms,
    "bday_forms": config.bday_forms,
    
    # Data for Pie Charts (Keeping these for later sections)
    "num_good": convo_goodExample_tags,
    "num_bad": convo_badExample_tags,
    "num_neutral": convo_Neutral_tags,
    # Neutral calculated in template
    
    "topics_text": config.topics_text,
    "topic_counts": topic_counts,  # Pass the topic counts for the pie chart

    "quality_text": config.quality_text,

    "generation_date": datetime.now().strftime("%d.%m.%Y"), 
    "author_name": "Ignacy Manturewicz"
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
    template_name='reportTemplate.tex.j2',
    context=context,
    output_dir=script_dir,
    output_filename="monthlyReport"
)