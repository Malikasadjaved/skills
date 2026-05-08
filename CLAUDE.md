# CLAUDE.md

This repo publishes agent skills for the [skills.sh](https://skills.sh) ecosystem — installable packages that give Claude Code domain-specific knowledge and patterns.

## Repo structure

```
qdrant-fastapi-integration/   # Skill: Qdrant + FastAPI integration patterns
fastapi-best-practices/       # Skill: FastAPI production patterns
whatsapp-cloud-api-agent/     # Skill: WhatsApp Cloud API agent backend
README.md                     # Skills catalog table + install commands
```

Each skill directory contains:
- `SKILL.md` — frontmatter (name, description, triggers, version, author) + full reference
- `references/` — cheatsheets and supplementary docs loaded into context when the skill activates
- `scripts/` — runnable examples for the skill's patterns

## Publishing a new skill or updating an existing one

1. The skill lives entirely in its directory. No build step — skills.sh reads the repo directly.
2. The `name` in SKILL.md frontmatter is the install path: `npx skills add malikasadjaved/skills@<name>`
3. After pushing to `main`, the skill is immediately installable — skills.sh indexes on every push.
4. **triggers** in frontmatter determine when the skill auto-activates. Use specific, searchable phrases that match what a developer would type (e.g., "whatsapp webhook", "tenant isolation qdrant").

## Conventions

- `main` branch, not `master`
- Conventional commits (`feat:`, `fix:`, `docs:`)
- README table must stay in sync with actual skill directories and names
- Each skill's description in SKILL.md frontmatter should differentiate it from official/competing skills
