---
name: ansible
url: https://www.ansible.com
deploys: Hosts and cloud modules via playbooks and roles (recognition only)
---

## File signatures
- `ansible.cfg`
- Playbooks: top-level YAML list of plays with `hosts:` plus `tasks:` or `roles:`
- `roles/*/tasks/main.yml` (or `.yaml`)
- NOT bare `inventory`, `hosts` or `requirements.yml`: those names collide with Helm and other tools. Count them only when one of the signatures above is also present

## Support level: recognition only
Imperative, no state: a playbook describes steps, not the resulting resources, so the catalog cannot treat it as source of truth. List the playbooks and roles found, tell the operator Ansible is not supported, and stop the IaC path for it. Do NOT extract resources and do NOT offer "teach me". If the repo also holds a supported tool, continue with that one; if cloud resources exist, offer real-discovery against live AWS.
