# A tool to change hedcenbot's subject links
import json

with open('jsons/subject_links.json', 'r') as f:
    sub_l = json.load(f)

schedule = 'HEDCen G12 1st Trim'
ol = list(enumerate(sub_l[schedule]))
selection = {str(n+1): key for n, key in ol}

print('\n'.join([f"{n+1}) {key}" for n, key in ol]))

valid_input = False
selected = None
while not valid_input:
    selected = input(f"Select a subject to change (1-{len(ol)}) or type \'exit\' to exit: ")
    if selected in selection and selected:
        valid_input = True
    elif selected.lower() == 'exit':
        quit()

if selected_key := selection.get(selected, None):
    nlink = input("Input new link: ")

    if nlink:
        sub_l[schedule][selected_key] = nlink
        print(f"Successfully changed {selected_key} to {nlink}!")

        with open('jsons/subject_links.json', 'w') as f:
            json.dump(sub_l, f, indent=4)
