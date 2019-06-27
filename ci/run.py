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


def get_list_of_potentials(potential_path):
    pot_lst = []
    for pot in os.listdir(potential_path):
        pot_dir = os.path.abspath(os.path.join(potential_path, pot))
        pot_dict = None
        for file in os.listdir(pot_dir):
            if '.json' in file:
                with open(os.path.join(pot_dir, file), 'r') as f: 
                    pot_dict = json.load(f)
        if pot_dict is not None:
            pot_dict['filename'] = [os.path.join(pot_dir, p) for p in pot_dict['filename']]
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


def apply_protocol(element, pot, proc, working_dir):
    os.makedirs(working_dir, exist_ok=True)
    input_dict = pot
    input_dict['path'] = working_dir
    input_dict['element'] = element
    with open(os.path.join(working_dir, 'input.json'), 'w') as f:
        json.dump(input_dict, f)
    for script in [proc['script'], proc['plot']]:
        shutil.copyfile(script, os.path.join(working_dir, os.path.basename(script)))
        subprocess.check_output('jupyter nbconvert --ExecutePreprocessor.timeout=9999999 --ExecutePreprocessor.kernel_name="python3" --to notebook --execute "' + os.path.basename(script) + '"', 
                                cwd=working_dir, 
                                shell=True)


for pot in get_list_of_potentials(potential_path=potential_path):
    for element in pot['species']:
        for k, v in get_list_of_protocols(protocol_path=protocol_path).items():
            slug = '-'.join([pot['name'], element, k]).lower().replace('_', '-') + '.ipynb'
            if slug not in os.listdir(website_path):
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
            notebook=[os.path.join(working_dir, f) for f in os.listdir(working_dir) if f == 'plot.nbconvert.ipynb'][0]
            slug = '-'.join([pot['name'], element, k]).lower().replace('_', '-') 
            with open(os.path.join(website_path, slug + '.md'), 'w') as f:
                f.writelines(render_post(pot=pot, element=element, k=k, now=now, slug=slug, notebook=slug + '.ipynb'))           
            shutil.copyfile(notebook, os.path.join(website_path, slug + '.ipynb'))


