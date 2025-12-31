# Red Hat Content Creation Integration

## Overview

Mo11y now has the ability to create Red Hat training content (lectures, Guided Exercises, and lab scripts) following official Red Hat content standards.

## How It Works

### 1. User Request
Simply ask Mo11y to create Red Hat content:
- "create a lecture and GE on Ansible Roles Create in /home/dallas/dev/au0025l-demo"
- "create a lecture, GE, and lab scripts on Ansible Roles"
- "create Red Hat content for Ansible Roles Create"

### 2. Automatic Detection
Mo11y automatically detects content creation requests by looking for keywords like:
- "create lecture", "create ge", "create lab"
- "red hat content", "training content"
- "lecture on", "ge on", "lab on"

### 3. Content Generation
When detected, Mo11y:
1. Parses your request to extract:
   - Topic (e.g., "Ansible Roles Create")
   - Content types needed (lecture, GE, dynolabs)
   - Output directory
   - Course ID (extracted from directory path)

2. Generates content using:
   - Red Hat content standards from `/home/dallas/dev/redhat-content-standards`
   - Templates for lectures and GEs
   - Instructions for each content type
   - DeepSeek R1 model for content generation

3. Creates files:
   - **Lecture**: `content/<topic>/lecture.adoc`
   - **GE**: `content/<topic>/ge.adoc`
   - **Lab Scripts**:
     - Python script: `classroom/grading/src/<course-id>/<exercise-name>.py`
     - Start playbook: `classroom/grading/src/<course-id>/ansible/<exercise-name>/start.yml`
     - Finish playbook: `classroom/grading/src/<course-id>/ansible/<exercise-name>/finish.yml`
     - Lab materials: `classroom/grading/src/<course-id>/materials/labs/<exercise-name>/`

## Components

### `redhat_content_creator.py`
Main module that handles:
- Parsing user requests
- Loading Red Hat standards and templates
- Generating lectures using Ollama
- Generating GEs using Ollama
- Creating dynolabs infrastructure (Python scripts, Ansible playbooks, lab materials)

### MCP Tool: `create_redhat_content`
Registered in `local_mcp_server.py`:
- Tool name: `create_redhat_content`
- Parameters:
  - `request`: Natural language request
  - `output_directory`: Output directory (default: `/home/dallas/dev/au0025l-demo`)

### Agent Integration
In `mo11y_agent.py`:
- Auto-detects Red Hat content creation requests
- Calls MCP tool automatically
- Adds success message to context
- Tracks tool usage for logging

## Example Usage

### Request
```
"create a lecture and GE with lab scripts on Ansible Roles Create in /home/dallas/dev/au0025l-demo"
```

### What Gets Created

1. **Lecture** (`content/ansible_roles_create/lecture.adoc`)
   - Full AsciiDoc lecture following Red Hat standards
   - Includes headings, code blocks, admonitions, references

2. **Guided Exercise** (`content/ansible_roles_create/ge.adoc`)
   - Complete GE with Outcomes, Prerequisites, Instructions
   - Numbered steps and substeps
   - Includes required snippets

3. **Lab Scripts**:
   - `classroom/grading/src/au0025l/ansible-roles-create.py` - Python lab control script
   - `classroom/grading/src/au0025l/ansible/ansible-roles-create/start.yml` - Setup playbook
   - `classroom/grading/src/au0025l/ansible/ansible-roles-create/finish.yml` - Cleanup playbook
   - `classroom/grading/src/au0025l/materials/labs/ansible-roles-create/` - Lab materials (inventory, ansible.cfg, etc.)

## Standards Compliance

All generated content follows:
- Red Hat Technical Writing Style Guide
- AsciiDoc formatting standards
- Content structure requirements
- Module naming conventions (FQCNs)
- Step numbering patterns
- Lab infrastructure standards

## Requirements

- Ollama running with DeepSeek R1 model
- Red Hat content standards directory at `/home/dallas/dev/redhat-content-standards`
- Output directory must exist or be creatable

## Testing

To test the integration:

1. Start Mo11y:
   ```bash
   streamlit run app_enhanced.py
   ```

2. Ask Mo11y:
   ```
   create a lecture and GE on Ansible Roles Create in /home/dallas/dev/au0025l-demo
   ```

3. Check the output directory for created files

## Files Modified

- `redhat_content_creator.py` - New module for content creation
- `local_mcp_server.py` - Added `create_redhat_content` tool
- `mo11y_agent.py` - Added auto-detection and execution logic

## Future Enhancements

- Support for learning objectives input
- Custom outcomes for GEs
- Lab grading scripts generation
- Multi-topic content creation
- Content validation and linting

---

**Ready to create Red Hat training content! 🚀**
