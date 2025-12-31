"""
Red Hat Content Creator
Generates Red Hat training content (lectures, GEs, lab scripts) following Red Hat standards
Automatically pulls latest standards from redhat-content-standards repository
"""

import os
import json
import re
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Try to import Ollama for content generation
try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama not available for content generation")


class RedHatContentCreator:
    """
    Creates Red Hat training content following official standards
    Automatically pulls/clones redhat-content-standards repository
    """
    
    def __init__(self, 
                 standards_dir: str = "/home/dallas/dev/redhat-content-standards",
                 standards_repo: Optional[str] = None,
                 model_name: str = "deepseek-r1:latest",
                 auto_pull: bool = True):
        """
        Initialize Red Hat Content Creator
        
        Args:
            standards_dir: Path to redhat-content-standards directory
            standards_repo: Git repository URL for redhat-content-standards (optional)
            model_name: Ollama model to use for content generation
            auto_pull: Automatically pull/clone repo before creating content
        """
        self.standards_dir = Path(standards_dir)
        self.standards_repo = standards_repo
        self.model_name = model_name
        self.auto_pull = auto_pull
        
        # Ensure standards directory exists and is up to date
        if self.auto_pull:
            self._ensure_standards_repo()
        
        self.templates = self._load_templates()
        self.instructions = self._load_instructions()
    
    def _ensure_standards_repo(self):
        """
        Ensure redhat-content-standards repository exists and is up to date
        Clones if missing, pulls if exists
        """
        standards_path = self.standards_dir
        
        # Check if directory exists
        if standards_path.exists():
            # Check if it's a git repository
            git_dir = standards_path / ".git"
            if git_dir.exists():
                # It's a git repo - pull latest changes
                try:
                    print(f"Pulling latest changes from redhat-content-standards repository...")
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=str(standards_path),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        print(f"✅ Successfully updated redhat-content-standards repository")
                    else:
                        print(f"⚠️  Git pull had issues: {result.stderr}")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  Git pull timed out, using existing standards")
                except Exception as e:
                    print(f"⚠️  Error pulling standards repo: {e}, using existing standards")
            else:
                # Directory exists but not a git repo
                print(f"⚠️  Standards directory exists but is not a git repository")
                print(f"   Using existing standards at {standards_path}")
        else:
            # Directory doesn't exist - clone if repo URL provided
            if self.standards_repo:
                try:
                    print(f"Cloning redhat-content-standards repository from {self.standards_repo}...")
                    parent_dir = standards_path.parent
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    
                    result = subprocess.run(
                        ["git", "clone", self.standards_repo, str(standards_path.name)],
                        cwd=str(parent_dir),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        print(f"✅ Successfully cloned redhat-content-standards repository")
                    else:
                        print(f"⚠️  Git clone failed: {result.stderr}")
                        print(f"   Will attempt to use standards_dir if it exists")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  Git clone timed out")
                except Exception as e:
                    print(f"⚠️  Error cloning standards repo: {e}")
            else:
                print(f"⚠️  Standards directory not found and no repository URL provided")
                print(f"   Expected location: {standards_path}")
                print(f"   Set standards_repo parameter to auto-clone, or ensure directory exists")
        
    def _load_templates(self) -> Dict:
        """Load templates from standards directory"""
        templates = {}
        templates_dir = self.standards_dir / "templates"
        
        if templates_dir.exists():
            # Load lecture template
            lecture_template = templates_dir / "lecture-template.adoc"
            if lecture_template.exists():
                templates["lecture"] = lecture_template.read_text()
            
            # Load GE template
            ge_template = templates_dir / "ge-template.adoc"
            if ge_template.exists():
                templates["ge"] = ge_template.read_text()
        
        return templates
    
    def _load_instructions(self) -> Dict:
        """Load instructions from standards directory"""
        instructions = {}
        instructions_dir = self.standards_dir / "instructions"
        
        if instructions_dir.exists():
            # Load lecture instructions
            lecture_instructions = instructions_dir / "lectures.md"
            if lecture_instructions.exists():
                instructions["lecture"] = lecture_instructions.read_text()
            
            # Load GE instructions
            ge_instructions = instructions_dir / "guided-exercises.md"
            if ge_instructions.exists():
                instructions["ge"] = ge_instructions.read_text()
            
            # Load dynolabs instructions
            dynolabs_instructions = instructions_dir / "dynolabs.md"
            if dynolabs_instructions.exists():
                instructions["dynolabs"] = dynolabs_instructions.read_text()
        
        return instructions
    
    def parse_content_request(self, user_input: str) -> Dict:
        """
        Parse user input to extract content creation request
        
        Args:
            user_input: User's request text
            
        Returns:
            Dict with parsed request details
        """
        user_lower = user_input.lower()
        
        # Detect content types
        content_types = []
        if "lecture" in user_lower:
            content_types.append("lecture")
        if "ge" in user_lower or "guided exercise" in user_lower:
            content_types.append("ge")
        if "lab" in user_lower or "dynolab" in user_lower or "lab script" in user_lower:
            content_types.append("dynolabs")
        
        # Extract topic
        topic = None
        # Look for patterns like "on <topic>", "about <topic>", "for <topic>"
        patterns = [
            r"(?:on|about|for|create.*?on)\s+([A-Z][^,\.]+?)(?:\.|,|$|in)",
            r"topic[:\s]+([A-Z][^,\.]+?)(?:\.|,|$|in)",
        ]
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                break
        
        # If no topic found, try to extract from common patterns
        if not topic:
            # Look for capitalized phrases that might be topics
            words = user_input.split()
            capitalized_phrases = []
            current_phrase = []
            for word in words:
                if word[0].isupper() and len(word) > 2:
                    current_phrase.append(word)
                else:
                    if current_phrase:
                        capitalized_phrases.append(" ".join(current_phrase))
                        current_phrase = []
            if capitalized_phrases:
                topic = capitalized_phrases[-1]  # Take the last capitalized phrase
        
        # Extract directory
        directory = None
        dir_patterns = [
            r"in\s+(/[\w/-]+)",
            r"directory[:\s]+([/\w-]+)",
            r"to\s+(/[\w/-]+)",
        ]
        for pattern in dir_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                directory = match.group(1).strip()
                break
        
        # Default directory if not specified
        if not directory:
            directory = "/home/dallas/dev/au0025l-demo"
        
        # Extract course ID from directory if possible
        course_id = None
        if directory:
            # Look for pattern like au0025l, au0024l, etc.
            course_match = re.search(r'(au\d{4}[a-z]?)', directory, re.IGNORECASE)
            if course_match:
                course_id = course_match.group(1).lower()
        
        return {
            "content_types": content_types if content_types else ["lecture", "ge", "dynolabs"],
            "topic": topic or "Ansible Roles Create",
            "directory": directory,
            "course_id": course_id or "au0025l"
        }
    
    def create_lecture(self, topic: str, output_dir: str, learning_objectives: Optional[List[str]] = None) -> str:
        """
        Create a Red Hat lecture following standards
        
        Args:
            topic: Lecture topic
            output_dir: Directory to save lecture
            learning_objectives: Optional list of learning objectives
            
        Returns:
            Path to created lecture file
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama not available for content generation")
        
        # Build prompt using instructions
        instruction_text = self.instructions.get("lecture", "")
        template_text = self.templates.get("lecture", "")
        
        prompt = f"""You are an expert Red Hat training content developer. Create a lecture on "{topic}" following Red Hat content standards.

{instruction_text}

Use this template structure:
{template_text}

Generate a complete lecture in AsciiDoc format that:
1. Follows all Red Hat Technical Writing Style Guide requirements
2. Uses proper AsciiDoc formatting (==, ===, ==== for headings)
3. Includes code blocks with [subs="+quotes,+macros"]
4. Uses proper command formatting with [student@workstation ~]$ prompts
5. Includes a References section at the end
6. Focuses on learning objectives related to: {topic}

Learning Objectives:
{chr(10).join(f"- {obj}" for obj in (learning_objectives or [f"Understand {topic}", f"Configure {topic}", f"Manage {topic}"]))}

Generate the complete lecture now:"""
        
        # Generate content using Ollama
        response = chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        
        content = response.get("message", {}).get("content", "")
        
        # Clean up content (remove markdown code blocks if present)
        if "```asciidoc" in content:
            content = content.split("```asciidoc")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Create output directory structure
        output_path = Path(output_dir)
        content_dir = output_path / "content" / self._slugify(topic)
        content_dir.mkdir(parents=True, exist_ok=True)
        
        # Save lecture
        lecture_file = content_dir / "lecture.adoc"
        lecture_file.write_text(content)
        
        return str(lecture_file)
    
    def create_ge(self, topic: str, output_dir: str, outcomes: Optional[List[str]] = None, course_id: str = "au0025l") -> str:
        """
        Create a Red Hat Guided Exercise following standards
        
        Args:
            topic: GE topic
            output_dir: Directory to save GE
            outcomes: Optional list of outcomes
            course_id: Course ID for lab script reference
            
        Returns:
            Path to created GE file
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama not available for content generation")
        
        # Build prompt using instructions
        instruction_text = self.instructions.get("ge", "")
        template_text = self.templates.get("ge", "")
        
        # Create exercise name slug
        exercise_name = self._slugify(topic)
        lab_script = f"{course_id}-{exercise_name}"
        
        prompt = f"""You are an expert Red Hat training content developer. Create a Guided Exercise (GE) on "{topic}" following Red Hat content standards.

{instruction_text}

Use this template structure:
{template_text}

Generate a complete Guided Exercise in AsciiDoc format that:
1. Includes :gls_prefix: at the top
2. Has Outcomes section with pass:a,n[{{gls_res_outcomes}}]
3. Has Prerequisites section with pass:a,n[{{gls_res_prereqs}}]
4. Has Instructions section with [role='Checklist'] and pass:a,n[{{gls_res_instructions}}]
5. Includes step_one_ge.adoc snippet
6. Uses numbered steps (.) and substeps (..)
7. Includes close_remote.adoc snippet at the end
8. Uses proper code blocks with [subs="+quotes,+macros"]
9. Uses lab script: {lab_script}

Outcomes:
{chr(10).join(f"* {outcome}" for outcome in (outcomes or [f"Configure {topic}", f"Verify {topic}", f"Manage {topic}"]))}

Generate the complete Guided Exercise now:"""
        
        # Generate content using Ollama
        response = chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        
        content = response.get("message", {}).get("content", "")
        
        # Clean up content
        if "```asciidoc" in content:
            content = content.split("```asciidoc")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Replace lab script placeholder
        content = content.replace("{gls_lab_script}", lab_script)
        
        # Create output directory structure
        output_path = Path(output_dir)
        content_dir = output_path / "content" / self._slugify(topic)
        content_dir.mkdir(parents=True, exist_ok=True)
        
        # Save GE
        ge_file = content_dir / "ge.adoc"
        ge_file.write_text(content)
        
        return str(ge_file)
    
    def create_dynolabs(self, topic: str, output_dir: str, course_id: str = "au0025l", targets: List[str] = None) -> Dict[str, str]:
        """
        Create Red Hat dynolabs (lab infrastructure) components
        
        Args:
            topic: Lab topic
            output_dir: Directory to save lab scripts
            course_id: Course ID
            targets: List of target hosts (default: ["workstation", "servera"])
            
        Returns:
            Dict with paths to created files
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama not available for content generation")
        
        targets = targets or ["workstation", "servera"]
        exercise_name = self._slugify(topic)
        lab_name = exercise_name.replace("_", "-")
        
        # Load dynolabs instructions
        dynolabs_instructions = self.instructions.get("dynolabs", "")
        
        output_path = Path(output_dir)
        
        # 1. Create Python script
        python_script = self._create_python_script(exercise_name, lab_name, course_id, targets, output_path)
        
        # 2. Create start.yml playbook
        start_playbook = self._create_start_playbook(exercise_name, lab_name, course_id, targets, output_path)
        
        # 3. Create finish.yml playbook
        finish_playbook = self._create_finish_playbook(exercise_name, lab_name, course_id, targets, output_path)
        
        # 4. Create lab materials directory structure
        materials = self._create_lab_materials(exercise_name, lab_name, course_id, output_path)
        
        return {
            "python_script": python_script,
            "start_playbook": start_playbook,
            "finish_playbook": finish_playbook,
            "materials": materials
        }
    
    def _create_python_script(self, exercise_name: str, lab_name: str, course_id: str, targets: List[str], output_path: Path) -> str:
        """Create Python lab control script"""
        class_name = "".join(word.capitalize() for word in exercise_name.split("_"))
        
        script_content = f'''"""
{exercise_name.replace("_", " ").title()} Guided Exercise
"""
from labs.ui.steps import ansible
from labs.activities import GuidedExercise

_targets = {targets}


class {class_name}(GuidedExercise):
    """
    Guided Exercise for {exercise_name.replace("_", " ")}.
    """
    __LAB__ = "{lab_name}"

    def start(self):
        """
        Start the {lab_name} lab environment.
        """
        # Check lab systems
        ansible.run_playbook_step(
            self,
            "rht.dynolabs_aap.host_reachable.yml",
            step_message="Checking lab systems",
            extra_args="--limit " + ",".join(_targets),
        )

        # Add exercise content
        ansible.run_playbook_step(
            self,
            "collections/ansible_collections/rht/{course_id}_common/playbooks/add-exercise-dirs.yml",
            step_message="Adding exercise content",
            extra_vars={{"exercise": "{{{{ {exercise_name} }}}}"}},
        )

        # Initialize VS Code
        ansible.run_playbook_step(
            self,
            "collections/ansible_collections/rht/{course_id}_common/playbooks/initialize-vscode.yml",
            step_message="Initialize VS Code",
        )

        # Run exercise-specific setup
        ansible.run_playbook_step(
            self,
            "{lab_name}/start.yml",
            step_message="Setting up exercise",
        )

    def finish(self):
        """
        Finish and clean up the {lab_name} lab environment.
        """
        # Check lab systems
        ansible.run_playbook_step(
            self,
            "rht.dynolabs_aap.host_reachable.yml",
            step_message="Checking lab systems",
            extra_args="--limit " + ",".join(_targets),
        )

        # Remove dev container
        ansible.run_playbook_step(
            self,
            "collections/ansible_collections/rht/{course_id}_common/playbooks/remove-dev-container.yml",
            step_message="Removing the development container",
            extra_vars={{"exercise": "{{{{ {exercise_name} }}}}"}},
        )

        # Run exercise-specific cleanup
        ansible.run_playbook_step(
            self,
            "{lab_name}/finish.yml",
            step_message="Cleaning up exercise",
        )
'''
        
        # Save Python script
        script_dir = output_path / "classroom" / "grading" / "src" / course_id
        script_dir.mkdir(parents=True, exist_ok=True)
        script_file = script_dir / f"{lab_name}.py"
        script_file.write_text(script_content)
        
        return str(script_file)
    
    def _create_start_playbook(self, exercise_name: str, lab_name: str, course_id: str, targets: List[str], output_path: Path) -> str:
        """Create start.yml Ansible playbook"""
        playbook_content = f'''---
- name: Set up {lab_name} lab environment
  hosts: {targets[0] if targets else "servera"}.lab.example.com
  become: true

  tasks:
    - name: Create devops user with home directory
      ansible.builtin.user:
        name: devops
        create_home: true
        shell: /bin/bash
        state: present

    - name: Set up sudo access for devops user
      ansible.builtin.copy:
        content: "devops ALL=(ALL) NOPASSWD: ALL\\n"
        dest: /etc/sudoers.d/devops
        mode: '0440'
        owner: root
        group: root

    - name: Create exercise directory structure
      ansible.builtin.file:
        path: "{{{{ item }}}}"
        state: directory
        mode: '0755'
      loop:
        - /home/student/{lab_name}
        - /home/student/{lab_name}/files
        - /home/student/{lab_name}/templates
        - /home/student/{lab_name}/roles

    - name: Clean up any existing exercise files
      ansible.builtin.file:
        path: /home/student/{lab_name}/old-file.yml
        state: absent
'''
        
        # Save start playbook
        playbook_dir = output_path / "classroom" / "grading" / "src" / course_id / "ansible" / lab_name
        playbook_dir.mkdir(parents=True, exist_ok=True)
        playbook_file = playbook_dir / "start.yml"
        playbook_file.write_text(playbook_content)
        
        return str(playbook_file)
    
    def _create_finish_playbook(self, exercise_name: str, lab_name: str, course_id: str, targets: List[str], output_path: Path) -> str:
        """Create finish.yml Ansible playbook"""
        playbook_content = f'''---
- name: Clean up {lab_name} lab environment
  hosts: {targets[0] if targets else "servera"}.lab.example.com
  become: true

  tasks:
    - name: Stop and disable services
      ansible.builtin.systemd_service:
        name: "{{{{ item }}}}"
        enabled: false
        state: stopped
      loop: []

    - name: Remove packages
      ansible.builtin.dnf:
        name: "{{{{ item }}}}"
        state: absent
      loop: []

    - name: Remove created files
      ansible.builtin.file:
        path: "{{{{ item }}}}"
        state: absent
      loop: []

    - name: Reset firewall to default state
      ansible.posix.firewalld:
        state: reset
        permanent: true
        immediate: true

    - name: Remove devops user and sudo access
      ansible.builtin.user:
        name: devops
        state: absent
        remove: true

    - name: Remove sudoers file
      ansible.builtin.file:
        path: /etc/sudoers.d/devops
        state: absent

    - name: Remove exercise directory
      ansible.builtin.file:
        path: /home/student/{lab_name}
        state: absent

    - name: Clean up temporary files
      ansible.builtin.file:
        path: "{{{{ item }}}}"
        state: absent
      loop:
        - /tmp/ansible-*
        - /var/tmp/ansible-*
'''
        
        # Save finish playbook
        playbook_dir = output_path / "classroom" / "grading" / "src" / course_id / "ansible" / lab_name
        playbook_dir.mkdir(parents=True, exist_ok=True)
        playbook_file = playbook_dir / "finish.yml"
        playbook_file.write_text(playbook_content)
        
        return str(playbook_file)
    
    def _create_lab_materials(self, exercise_name: str, lab_name: str, course_id: str, output_path: Path) -> str:
        """Create lab materials directory structure"""
        materials_dir = output_path / "classroom" / "grading" / "src" / course_id / "materials" / "labs" / lab_name
        materials_dir.mkdir(parents=True, exist_ok=True)
        
        # Create inventory file
        inventory_file = materials_dir / "inventory"
        inventory_content = f"""[webservers]
servera.lab.example.com

[dev]
serverc.lab.example.com
"""
        inventory_file.write_text(inventory_content)
        
        # Create ansible.cfg
        ansible_cfg = materials_dir / "ansible.cfg"
        ansible_cfg_content = """[defaults]
remote_user=devops
inventory=./inventory
ask_pass = false

[privilege_escalation]
become = true
become_method = ansible.builtin.sudo
become_user = root
become_ask_pass = false
"""
        ansible_cfg.write_text(ansible_cfg_content)
        
        # Create ansible-navigator.yml
        navigator_file = materials_dir / "ansible-navigator.yml"
        navigator_content = f'''---
ansible-navigator:
  execution-environment:
    image: utility.lab.example.com:5000/ansible-automation-platform-25/ee-supported-rhel8:latest
    pull:
      policy: missing
      arguments:
        - "--tls-verify=false"
  mode: stdout
  playbook-artifact:
    enable: false
'''
        navigator_file.write_text(navigator_content)
        
        # Create solutions directory
        solutions_dir = materials_dir / "solutions"
        solutions_dir.mkdir(parents=True, exist_ok=True)
        
        return str(materials_dir)
    
    def _slugify(self, text: str) -> str:
        """Convert text to slug format"""
        # Convert to lowercase and replace spaces/special chars with underscores
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '_', slug)
        return slug.strip('_')
    
    def create_all_content(self, topic: str, output_dir: str, course_id: str = "au0025l", 
                          content_types: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Create all requested content types
        
        Args:
            topic: Content topic
            output_dir: Output directory
            course_id: Course ID
            content_types: List of content types to create (lecture, ge, dynolabs)
            
        Returns:
            Dict mapping content type to file paths
        """
        # Ensure standards are up to date before creating content
        if self.auto_pull:
            self._ensure_standards_repo()
            # Reload templates and instructions in case they were updated
            self.templates = self._load_templates()
            self.instructions = self._load_instructions()
        
        content_types = content_types or ["lecture", "ge", "dynolabs"]
        results = {}
        
        if "lecture" in content_types:
            lecture_path = self.create_lecture(topic, output_dir)
            results["lecture"] = lecture_path
        
        if "ge" in content_types:
            ge_path = self.create_ge(topic, output_dir, course_id=course_id)
            results["ge"] = ge_path
        
        if "dynolabs" in content_types:
            dynolabs_paths = self.create_dynolabs(topic, output_dir, course_id=course_id)
            results["dynolabs"] = dynolabs_paths
        
        return results
