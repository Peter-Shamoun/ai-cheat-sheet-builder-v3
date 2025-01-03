from flask import Flask, Response, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI
from pydantic import BaseModel
import base64
import os
import subprocess
import tempfile
import PyPDF2
from io import BytesIO
import ast

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

@app.route('/pdf/extract', methods=['POST'])
def extract_text():
    try:
        if 'file' not in request.files:
            return 'No file provided', 400

        file = request.files['file']
        
        # Check if a file was actually selected
        if file.filename == '':
            return 'No file selected', 400

        # Check if it's a PDF
        if not file.filename.lower().endswith('.pdf'):
            return 'File must be a PDF', 400

        # Read the PDF file
        pdf_bytes = file.read()
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        
        # Extract text from all pages
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text() or ''

        return text, 200

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return f'Error processing PDF: {str(e)}', 500

@app.route('/topics', methods=['POST'])
def process_topics():
    try:
        data = request.get_json()
        if not data or 'text_list' not in data:
            return 'No text_list provided in request body', 400

        # Get the text_list from the request
        text_list = data['text_list']
        
        # If it's not already a list, try to convert it
        if not isinstance(text_list, list):
            try:
                text_list = list(text_list)
            except:
                return 'Could not convert text_list to list', 400

        # Return the count of entries as a string
        text_list = text_list

        all_topics = []
        
        for text in text_list:
            class Topic_Scope(BaseModel):
                topic: str
                scope: list[str]

            class Topic_Output(BaseModel):
                topics: list[Topic_Scope]
            
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": """
                    
                    You are an expert assistant creating study materials for students.

                    Task: Analyze the provided text and extract key topics likely to appear on exams.


                    Rules:
                    - Identify core testable concepts
                    - Include ALL IMPORTANT academic keywords per topic that are in the topic's scope in the text
                    - Focus on exam-critical material
                    - Use precise technical terminology
                    - TAKE ALL THE TIME NEEDED TO PERFORM THE TASK

                    Format:
                    {
                        "topics": [
                            {
                                "topic": "Topic Name",
                                "scope": ["keyword1", "keyword2", "keyword3", "keyword4"]
                            }
                        ]
                    }

                    """},


                    {"role": "user", "content": f"{text}"},
                ],
                max_completion_tokens = 10_000, #non max because i want them to upload up to 10 files
                response_format=Topic_Output,
            )

            event = completion.choices[0].message.parsed
            all_topics.append(event)

        def output_to_input(output):
            json_dict = []

            for i in range(len(output)):
                document_topic_output = output[i]

                document_topic_output_dict = {'topics': []}


                for topic in document_topic_output.topics:
                    temp_dict = {}
                    temp_dict['topic'] = topic.topic
                    temp_dict['scope'] = topic.scope
                    document_topic_output_dict['topics'].append(temp_dict)


                json_dict.append(document_topic_output_dict)
            
            return json_dict
        t_list = output_to_input(all_topics)


        text = str(t_list)

        return text, 200

    except Exception as e:
        print(f"Error processing text list: {str(e)}")
        return f'Error processing text list: {str(e)}', 500

@app.route('/topics/summarize', methods=['POST'])
def summarize_topics():
    try:
        data = request.get_json()
        if not data or 'topic_list' not in data:
            return 'No topic_list provided in request body', 400

        # Get the topic_list string from the request and return it
        topic_list = data['topic_list']
        text = topic_list

        class Topic_Scope(BaseModel):
            topic: str
            scope: list[str]
        class Topic_Output(BaseModel):
            topics: list[Topic_Scope]

        completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": """
            
            You are an expert in designing study materials for exams. 
            There will be an exam given on the topics from the proivded text.
            Your task is to analyze the provided text and identify the twelve (12)
            THERE MUST BE TWELVE TOPICS  
            most fundamental concepts that are likely to appear on an exam, 
            considering the curriculum topics and their scope.

            Evaluation Criteria for Concepts:

            Foundational Importance: Concepts that form the basis for understanding other topics.
            Practical Application: Concepts with the widest and most frequent applications.
            Cross-Referencing: Topics frequently referenced across different areas of the curriculum.
            Subject Core: Essential for a comprehensive understanding of the subject.
            Output Requirements:

            List exactly 12 concepts based on their exam prevelance importance. THERE MUST BE TWELVE TOPICS

            
            Example Format:

            topic: Thermodynamics scope: ["keyword1", "keyword2", "keyword3", "keyword4" ...]
            topic: Kinetics scope: ["keyword1", "keyword2", "keyword3", "keyword4" ...]

            TAKE ALL THE TIME NEEDED TO PERFORM THE TASK. THERE MUST BE TWELVE TOPICS
            """},


            {"role": "user", "content": f"{text}"},
        ],
        temperature = 0.2,
        max_completion_tokens = 1000, #Only want 12 topics
        response_format=Topic_Output,
        )

        event = completion.choices[0].message.parsed


        topic_lst = []
        for i in range(12):
            topic_dict = {}
            topic = event.topics[i].topic
            scope  = event.topics[i].scope
            topic_dict[topic] = scope
            topic_lst.append(topic_dict)

        return str(topic_lst), 200

    except Exception as e:
        print(f"Error processing topic list: {str(e)}")
        return f'Error processing topic list: {str(e)}', 500

@app.route('/latex', methods=['POST'])
def generate_latex():
    try:
        data = request.get_json()
        if not data or 'topic_twelve' not in data:
            print("Missing topic_twelve in request data")
            return 'No topic_twelve provided in request body', 400

        # Get the topic_twelve string
        topic_twelve_str = data['topic_twelve']
        print("Received topic_twelve:", topic_twelve_str)  # Debug print
        
        try:
            # Try to convert string to list
            topic_list = ast.literal_eval(topic_twelve_str)
            print("Converted to list:", topic_list)  # Debug print
        except Exception as e:
            print(f"Conversion error: {str(e)}")
            # If conversion fails, just use the string as is
            topic_list = topic_twelve_str

        # Example LaTeX content - using the actual topics if possible
        ex_1 = r""" 
        heading: Scatter Plot
        latex_code: Relationship between two variables
        """
        ex_2 = r""" 
        heading: $\mathbb{E}(X)$
        latex_code: $\sum_{x \in \text{supp}(X)} x \times p_X(x)$\\
        """
        ex_3 = r""" 
        heading: quartile
        latex_code: For $0 \leq \alpha \leq 1$, the $\alpha$-quantile of $x_1, x_2, \ldots, x_n$ is the value for which at least an $\alpha$ fraction of the points have a value less than or equal to it.
        """

        latex_lst = []

        for i in topic_list:

            class Heading(BaseModel):
                heading: str
                latex_content: str
            class Heading_Latex(BaseModel):
                headings: list[Heading]

            completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": f"""
                
                You are an expert in designing effective study materials for exams. 
                Your task is to create exactly FIVE (5) key headings and their corresponding 
                segments of LaTeX text based on the most critical topics from the provided text.

                Requirements:
                DO NOT USER ANY UNDERSCORES
                YOU MUST GO BEYOND MEER DEFINITIONS AND PROVIDE INFO THAT WILL HELP ANSWER QUESTIONS ON AN EXAM

                Headings: Identify the five most essential topics in the provided material. Each heading should concisely reflect its subject matter.
                LaTeX Content: For each heading, include one line of LaTeX text that summarizes or conveys key information about the topic.
                Formatting:
                Do not include begin document or end document tags.
                DO NOT USER ANY UNDERSCORES
                Close all LaTeX environments properly (e.g., for equations or itemized lists).
                Example Output Format:
                {ex_1},{ex_2},{ex_3}
                Additional Notes:
                Use your expertise to determine the most critical topics and present them effectively.
                Take all the time needed to reason through the task and ensure the highest quality.
                Expectations:
                FIVE (5) HEADINGS
                Follow the format and ensure outputs are consistent.
                DO NOT USER ANY UNDERSCORES
                Use proper LaTeX syntax and close environments properly.
                Ensure headings and LaTeX content provide meaningful information for readers preparing for the exam.
                """},


                {"role": "user", "content": f"{str(i)}"},
            ],
            temperature = 0.2,
            max_completion_tokens = 1000, #Only want 5 pairs
            response_format=Heading_Latex,
            )

            event = completion.choices[0].message.parsed
            latex_lst.append(event)

        heading_mapping_dict = {
            '@@box1blank1title@@': None, '@@box1blank2title@@': None, '@@box1blank3title@@': None, '@@box1blank4title@@': None, '@@box1blank5title@@': None,
            '@@box2blank1title@@': None, '@@box2blank2title@@': None, '@@box2blank3title@@': None, '@@box2blank4title@@': None, '@@box2blank5title@@': None,
            '@@box3blank1title@@': None, '@@box3blank2title@@': None, '@@box3blank3title@@': None, '@@box3blank4title@@': None, '@@box3blank5title@@': None,
            '@@box4blank1title@@': None, '@@box4blank2title@@': None, '@@box4blank3title@@': None, '@@box4blank4title@@': None, '@@box4blank5title@@': None,
            '@@box5blank1title@@': None, '@@box5blank2title@@': None, '@@box5blank3title@@': None, '@@box5blank4title@@': None, '@@box5blank5title@@': None,
            '@@box6blank1title@@': None, '@@box6blank2title@@': None, '@@box6blank3title@@': None, '@@box6blank4title@@': None, '@@box6blank5title@@': None,
            '@@box7blank1title@@': None, '@@box7blank2title@@': None, '@@box7blank3title@@': None, '@@box7blank4title@@': None, '@@box7blank5title@@': None,
            '@@box8blank1title@@': None, '@@box8blank2title@@': None, '@@box8blank3title@@': None, '@@box8blank4title@@': None, '@@box8blank5title@@': None,
            '@@box9blank1title@@': None, '@@box9blank2title@@': None, '@@box9blank3title@@': None, '@@box9blank4title@@': None, '@@box9blank5title@@': None,
            '@@box10blank1title@@': None, '@@box10blank2title@@': None, '@@box10blank3title@@': None, '@@box10blank4title@@': None, '@@box10blank5title@@': None,
            '@@box11blank1title@@': None, '@@box11blank2title@@': None, '@@box11blank3title@@': None, '@@box11blank4title@@': None, '@@box11blank5title@@': None,
            '@@box12blank1title@@': None, '@@box12blank2title@@': None, '@@box12blank3title@@': None, '@@box12blank4title@@': None, '@@box12blank5title@@': None
        }

        fill_mapping_dict = {f"@@box{i}blank{j}fill@@": None for i in range(1, 13) for j in range(1, 6)}

        page_dict = {f"@@page{i}@@": None for i in range(1, 12)}

        for i in range(len(latex_lst)):
            for j in range(len(latex_lst[i].headings)):
                    key = f"@@box{i+1}blank{j+1}title@@"
                    heading_mapping_dict[key] = latex_lst[i].headings[j].heading

        for i in range(len(latex_lst)):
            for j in range(len(latex_lst[i].headings)):
                    key = f"@@box{i+1}blank{j+1}fill@@"
                    fill_mapping_dict[key] = latex_lst[i].headings[j].latex_content


        for i in range(len(topic_list)):
            key = f"@@page{i+1}@@"
            page_dict[key] = list(topic_list[i].keys())[0] 

        template = r""" 
        \documentclass{article}
        \usepackage[landscape]{geometry}
        \usepackage{url}
        \usepackage{multicol}
        \usepackage{amsmath}
        \usepackage{esint}
        \usepackage{amsfonts}
        \usepackage{tikz}
        \usetikzlibrary{decorations.pathmorphing}
        \usepackage{amsmath,amssymb}

        \usepackage{colortbl}
        \usepackage{xcolor}
        \usepackage{mathtools}
        \usepackage{amsmath,amssymb}
        \usepackage{enumitem}
        \makeatletter

        \newcommand*\bigcdot{\mathpalette\bigcdot@{.5}}
        \newcommand*\bigcdot@[2]{\mathbin{\vcenter{\hbox{\scalebox{#2}{$\m@th#1\bullet$}}}}}
        \makeatother

        \title{Title Cheat Sheet}
        \usepackage[brazilian]{babel}
        \usepackage[utf8]{inputenc}

        \advance\topmargin-.8in
        \advance\textheight3in
        \advance\textwidth3in
        \advance\oddsidemargin-1.5in
        \advance\evensidemargin-1.5in
        \parindent0pt
        \parskip2pt
        \newcommand{\hr}{\centerline{\rule{3.5in}{1pt}}}
        %\colorbox[HTML]{e4e4e4}{\makebox[\textwidth-2\fboxsep][l]{texto}
        \begin{document}

        \begin{center}{\huge{\textbf{Title Cheat Sheet}}}\\
        \end{center}
        \begin{multicols*}{3}

        \tikzstyle{mybox} = [draw=black, fill=white, very thick,
            rectangle, rounded corners, inner sep=10pt, inner ysep=10pt]
        \tikzstyle{fancytitle} =[fill=black, text=white, font=\bfseries]

        %------------ @@page1@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
        
                \textbf{@@box1blank1title@@:} @@box1blank1fill@@\\
                \textbf{@@box1blank2title@@:} @@box1blank2fill@@\\
                \textbf{@@box1blank3title@@:} @@box1blank3fill@@\\
                \textbf{@@box1blank4title@@:} @@box1blank4fill@@\\
                \textbf{@@box1blank5title@@:} @@box1blank5fill@@\\
                    
        \end{minipage}
        };
        %------------ @@page1@@  Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page1@@};
        \end{tikzpicture}

        %------------ @@page2@@  ---------------
        \begin{tikzpicture}
        \node [mybox] (box) {%
            \begin{minipage}{0.3\textwidth}
            \textbf{@@box2blank1title@@:} @@box2blank1fill@@\\
                \textbf{@@box2blank2title@@:} @@box2blank2fill@@\\
                \textbf{@@box2blank3title@@:} @@box2blank3fill@@\\
                \textbf{@@box2blank4title@@:} @@box2blank4fill@@\\
                \textbf{@@box2blank5title@@:} @@box2blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page2@@  Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page2@@};
        \end{tikzpicture}

        %------------ @@page3@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
            \textbf{@@box3blank1title@@:} @@box3blank1fill@@\\
                \textbf{@@box3blank2title@@:} @@box3blank2fill@@\\
                \textbf{@@box3blank3title@@:} @@box3blank3fill@@\\
                \textbf{@@box3blank4title@@:} @@box3blank4fill@@\\
                \textbf{@@box3blank5title@@:} @@box3blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page3@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page3@@};
        \end{tikzpicture}

        %------------ @@page4@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
                \textbf{@@box4blank1title@@:} @@box4blank1fill@@\\
                \textbf{@@box4blank2title@@:} @@box4blank2fill@@\\
                \textbf{@@box4blank3title@@:} @@box4blank3fill@@\\
                \textbf{@@box4blank4title@@:} @@box4blank4fill@@\\
                \textbf{@@box4blank5title@@:} @@box4blank5fill@@\\    \end{minipage}
        };
        %------------ @@page4@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page4@@};
        \end{tikzpicture}
        %------------ @@page5@@ ---------------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
                \textbf{@@box5blank1title@@:} @@box5blank1fill@@\\
                \textbf{@@box5blank2title@@:} @@box5blank2fill@@\\
                \textbf{@@box5blank3title@@:} @@box5blank3fill@@\\
                \textbf{@@box5blank4title@@:} @@box5blank4fill@@\\
                \textbf{@@box5blank5title@@:} @@box5blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page5@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page5@@};
        \end{tikzpicture}

        %------------ @@page6@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}  
        \textbf{@@box6blank1title@@:} @@box6blank1fill@@\\
                \textbf{@@box6blank2title@@:} @@box6blank2fill@@\\
                \textbf{@@box6blank3title@@:} @@box6blank3fill@@\\
                \textbf{@@box6blank4title@@:} @@box6blank4fill@@\\
                \textbf{@@box6blank5title@@:} @@box6blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page6@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page6@@};
        \end{tikzpicture}

        %------------ @@page7@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
            \textbf{@@box7blank1title@@:} @@box7blank1fill@@\\
                \textbf{@@box7blank2title@@:} @@box7blank2fill@@\\
                \textbf{@@box7blank3title@@:} @@box7blank3fill@@\\
                \textbf{@@box7blank4title@@:} @@box7blank4fill@@\\
                \textbf{@@box7blank5title@@:} @@box7blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page7@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page7@@};
        \end{tikzpicture}


        %------------ @@page8@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
        \textbf{@@box8blank1title@@:} @@box8blank1fill@@\\
                \textbf{@@box8blank2title@@:} @@box8blank2fill@@\\
                \textbf{@@box8blank3title@@:} @@box8blank3fill@@\\
                \textbf{@@box8blank4title@@:} @@box8blank4fill@@\\
                \textbf{@@box8blank5title@@:} @@box8blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page8@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page8@@};
        \end{tikzpicture}
        \
        %------------ @@page9@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
                \textbf{@@box9blank1title@@:} @@box9blank1fill@@\\
                \textbf{@@box9blank2title@@:} @@box9blank2fill@@\\
                \textbf{@@box9blank3title@@:} @@box9blank3fill@@\\
                \textbf{@@box9blank4title@@:} @@box9blank4fill@@\\
                \textbf{@@box9blank5title@@:} @@box9blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page9@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page9@@};
        \end{tikzpicture}
        %------------ @@page10@@---------------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
                \textbf{@@box10blank1title@@:} @@box10blank1fill@@\\
                \textbf{@@box10blank2title@@:} @@box10blank2fill@@\\
                \textbf{@@box10blank3title@@:} @@box10blank3fill@@\\
                \textbf{@@box10blank4title@@:} @@box10blank4fill@@\\
                \textbf{@@box10blank5title@@:} @@box10blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page10@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page10@@};
        \end{tikzpicture}

        %------------ @@page11@@ ---------------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
                \textbf{@@box11blank1title@@:} @@box11blank1fill@@\\
                \textbf{@@box11blank2title@@:} @@box11blank2fill@@\\
                \textbf{@@box11blank3title@@:} @@box11blank3fill@@\\
                \textbf{@@box11blank4title@@:} @@box11blank4fill@@\\
                \textbf{@@box11blank5title@@:} @@box11blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page11@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page11@@};
        \end{tikzpicture}

        %------------ @@page12@@ ---------------
        \begin{tikzpicture}
        \node [mybox] (box){%
            \begin{minipage}{0.3\textwidth}
                \textbf{@@box12blank1title@@:} @@box12blank1fill@@\\
                \textbf{@@box12blank2title@@:} @@box12blank2fill@@\\
                \textbf{@@box12blank3title@@:} @@box12blank3fill@@\\
                \textbf{@@box12blank4title@@:} @@box12blank4fill@@\\
                \textbf{@@box12blank5title@@:} @@box12blank5fill@@\\
            \end{minipage}
        };
        %------------ @@page12@@ Header ---------------------
        \node[fancytitle, right=10pt] at (box.north west) {@@page12@@};
        \end{tikzpicture}
        \end{multicols*}
        \end{document}

        """


        for key, value in heading_mapping_dict.items():
            template = template.replace(key, value)

        # Then, replace the fill placeholders
        for key, value in fill_mapping_dict.items():
            template = template.replace(key, value)

        for key, value in page_dict.items():
            template = template.replace(key, value)
        
        return template, 200

    except Exception as e:
        print(f"Error in /latex endpoint: {str(e)}")
        return f'Error generating LaTeX: {str(e)}', 500

@app.route('/pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        if not data or 'template' not in data:
            return 'No template provided in request body', 400

        template = data['template']

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "document.tex")
            pdf_path = os.path.join(tmpdir, "document.pdf")

            # Write the LaTeX file
            with open(tex_path, "w", encoding='utf-8') as f:
                f.write(template)

            # Run pdflatex to generate PDF
            cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                tex_path
            ]
            result = subprocess.run(
                cmd,
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )

            if result.returncode != 0:
                print("LaTeX compilation error:", result.stderr.decode("utf-8"))
                return 'Error compiling LaTeX', 400

            # Read the generated PDF
            with open(pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()

            # Create response with PDF file
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'inline; filename=cheatsheet.pdf'
            return response

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return f'Error generating PDF: {str(e)}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)