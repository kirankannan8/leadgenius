import pandas as pd

def assess_risk_category(row):
    """
    Assess risk category based on the provided business logic rules.
    
    Args:
        row: A pandas Series representing a single lead's data
        
    Returns:
        str: Risk category ('High', 'Medium', or 'Low')
    """
    
    # Extract values from the row
    missed_demos = int(row.get('Missed Demos', 0))
    
    # Handle N/A values for Last Interaction Days
    last_interaction_raw = row.get('Last Interaction Days', 0)
    if pd.isna(last_interaction_raw) or str(last_interaction_raw).strip().lower() == 'n/a':
        last_interaction_days = 0  # Treat N/A as fresh lead (just scheduled, no interaction yet)
    else:
        try:
            last_interaction_days = int(last_interaction_raw)
        except (ValueError, TypeError):
            last_interaction_days = 0
    
    # Handle N/A values for Contact Shared
    contact_shared_raw = row.get('Contact Shared', '')
    if pd.isna(contact_shared_raw) or str(contact_shared_raw).strip().lower() == 'n/a':
        contact_shared = 'n/a'
    else:
        contact_shared = str(contact_shared_raw).strip().lower()
    
    link_clicked = str(row.get('Link Clicked', '')).strip().lower()
    scheduled_by = str(row.get('Scheduled By', '')).strip().lower()
    showed_up_for_demo = str(row.get('Showed Up for Demo', '')).strip().lower()
    
    # Normalize boolean-like values
    contact_shared_yes = contact_shared in ['yes', 'y', '1', 'true']
    contact_shared_no = contact_shared in ['no', 'n', '0', 'false']
    contact_shared_na = contact_shared in ['n/a', 'na', '']
    link_clicked_yes = link_clicked in ['yes', 'y', '1', 'true']
    link_clicked_no = link_clicked in ['no', 'n', '0', 'false']
    showed_up_yes = showed_up_for_demo in ['yes', 'y', '1', 'true']
    scheduled_by_agent = scheduled_by in ['agent']
    scheduled_by_self = scheduled_by in ['self']
    
    # HIGH RISK CRITERIA
    # 1. Missed Demos ≥ 1
    if missed_demos >= 1:
        return 'High'
    
    # 2. Last Interaction Days > 10 AND Contact Shared = "No" (treat N/A as "No")
    if last_interaction_days > 10 and (contact_shared_no or contact_shared_na):
        return 'High'
    
    # 3. Link Clicked = "No" AND Scheduled By = "Agent"
    if link_clicked_no and scheduled_by_agent:
        return 'High'
    
    # LOW RISK CRITERIA (check before Medium to prioritize)
    # 1. Showed Up for Demo = "Yes"
    if showed_up_yes:
        return 'Low'
    
    # 2. Last Interaction Days ≤ 5 AND Contact Shared = "Yes"
    if last_interaction_days <= 5 and contact_shared_yes:
        return 'Low'
    
    # MEDIUM RISK CRITERIA
    # 1. Last Interaction Days between 5 and 10 AND Contact Shared = "Yes"
    if 5 < last_interaction_days <= 10 and contact_shared_yes:
        return 'Medium'
    
    # 2. Link Clicked = "Yes" BUT Missed Demos = 0
    if link_clicked_yes and missed_demos == 0:
        return 'Medium'
    
    # 3. Scheduled By = "Self" BUT No Shows = 0 AND Last Interaction Days > 5
    # Note: "No Shows" seems to refer to "Missed Demos" based on context
    if scheduled_by_self and missed_demos == 0 and last_interaction_days > 5:
        return 'Medium'
    
    # DEFAULT: If none of the above conditions are satisfied, assign Medium Risk
    return 'Medium'

def get_risk_statistics(df):
    """
    Calculate statistics for each risk category.
    
    Args:
        df: DataFrame with risk assessments
        
    Returns:
        dict: Statistics for each risk category
    """
    if 'Risk Score' not in df.columns:
        return {}
    
    risk_counts = df['Risk Score'].value_counts()
    total_leads = len(df)
    
    stats = {}
    for risk_level in ['High', 'Medium', 'Low']:
        count = risk_counts.get(risk_level, 0)
        percentage = (count / total_leads * 100) if total_leads > 0 else 0
        stats[risk_level] = {
            'count': count,
            'percentage': round(percentage, 1)
        }
    
    return stats

def validate_lead_data(row):
    """
    Validate that a lead row has all required fields for risk assessment.
    
    Args:
        row: A pandas Series representing a single lead's data
        
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    required_fields = [
        'Lead Name', 'Missed Demos', 'Last Interaction Days',
        'Contact Shared', 'Link Clicked', 'Scheduled By', 'Showed Up for Demo'
    ]
    
    for field in required_fields:
        if pd.isna(row.get(field)) or str(row.get(field)).strip() == '':
            errors.append(f"Missing or empty field: {field}")
    
    # Validate numeric fields
    try:
        int(row.get('Missed Demos', 0))
    except (ValueError, TypeError):
        errors.append("Missed Demos must be a number")
    
    # Validate Last Interaction Days (allow N/A)
    last_interaction_raw = row.get('Last Interaction Days', 0)
    if not (pd.isna(last_interaction_raw) or str(last_interaction_raw).strip().lower() == 'n/a'):
        try:
            int(last_interaction_raw)
        except (ValueError, TypeError):
            errors.append("Last Interaction Days must be a number or N/A")
    
    # Validate boolean-like fields (allow N/A for Contact Shared)
    boolean_fields_strict = ['Link Clicked', 'Showed Up for Demo']
    valid_boolean_values = ['yes', 'no', 'y', 'n', '1', '0', 'true', 'false']
    
    for field in boolean_fields_strict:
        value = str(row.get(field, '')).strip().lower()
        if value not in valid_boolean_values:
            errors.append(f"{field} must be Yes/No (found: '{row.get(field)}')")
    
    # Special validation for Contact Shared (allow N/A)
    contact_shared_value = str(row.get('Contact Shared', '')).strip().lower()
    valid_contact_shared_values = valid_boolean_values + ['n/a', 'na']
    if contact_shared_value not in valid_contact_shared_values:
        errors.append(f"Contact Shared must be Yes/No/N/A (found: '{row.get('Contact Shared')}')")
    
    # Validate Scheduled By field
    scheduled_by = str(row.get('Scheduled By', '')).strip().lower()
    if scheduled_by not in ['agent', 'self']:
        errors.append(f"Scheduled By must be 'Agent' or 'Self' (found: '{row.get('Scheduled By')}')")
    
    return len(errors) == 0, errors
