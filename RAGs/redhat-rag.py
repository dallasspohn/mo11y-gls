import json

def generate_rag_guidelines():
    guidelines = {
        "writing_style": {
            "tone": "Professional yet approachable",
            "technical_balance": "Technical but accessible",
            "formatting": "Adhere to Red Hat's Stylepedia guidelines"
        },
        "preferred_terminology": {
            "automation_execution_environment": "Use instead of 'container'",
            "playbook_run": "Use instead of 'execution'",
            "worker": "Replace 'slave'",
            "controller": "Use instead of 'tower' (except for legacy)"
        },
        "word_modifications": {
            "avoid": ["simply", "just", "obviously"],
            "inclusive_replacements": {"guys": "team"}
        },
        "formatting_asciidoc": {
            "comments": "Use commented-out replacements instead of removals",
            "syntax": "Ensure correct AsciiDoc formatting for Red Hat docs"
        },
        "hierarchy": {
            "immediate_supervisor": "Jaime Yague Mayans",
            "team_lead": "Michael Phillips",
            "team_members": "Alejandra, Morgan, David O",
            "higher_management": "Pat Sharp"
        },
        "internal_links": {
            "stylepedia": "https://stylepedia.net/style/",
            "team_wiki": "[Insert Link]",
            "code_repositories": "https://github.com/RedHatTraining",
            "automation_guidelines": "https://docs.ansible.com/ansible/2.8/user_guide/playbooks_best_practices.html"
        },
        "contextual_notes": [
            "Red Hat product knowledge should be assumed.",
            "Ansible best practices should align with internal documentation.",
            "Updates should be incorporated as policies evolve."
        ]
    }
    
    with open("rag_guidelines.json", "w") as file:
        json.dump(guidelines, file, indent=4)
    
    print("RAG guidelines JSON file has been saved.")

# Run the function to generate the file
generate_rag_guidelines()
