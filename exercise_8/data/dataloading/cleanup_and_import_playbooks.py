import redis
import json
import uuid
import os

def cleanup_and_import_playbooks():
    """
    Clean up duplicate playbooks and import the necessary ones
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

    # Load the actual playbook data from the JSON file
    try:
        with open("D:/MyCode/AI/Victoria/lesson3/ai_agent_01/exercise_8/data/policies/playbook.json", "r", encoding="utf-8") as f:
            playbook_data = json.load(f)
    except FileNotFoundError:
        print("[ERROR] Could not find playbook.json at the expected path")
        return

    # Convert the detailed playbook data into a structure usable by the application
    nda_policy_rules = {}
    
    for clause_policy in playbook_data:
        clause_name = clause_policy.get("clause", "unnamed_clause").replace(" ", "_").replace("-", "_").lower()
        nda_policy_rules[clause_name] = {
            "ideal": clause_policy.get("ideal", ""),
            "red_flag": clause_policy.get("red_flag", ""),
            "acceptable": clause_policy.get("acceptable", ""),
            "is_required": clause_policy.get("is_required", False),
            "clause_definition": clause_policy.get("clause_definition", ""),
            "review_instruction": clause_policy.get("review_instruction", ""),
            "example_ideal_clause": clause_policy.get("example_ideal_clause", ""),
            "example_fallback_clause": clause_policy.get("example_fallback_clause", "")
        }

    # Create the comprehensive NDA playbook from the detailed data
    comprehensive_nda_playbook = {
        "name": "Comprehensive NDA Policy Rules",
        "rules": nda_policy_rules
    }

    # Create a simplified version
    simplified_nda_playbook = {
        "name": "Simplified NDA Policy",
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
            }
        }
    }

    # Define all the playbooks we want to have
    desired_playbooks = [
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
            "name": "Basic NDA Policy",
            "rules": {
                "confidentiality_period": "3 years",
                "purpose_limitation": True,
                "return_obligation": True,
                "non_solicitation": "6 months post-termination",
                "governing_law": "${country}",
                "jurisdiction": "${courts_of_jurisdiction}"
            }
        },
        comprehensive_nda_playbook,
        simplified_nda_playbook,
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

    # Clean up all existing playbooks
    print("[INFO] Removing existing playbooks to avoid duplicates...")
    existing_playbook_keys = r.keys("playbook:*")
    for key in existing_playbook_keys:
        r.delete(key)
    
    print(f"[INFO] Removed {len(existing_playbook_keys)} existing playbook entries")

    # Add the desired playbooks
    print(f"[INFO] Adding {len(desired_playbooks)} unique playbooks...")
    for i, playbook in enumerate(desired_playbooks, 1):
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

    print("\n[SUCCESS] Clean playbook import completed successfully!")

if __name__ == "__main__":
    cleanup_and_import_playbooks()