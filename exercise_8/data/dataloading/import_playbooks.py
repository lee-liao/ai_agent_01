import redis
import json
import uuid
import os

def import_playbooks():
    """
    Import sample playbooks into Redis for the Exercise 8 application
    """
    # Connect to Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        print("[SUCCESS] Successfully connected to Redis")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Redis: {e}")
        print("Make sure Redis is running (try: docker-compose up redis)")
        return

    # Sample playbooks based on the application requirements
    sample_playbooks = [
        {
            "name": "SaaS MSA Policy",
            "rules": {
                "liability_cap": "12 months fees",
                "payment_terms": "Net 30",
                "auto_renewal": True,
                "termination_notice": "90 days",
                "requires_subprocessors_list": True,
                "dpa_reference_sccs": True,
                "security_standards": ["SOC2", "ISO27001"]
            }
        },
        {
            "name": "GDPR DPA Policy",
            "rules": {
                "data_retention": "90 days post-term",
                "required_clauses": ["SCC", "audit rights"],
                "subprocessor_approval": "prior written",
                "breach_notification": "72 hours"
            }
        },
        {
            "name": "NDA Policy",
            "rules": {
                "confidentiality_period": "3 years",
                "purpose_limitation": True,
                "return_obligation": True,
                "non_solicitation": "6 months post-termination",
                "governing_law": "${country}",
                "jurisdiction": "${courts_of_jurisdiction}"
            }
        },
        {
            "name": "Comprehensive NDA Policy",
            "rules": {
                "confidential_information_definition": {
                    "broad_scope": True,
                    "form_agnostic": True,
                    "designation_not_required": True,
                    "circumstantial_protection": True,
                    "temporal_coverage": True,
                    "ownership_clarity": True,
                    "catch_all_safeguard": True
                },
                "confidentiality_period": {
                    "duration": "3 years",
                    "commencement_trigger": "last party signs",
                    "survival_clause": True
                },
                "purpose_limitations": {
                    "specificity": True,
                    "multiple_permissible_uses": [
                        "explore formalise commercial relationship",
                        "marketing discloser offerings",
                        "evaluate supplier fit"
                    ],
                    "purpose_limiting_language": True
                },
                "recipient_obligations": {
                    "core_confidentiality": True,
                    "use_restrictions": True,
                    "internal_access_control": True,
                    "prohibition_on_misuse": True,
                    "breach_notification_duty": True,
                    "standard_exclusions": [
                        "publicly_available",
                        "already_known",
                        "independently_developed",
                        "approved_in_writing"
                    ]
                },
                "disclosure_by_law": {
                    "mandatory_exception": True,
                    "advance_notice": True,
                    "cooperation_requirement": True,
                    "mitigation_efforts": True
                },
                "return_of_confidential_info": {
                    "discloser_initiated": True,
                    "comprehensive_scope": True,
                    "certification_required": True
                },
                "non_solicitation": {
                    "covers_both_term_and_post": True,
                    "applies_to_direct_and_indirect": True,
                    "duration": "6 months"
                },
                "ip_ownership": {
                    "clear_ownership_statement": True,
                    "no_rights_transferred": True,
                    "covers_all_forms_of_transfer": True
                },
                "accuracy_disclaimer": {
                    "no_representations_or_warranties": True,
                    "as_is_with_all_faults": True,
                    "liability_disclaimer": True
                },
                "indemnity": {
                    "broad_coverage": True,
                    "includes_attorneys_fees": True,
                    "covers_direct_and_indirect_loss": True
                }
            }
        },
        {
            "name": "Sample Policy from File",
            "rules": {
                "liability_cap": "12 months fees",
                "requires_subprocessors_list": True,
                "dpa_reference_sccs": True,
                "security_standards": ["SOC2", "ISO27001"]
            }
        }
    ]

    print(f"[INFO] Importing {len(sample_playbooks)} sample playbooks...")

    for i, playbook in enumerate(sample_playbooks, 1):
        playbook_id = f"playbook_{uuid.uuid4().hex[:8]}"
        playbook_key = f"playbook:{playbook_id}"
        
        # Store the playbook in Redis
        r.set(playbook_key, json.dumps(playbook))
        
        print(f"  {i}. Added '{playbook['name']}' with ID: {playbook_id}")

    # Verify the import by listing all playbooks
    print("\n[INFO] Verifying imported playbooks...")
    playbook_keys = r.keys("playbook:*")
    print(f"Total playbooks in Redis: {len(playbook_keys)}")
    
    for key in playbook_keys:
        pb_data = json.loads(r.get(key))
        print(f"  - {pb_data['name']} ({key})")

    print("\n[SUCCESS] Playbook import completed successfully!")

if __name__ == "__main__":
    import_playbooks()