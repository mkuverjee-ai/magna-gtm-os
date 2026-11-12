# Freckle Dataset Signals Reference

Dataset Signals watch the Dataset Entries a workspace already keeps in one input Dataset and append provider findings to a separate output Dataset in the same Workbook. The input Dataset is the desired monitor set: adding a Dataset Entry requests a monitor, editing a Dataset Entry safely deactivates and replaces its remote monitor, and deleting a Dataset Entry requests remote cleanup. Deleting the Signal Provider Configuration requests cleanup for every monitor.

Provisioning and deletion are asynchronous. Commands report the configuration status plus aggregate monitor counts (`provisioning`, `active`, `failed`, `deleting`, and `deleted`); use `signals get` to follow progress. A successful create or delete command confirms that Freckle accepted the request, not that every remote monitor has already reached its terminal state.

Signals use Freckle-managed provider credentials and polling. Never ask for or pass a provider API key, webhook URL or secret, event key path, bulk id, or remote radar id.

## Create

The CLI supports every backend Signal type:

- Filterable company: `company_job_openings`, `company_new_hires`, `company_promotions`, and `company_social_posts_cxo`.
- Other company: `company_reviews`, `company_mentions`, `company_social_posts`, and `company_social_engagements`.
- Contact: `contact_job_changes`, `contact_social_posts`, and `contact_social_engagements`.
- Industry: `industry_mentions`, `industry_funding_rounds`, `industry_new_companies`, and `industry_job_openings`.

Every company type requires `--company-domain-path`; `--company-profile-url-path` is optional. Filterable company types also accept repeatable `--department`, repeatable `--seniority`, and `--job-titles`:

```bash
freckle signals create <input-dataset-id> <output-dataset-id> \
  --signal-type company_new_hires \
  --company-domain-path /company/domain \
  --company-profile-url-path /company/linkedinUrl
```

Company social engagements use the same company mapping:

```bash
freckle signals create <input-dataset-id> <output-dataset-id> \
  --signal-type company_social_engagements \
  --company-domain-path /company/domain
```

Contact job-change monitoring also requires a company domain and at least one contact identifier. Supply any combination of contact email, profile URL, and full name pointers:

```bash
freckle signals create <input-dataset-id> <output-dataset-id> \
  --signal-type contact_job_changes \
  --company-domain-path /company/domain \
  --contact-email-path /contact/email \
  --contact-profile-url-path /contact/linkedinUrl
```

Contact social types require only `--contact-profile-url-path`:

```bash
freckle signals create <input-dataset-id> <output-dataset-id> \
  --signal-type contact_social_engagements \
  --contact-profile-url-path /contact/linkedinUrl
```

`industry_mentions` and `industry_job_openings` require `--keyword-path`. The keyword is optional for `industry_funding_rounds` and `industry_new_companies`. Industry types accept up to five repeatable uppercase ISO country codes:

```bash
freckle signals create <input-dataset-id> <output-dataset-id> \
  --signal-type industry_mentions \
  --keyword-path /industry/keyword \
  --country US \
  --country GB
```

All types accept `--include-historical`.

Both Datasets must be active, distinct, and in the same Workbook. Creation prints the Signal Provider Configuration id and a `signals get` command. It does not wait for remote provisioning.

## Inspect and list

```bash
freckle signals list <input-dataset-id>
freckle signals get <signal-provider-configuration-id>
freckle signals list <input-dataset-id> --json
freckle signals get <signal-provider-configuration-id> --json
```

Output contains only product configuration and safe lifecycle data. It never contains managed credentials, remote radar ids, bulk correlation, leases, or raw provider errors.

## Delete

```bash
freckle signals delete <signal-provider-configuration-id>
freckle signals delete <signal-provider-configuration-id> --json
```

Delete is idempotent and asynchronous. Repeating it is safe. Historical findings remain in the output Dataset while remote monitors drain; late polled findings are ignored and do not create new Dataset Entries or Workflow admissions. Poll `signals get` until the configuration is `deleted`.

This release slice is CLI and backend only. It does not include a Signals UI, billing, credits, subscriptions, pricing behavior, or customer-supplied provider keys.
