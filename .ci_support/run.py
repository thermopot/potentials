#!/usr/bin/env python
import datetime
import os
import json
from jinja2 import Template
import subprocess
import shutil

potential_path = 'potential'
protocol_path = 'protocol'
calculation_path = 'calculation'
website_path = 'website/content'
database_path = 'database'


def get_list_of_potentials(potential_path):
    pot_lst = []
    for pot in os.listdir(potential_path):
        pot_dir = os.path.abspath(os.path.join(potential_path, pot))
        pot_dict = None
        for file in os.listdir(pot_dir):
            if '.json' in file:
                os.makedirs(os.path.join(database_path, pot), exist_ok=True)
                pot_file = os.path.join(pot_dir, file)
                shutil.copyfile(pot_file, os.path.join(database_path, pot, file))
                with open(pot_file, 'r') as f: 
                    pot_dict = json.load(f)
        if pot_dict is not None:
            pot_dict['filename'] = [os.path.join(pot_dir, p) for p in pot_dict['filename']]
            for f in pot_dict['filename']:
                shutil.copyfile(f, os.path.join(database_path, pot, os.path.basename(f))) 
            pot_lst.append(pot_dict)
    return pot_lst


def get_list_of_protocols(protocol_path):
    proc_lst = {}
    for proc in os.listdir(protocol_path):
        proc_dir = os.path.abspath(os.path.join(protocol_path, proc))
        proc_dict = {}
        for f in os.listdir(proc_dir): 
            if 'script.ipynb' == f: 
                proc_dict['script'] = os.path.join(proc_dir, f)
            elif 'plot.ipynb' == f:
                proc_dict['plot'] = os.path.join(proc_dir, f)
        if len(proc_dict) > 0: 
            proc_lst[proc] = proc_dict
    return proc_lst


def get_script_output(script):
    script_ext_split = os.path.splitext(script)
    return script_ext_split[0] + ".nbconvert" + script_ext_split[1]


def apply_protocol(element, pot, proc, working_dir):
    os.makedirs(working_dir, exist_ok=True)
    input_dict = pot
    input_dict['path'] = working_dir
    input_dict['element'] = element
    with open(os.path.join(working_dir, 'input.json'), 'w') as f:
        json.dump(input_dict, f)
    script = proc['script']
    script_directory = os.path.dirname(script)
    job_name = os.path.basename(script_directory)
    command = os.path.join(script_directory, "run.sh") + " " + \
              job_name + " " + \
              os.path.join(working_dir, "input_file.json") + " " + \
              os.path.join(working_dir, "output_file.json") + " " + \
              os.path.join(working_dir, "plot.nbconvert.ipynb")
    subprocess.check_output("export script_dir=" + script_directory + "; " + command,
                           cwd=working_dir,
                           shell=True)


for pot in get_list_of_potentials(potential_path=potential_path):
    for element in pot['species']:
        for k, v in get_list_of_protocols(protocol_path=protocol_path).items():
            slug = '-'.join([pot['name'], element, k]).lower().replace('_', '-') + '.json'
            pot_path = os.path.join(database_path, pot['name'])
            if not os.path.exists(pot_path) or (os.path.exists(pot_path) and slug not in os.listdir(pot_path)):
                apply_protocol(element=element, 
                               pot=pot, 
                               proc=v, 
                               working_dir=os.path.abspath(os.path.join(calculation_path, pot['name'], element, k)))


t = Template("""Title: {{title}}
Slug: {{slug}}
Date: {{date}}
Tags: {{tags}}
Author: {{author}}

{{'{%'}} notebook {{notebook}} {{'%}'}}'""")


def render_post(pot, element, k, now, slug, notebook):
    return t.render(title=' '.join([pot['name'], element, k]),
                    slug=slug,
                    date='-'.join([str(now.year), str(now.month), str(now.day)]),
                    tags=', '.join([pot['name'], k]) + ',',
                    author='Potential',
                    notebook=notebook,
                    )


now = datetime.datetime.now()
for pot in get_list_of_potentials(potential_path=potential_path):
    for element in pot['species']:
        for k, v in get_list_of_protocols(protocol_path=protocol_path).items():
            working_dir = os.path.abspath(os.path.join(calculation_path, pot['name'], element, k))
            if os.path.exists(working_dir):
                notebook = [os.path.join(working_dir, f) for f in os.listdir(working_dir) if f == 'plot.nbconvert.ipynb'][0]
                output_file = [os.path.join(working_dir, f) for f in os.listdir(working_dir) if f == 'output.json'][0]
                slug = '-'.join([pot['name'], element, k]).lower().replace('_', '-')
                
                # store files for website
                os.makedirs(os.path.join(website_path, pot['name']), exist_ok=True)
                with open(os.path.join(website_path, pot['name'], slug + '.md'), 'w') as f:
                    f.writelines(render_post(pot=pot, element=element, k=k, now=now, slug=slug, notebook=os.path.join(pot['name'], slug + '.ipynb')))
                shutil.copyfile(notebook, os.path.join(website_path, pot['name'], slug + '.ipynb'))
                shutil.copyfile(output_file, os.path.join(website_path, pot['name'], slug + '.json'))

                # store files for database 
                shutil.copyfile(output_file, os.path.join(database_path, pot['name'], slug + '.json'))
