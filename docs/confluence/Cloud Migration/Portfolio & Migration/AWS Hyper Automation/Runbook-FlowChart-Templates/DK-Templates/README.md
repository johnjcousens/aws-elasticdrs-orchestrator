# DK-Templates

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866999592/DK-Templates

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:20 AM

---

Runbook Templates
-----------------

### Migration runbooks

The provided flowcharts are base templates for:

**1.** Discovery and Analysis activities
**2.** Wave Planning and Design activities
**3.** Server Rehost activities

. Each flowchart template has its own tab in the same file which reduces the number of imports required when creating Cutover.com templates. The conversion automation supports using an export of the entire document as CSV (for LucidChart) or simply using the `.drawio` file (for DrawIO). It will then parse each template accordingly (see

for more details).

**Note:** If you don't want to convert all tabs at the same time then save them in independent DrawIO files or LucidChart workspaces.

Stay tuned for more runbook templates being added.

These templates are intended to be adapted for your customer and then added to the Hyper Automation Solution for automated conversion into Cutover.com runbook templates to perform actual migrations.

The templates are pre-configuerd with automation IDs for those tasks that have an equivalent automation in the

. Check the metadata attributes of each task and refer to thefor more information about best practices for editing these templates.

### Configuration runbooks (Cutover.com Bootstrapping)

This delivery kits includes one runbook to perform one-time bootstrapping activities of your Cutover.com instance. Download this template