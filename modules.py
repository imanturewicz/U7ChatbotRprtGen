import os
import subprocess
import jinja2

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
        for ext in [".aux", ".log", ".out", ".tex"]: # Added .tex to cleanup if you want
            temp_file = os.path.join(output_dir, f"{output_filename}{ext}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        print(f"🎉 Done! Check {os.path.join(output_dir, output_filename)}.pdf")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PDF Compilation Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")