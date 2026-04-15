---
name: ansible
url: https://www.ansible.com
deploys: Cloud and on-prem resources via playbooks and roles (often cloud modules)
---

## File signatures
- `playbook.yml` / `playbook.yaml` (or any top-level YAML with a list of plays — `hosts:`, `tasks:`, `roles:`)
- `roles/` directory with sub-directories containing `tasks/main.yml`
- `inventory` / `inventory.yml` / `inventory.ini` / `hosts`
- `ansible.cfg`
- `requirements.yml` (collection / role dependencies)

## Stack boundary
One stack = one playbook entry-point (`playbook.yml`) executed against one inventory.

Multi-instance is expressed via:
- separate inventory files per environment (`inventory/prod`, `inventory/staging`)
- group_vars / host_vars (`group_vars/prod.yml`, `group_vars/staging.yml`)
- `--limit` on the CLI to scope a run to a subset of hosts

## Parameter sources (highest to lowest priority)
- `--extra-vars` / `-e` on the CLI (highest precedence in Ansible)
- `vars:` declared in playbook / roles / tasks
- `host_vars/<host>.yml` (per-host variables)
- `group_vars/<group>.yml` (per-group variables)
- Role defaults (`roles/<role>/defaults/main.yml`)
- Vault-encrypted variables (`ansible-vault` files — record reference, NEVER decrypt)
- Inventory variables

## Resource extraction
- Cloud module invocations (`amazon.aws.ec2_instance`, `community.aws.ecs_service`, `azure.azcollection.azure_rm_*`, `google.cloud.gcp_*`, etc.) → one inventory entry per task; raw type is the module name
- `template:`, `copy:`, `lineinfile:` for config files → record as managed config
- `service:` / `systemd:` for service control → record as runtime control, not infrastructure
- `import_playbook:` / `include_tasks:` → resolve and continue extraction

## Naming pattern hints
Ansible does not enforce naming. Detect variable templates used in `name:` arguments to cloud modules.

## Typical cross-stack dependencies
- Other Ansible playbooks via `import_playbook:`
- External secret stores via `community.hashi_vault.vault_kv2_get` and similar
- Cloud APIs via the cloud modules
