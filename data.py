POLICIES = [
    {
        "id": "policy_001",
        "section": "Corporate Communications",
        "text": (
            "Employees are encouraged to share general project milestones and team updates on "
            "public social media platforms like LinkedIn and X (formerly Twitter), provided that "
            "specific client names, proprietary code snippets, or internal revenue figures are "
            "strictly omitted."
        ),
    },
    {
        "id": "policy_002",
        "section": "Data Security & Sharing",
        "text": (
            "All internal source code must be hosted on enterprise Git repositories. Sharing "
            "anonymized architecture diagrams for educational purposes or tech blogs is "
            "permissible only after a peer review by a Senior Engineer."
        ),
    },
    {
        "id": "policy_003",
        "section": "Vendor Management",
        "text": (
            "Procurement of third-party SaaS tools under $5,000 annually can be approved directly "
            "by Department Heads without requiring a formal review from the legal or information "
            "security teams."
        ),
    },
]

REGULATIONS = {
    "REG_2026_PR_COMPLIANCE": (
        "To mitigate insider trading and reputational risk, all external public communications, "
        "social media updates, or technical publications regarding active company projects must "
        "receive explicit, documented pre-approval from the PR Compliance Committee prior to "
        "publication."
    ),
    "REG_2026_SEC_VENDOR": (
        "All external software vendors, micro-services, and digital tools interacting with company "
        "data - regardless of contract value or tier - must undergo a mandatory automated security "
        "scanning and static analysis review by the central InfoSec team."
    ),
}
