from extract_text import get_extracted_text
from openai import OpenAI
from openai.types.beta.threads.message_create_params import (
    Attachment,
    AttachmentToolFileSearch,
)
from pydantic import BaseModel
from openai import OpenAI

from pathlib import Path
import re
import pdfplumber

from dotenv import load_dotenv
import os
import json
# Get the response text
response_text = get_extracted_text()
response_text = json.loads(response_text)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

text_lst = response_text['text_lst']

all_topics = []

for text in text_lst:
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

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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

for i in topic_lst:

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
         
        YOU MUST GO BEYOND MEER DEFINITIONS AND PROVIDE INFO THAT WILL HELP ANSWER QUESTIONS ON AN EXAM

        Headings: Identify the five most essential topics in the provided material. Each heading should concisely reflect its subject matter.
        LaTeX Content: For each heading, include one line of LaTeX text that summarizes or conveys key information about the topic.
        Formatting:
        Do not include begin document or end document tags.
        Close all LaTeX environments properly (e.g., for equations or itemized lists).
        Example Output Format:
        {ex_1},{ex_2},{ex_3}
        Additional Notes:
        Use your expertise to determine the most critical topics and present them effectively.
        Take all the time needed to reason through the task and ensure the highest quality.
        Expectations:
        FIVE (5) HEADINGS
        Follow the format and ensure outputs are consistent.
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


for i in range(len(topic_lst)):
    key = f"@@page{i+1}@@"
    page_dict[key] = list(topic_lst[i].keys())[0] 

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

file_name = "output.tex"

file_path = os.path.join(os.getcwd(), file_name)

with open(file_path, "w", encoding="utf-8") as file:
    file.write(template)



import subprocess
import os

def compile_latex_to_pdf(tex_file_path):
    """
    Compile a LaTeX file to PDF using pdflatex in the root directory
    
    Args:
        tex_file_path (str): Path to the .tex file
    
    Returns:
        bool: True if compilation was successful, False otherwise
    """
    try:
        # Check if the tex file exists
        if not os.path.exists(tex_file_path):
            print(f"Error: TeX file not found at {tex_file_path}")
            return False
            
        # Check if pdflatex is available
        try:
            subprocess.run(['pdflatex', '--version'], capture_output=True, text=True)
        except FileNotFoundError:
            print("Error: pdflatex not found. Please ensure LaTeX is installed and in your PATH")
            return False
            
        # Run pdflatex twice to ensure proper rendering of all elements
        for i in range(2):
            print(f"\nRunning pdflatex (pass {i+1})...")
            
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"\nPdflatex failed with return code: {result.returncode}")
                return False
                
        return True
        
    except Exception as e:
        print(f"Error compiling LaTeX: {str(e)}")
        return False

# After generating output.tex
tex_file_path = 'output.tex'

print("Starting PDF generation...")
success = compile_latex_to_pdf(tex_file_path)
if success:
    print("PDF generated successfully")
    if os.path.exists('output.pdf'):
        print("PDF file created in root directory")
    else:
        print("Warning: PDF file not found")
else:
    print("Failed to generate PDF")