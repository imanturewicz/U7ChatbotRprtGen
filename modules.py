import os
import subprocess
import jinja2
import json

def generate_pdf_from_template(env, template_name, context, output_dir, output_filename):
    """
    Renders a LaTeX template and compiles it to PDF.
    
    Args:
        env (jinja2.Environment): The configured Jinja2 environment.
        template_name (str): The name of the .tex template file.
        context (dict): The dictionary of variables to render.
        output_dir (str): Where to save the output.
        output_filename (str): The name of the file (without extension).
    """
    
    # 1. Render the template
    try:
        template = env.get_template(template_name)
        rendered_tex = template.render(context)

        # Add ChkTeX directives at the top of the rendered .tex to suppress specific warnings
        header = "% chktex-file 8\n% chktex-file 44\n\n"
        rendered_tex = header + rendered_tex
    except jinja2.TemplateError as e:
        print(f"❌ Jinja Error: {e}")
        return

    # 2. Write the .tex file
    tex_path = os.path.join(output_dir, f"{output_filename}.tex")
    with open(tex_path, "w") as f:
        f.write(rendered_tex)

    print(f"Compiling PDF for {output_filename}...")

    # 3. Compile PDF
    # We use cwd=output_dir so we don't have to os.chdir() globally
    try:
        subprocess.run(
            ["pdflatex", f"{output_filename}.tex"], 
            cwd=output_dir, 
            check=True,
            stdout=subprocess.DEVNULL  # Optional: Silence the noisy LaTeX logs
        )
        
        # 4. Cleanup Aux files
        for ext in [".aux", ".log", ".out"]:
            temp_file = os.path.join(output_dir, f"{output_filename}{ext}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        print(f"🎉 Done! Check {os.path.join(output_dir, output_filename)}.pdf")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PDF Compilation Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def filter_sensible_transcripts(transcripts_list):
    """
    Filters a list of transcripts, keeping only those where the 
    evaluation 'CzySensowna' is True.
    """
    print(f"🕵️  Filtering 'CzySensowna' conversations from {len(transcripts_list)} transcripts...")
    
    sensible_list = []
    
    for t in transcripts_list:
        evaluations = t.get("evaluations", [])
        
        # We need to find the specific evaluation inside the list
        is_sensible = False
        
        for evaluation in evaluations:
            if evaluation.get("name") == "CzySensowna":
                raw_value = evaluation.get("value")
                
                # Robust Check: specific for string "true" OR boolean True
                # str(raw_value) turns True -> "True" and "true" -> "true"
                if str(raw_value).lower() == "true":
                    is_sensible = True
                break
        
        # Decision time
        if is_sensible:
            sensible_list.append(t)

    print(f"✅ Filter Complete. Kept {len(sensible_list)} sensible transcripts (Dropped {len(transcripts_list) - len(sensible_list)}).")
    return sensible_list

def process_voiceflow_categories(transcripts_list):
    """
    1. Extracts 'Kategoryzacja' value and 'reason' from Voiceflow transcripts.
    2. Merges top 3 specific categories into "Pytania o rezerwacje i promocje".
    3. Selects the Top X remaining specific categories.
    4. Moves everything else (plus explicit 'Inne') to a catch-all bucket.
    5. Saves reasons for the 'Inne' bucket to a text file.
    """
    print(f"📊 [Categorization] Processing {len(transcripts_list)} transcripts from Voiceflow tags...")

    # --- CONFIGURATION ---
    # 1. The "Mega Category" (These 3 get merged)
    MEGA_GROUP_NAME = "Pytania o rezerwacje i promocje"
    MEGA_GROUP_KEYS = [
        "Rezerwacja kręgli lub bilarda na dzisiaj lub na jutro",
        "Rezerwacja na konkretny, przyszły termin",
        "Promocje lub kod rabatowy"
    ]

    # --- DATA COLLECTION ---
    # Dictionary to hold raw counts: { "Category Name": 5 }
    raw_counts = {}
    # Dictionary to hold reasons: { "Category Name": ["User asked X", "User asked Y"] }
    raw_reasons = {}

    for t in transcripts_list:
        evals = t.get("evaluations", [])
        
        # Find the specific 'Kategoryzacja' evaluation
        category_found = None
        reason_found = "Brak uzasadnienia (No reason provided)"

        for e in evals:
            if e.get("name") == "Kategoryzacja":
                # We found the tag!
                val = e.get("value") # The category name
                reas = e.get("reason") # The explanation
                
                if val:
                    category_found = str(val).strip()
                if reas:
                    reason_found = str(reas).strip()
                break
        
        # If no tag found, skip (or count as strict error/omission)
        if not category_found:
            continue

        # Initialize if new
        if category_found not in raw_counts:
            raw_counts[category_found] = 0
            raw_reasons[category_found] = []
        
        # Increment
        raw_counts[category_found] += 1
        raw_reasons[category_found].append(reason_found)

    # --- AGGREGATION LOGIC ---
    
    final_report_data = {}
    inne_bucket_reasons = [] # Will hold lines for the text file

    # 1. Process Mega Group
    mega_count = 0
    for key in MEGA_GROUP_KEYS:
        count = raw_counts.get(key, 0)
        mega_count += count
        # Note: We usually don't put these reasons in the text file as they are "Sorted"
    
    final_report_data[MEGA_GROUP_NAME] = mega_count

    # 2. Process Candidates for Top X
    # We filter out the Mega Keys and "Inne" (handled separately)
    candidates = []
    for cat, count in raw_counts.items():
        if cat not in MEGA_GROUP_KEYS and cat != "Inne":
            candidates.append((cat, count))
    
    # Sort by count descending
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Split into Top X and Leftovers
    split = 6
    top_cats = candidates[:split]
    leftovers = candidates[split:]

    # Add Top X to report
    for cat, count in top_cats:
        final_report_data[cat] = count

    # 3. Process "Inne" (Explicit Inne + Leftovers)
    total_inne_count = raw_counts.get("Inne", 0)
    
    # A. Get reasons from explicit "Inne"
    if "Inne" in raw_reasons:
        for r in raw_reasons["Inne"]:
            inne_bucket_reasons.append(f"[KATEGORIA: Inne] {r}")

    # B. Get reasons from Leftovers (Categories that didn't make the cut)
    for cat, count in leftovers:
        total_inne_count += count
        # Add their reasons to the list, tagged with their original category name
        if cat in raw_reasons:
            for r in raw_reasons[cat]:
                inne_bucket_reasons.append(f"[KATEGORIA: {cat}] {r}")

    final_report_data["Inne"] = total_inne_count

    # --- WRITE TO FILE ---
    filename = "Inne_tematy_konweracji.txt"
    if inne_bucket_reasons:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"=== SZCZEGÓŁY KATEGORII 'INNE' (Łącznie: {total_inne_count}) ===\n")
            f.write(f"Tutaj znajdują się rozmowy z kategorii 'Inne' oraz kategorie, które nie zmieściły się w TOP {split}.\n\n")
            for line in inne_bucket_reasons:
                f.write(f"- {line}\n")
        print(f"💾 Saved {len(inne_bucket_reasons)} reasons to '{filename}'")
    else:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Brak nietypowych tematów.")
        print("ℹ️ File created (empty).")

    return final_report_data

def format_report_range(start_dt, end_dt):
    # Get basic parts
    polish_months_genitive = {
        1: "Stycznia",
        2: "Lutego",
        3: "Marca",
        4: "Kwietnia",
        5: "Maja",
        6: "Czerwca",
        7: "Lipca",
        8: "Sierpnia",
        9: "Września",
        10: "Października",
        11: "Listopada",
        12: "Grudnia"
    }
    start_day = start_dt.day
    start_month = polish_months_genitive[start_dt.month]
    end_day = end_dt.day
    end_month = polish_months_genitive[end_dt.month]
    
    # Logic: Check if years are the same
    if start_dt.year == end_dt.year:
        # Same year: "1 Grudnia - 31 Grudnia 2025"
        return f"{start_day} {start_month} - {end_day} {end_month} {end_dt.year}"
    else:
        # Different years: "1 Grudnia 2025 - 31 Stycznia 2026"
        return f"{start_day} {start_month} {start_dt.year} - {end_day} {end_month} {end_dt.year}"