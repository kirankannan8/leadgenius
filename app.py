import streamlit as st
import pandas as pd
import io
import os
from urllib.parse import quote
import re
from risk_assessment import assess_risk_category
from whatsapp_generator import generate_whatsapp_message
from whatsapp_sender import get_whatsapp_sender

# Page configuration
st.set_page_config(
    page_title="Lead Risk Assessment & WhatsApp Outreach",
    page_icon="📊",
    layout="wide"
)

# Initialize WhatsApp sender
whatsapp_sender = get_whatsapp_sender()

# Main title
st.title("📊 Lead Risk Assessment & WhatsApp Outreach")
st.markdown("Upload your Excel file to process leads, assess risk categories, and generate personalized WhatsApp messages.")

# Sidebar for instructions
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    **Required Excel Columns:**
    - Lead Name
    - Channel
    - Contact Number
    - Scheduled By
    - Link Clicked
    - Contact Shared *(can be N/A)*
    - Last Interaction Days *(can be N/A)*
    - Missed Demos
    - Showed Up for Demo
    
    **Risk Categories:**
    - 🔴 **High Risk**: Missed demos, long inactivity
    - 🟡 **Medium Risk**: Moderate engagement
    - 🟢 **Low Risk**: Active and engaged leads
    
    **Note:** N/A values are handled appropriately:
    - Contact Shared N/A: Treated as unfavorable
    - Last Interaction Days N/A: Treated as fresh lead (0 days)
    
  )

def validate_excel_columns(df):
    """Validate that the Excel file contains all required columns"""
    required_columns = [
        'Lead Name', 'Channel', 'Contact Number', 'Scheduled By',
        'Link Clicked', 'Contact Shared', 'Last Interaction Days',
        'Missed Demos', 'Showed Up for Demo'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    return missing_columns

def clean_phone_number(phone):
    """Clean phone number to contain only digits"""
    if pd.isna(phone):
        return None
    # Convert to string and remove all non-numeric characters
    cleaned = re.sub(r'\D', '', str(phone))
    return cleaned if cleaned else None

def create_whatsapp_link(phone_number, message):
    """Create a clickable WhatsApp link using WhatsApp sender"""
    return whatsapp_sender.create_whatsapp_link(phone_number, message)

def get_risk_emoji(risk_score):
    """Get emoji for risk score"""
    emoji_map = {
        'High': '🔴',
        'Medium': '🟡',
        'Low': '🟢'
    }
    return emoji_map.get(risk_score, '⚪')

# File upload section
st.header("📁 Upload Excel File")

col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Choose an Excel file (.xlsx or .xls)",
        type=['xlsx', 'xls'],
        help="Upload your lead data file with all required columns"
    )

with col2:
    st.markdown("**Send Options:**")
    send_mode = st.radio(
        "Choose sending method:",
        ["Manual Links Only", "Auto-Send via WhatsApp API"] if whatsapp_configured else ["Manual Links Only"],
        help="Auto-send requires WhatsApp Cloud API configuration"
    )

if uploaded_file is not None:
    try:
        # Read the Excel file
        with st.spinner("📖 Reading Excel file..."):
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File uploaded successfully! Found {len(df)} leads.")
        
        # Validate columns
        missing_columns = validate_excel_columns(df)
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            st.stop()
        
        # Display original data preview
        with st.expander("👀 Preview Original Data", expanded=False):
            st.dataframe(df.head(10))
        
        # Process leads
        st.header("⚙️ Processing Leads")
        
        # Auto-send confirmation
        auto_send = send_mode == "Auto-Send via WhatsApp API"
        if auto_send:
            st.info("🚀 Auto-send mode enabled. Messages will be sent automatically to valid phone numbers.")
            confirm_send = st.checkbox("I confirm I want to send WhatsApp messages automatically", value=False)
            if not confirm_send:
                st.warning("⚠️ Please confirm to proceed with auto-sending messages.")
                st.stop()
        
        # Initialize progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        processed_data = []
        send_results = []
        
        for index, row in df.iterrows():
            # Update progress
            progress = (int(index) + 1) / len(df)
            progress_bar.progress(progress)
            status_text.text(f"Processing lead {int(index) + 1} of {len(df)}: {row['Lead Name']}")
            
            # Clean and validate phone number
            clean_phone = clean_phone_number(row['Contact Number'])
            
            if not clean_phone:
                # Skip leads with invalid phone numbers
                processed_data.append({
                    'Lead Name': row['Lead Name'],
                    'Risk Score': 'Invalid Phone',
                    'WhatsApp Message': 'N/A - Invalid phone number',
                    'WhatsApp Link': 'N/A',
                    'Send Status': 'N/A'
                })
                continue
            
            # Assess risk category
            try:
                risk_score = assess_risk_category(row)
            except Exception as e:
                st.warning(f"⚠️ Error assessing risk for {row['Lead Name']}: {str(e)}")
                risk_score = 'Medium'  # Default fallback
            
            # Generate WhatsApp message
            try:
                whatsapp_message = generate_whatsapp_message(row['Lead Name'], risk_score)
            except Exception as e:
                st.warning(f"⚠️ Error generating message for {row['Lead Name']}: {str(e)}")
                # Fallback to template messages
                message_templates = {
                    'High': f"Hi {row['Lead Name']}, your demo is scheduled but we missed you last time. Can we quickly reconnect today or tomorrow?",
                    'Medium': f"Hi {row['Lead Name']}, just checking in. Shall we go ahead with the demo this week?",
                    'Low': f"Hey {row['Lead Name']}, just a friendly nudge to confirm our upcoming demo. Excited to connect!"
                }
                whatsapp_message = message_templates.get(risk_score, f"Hi {row['Lead Name']}, let's connect!")
            
            # Create WhatsApp link
            whatsapp_link = create_whatsapp_link(clean_phone, whatsapp_message)
            
            # Auto-send message if enabled
            send_status = "Not Sent"
            send_error = None
            
            if auto_send and clean_phone and whatsapp_message:
                try:
                    send_result = whatsapp_sender.send_text_message(clean_phone, whatsapp_message)
                    if send_result["success"]:
                        send_status = "✅ Sent"
                        send_results.append({
                            "lead_name": row['Lead Name'],
                            "phone": clean_phone,
                            "status": "success",
                            "message_id": send_result["message_id"]
                        })
                    else:
                        send_status = "❌ Failed"
                        send_error = send_result["error"]
                        send_results.append({
                            "lead_name": row['Lead Name'],
                            "phone": clean_phone,
                            "status": "failed",
                            "error": send_error
                        })
                except Exception as e:
                    send_status = "❌ Error"
                    send_error = str(e)
                    send_results.append({
                        "lead_name": row['Lead Name'],
                        "phone": clean_phone,
                        "status": "error",
                        "error": send_error
                    })
            
            processed_data.append({
                'Lead Name': row['Lead Name'],
                'Risk Score': risk_score,
                'WhatsApp Message': whatsapp_message,
                'WhatsApp Link': whatsapp_link,
                'Send Status': send_status
            })
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Create results dataframe
        results_df = pd.DataFrame(processed_data)
        
        # Display results
        st.success(f"🎉 Processing complete! Processed {len(results_df)} leads.")
        
        # Auto-send results summary
        if auto_send and send_results:
            st.header("📤 Auto-Send Results")
            
            successful_sends = len([r for r in send_results if r['status'] == 'success'])
            failed_sends = len([r for r in send_results if r['status'] in ['failed', 'error']])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("✅ Successfully Sent", successful_sends)
            
            with col2:
                st.metric("❌ Failed to Send", failed_sends)
            
            with col3:
                success_rate = (successful_sends / len(send_results) * 100) if send_results else 0
                st.metric("📈 Success Rate", f"{success_rate:.1f}%")
            
            # Show failed sends if any
            if failed_sends > 0:
                with st.expander(f"❌ View Failed Sends ({failed_sends})", expanded=False):
                    failed_data = []
                    for result in send_results:
                        if result['status'] in ['failed', 'error']:
                            failed_data.append({
                                'Lead Name': result['lead_name'],
                                'Phone': result['phone'],
                                'Error': result.get('error', 'Unknown error')
                            })
                    
                    if failed_data:
                        failed_df = pd.DataFrame(failed_data)
                        st.dataframe(failed_df, use_container_width=True)
        
        # Risk category summary
        st.header("📊 Risk Category Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        high_risk_count = len(results_df[results_df['Risk Score'] == 'High'])
        medium_risk_count = len(results_df[results_df['Risk Score'] == 'Medium'])
        low_risk_count = len(results_df[results_df['Risk Score'] == 'Low'])
        invalid_count = len(results_df[results_df['Risk Score'] == 'Invalid Phone'])
        
        with col1:
            st.metric("🔴 High Risk", high_risk_count)
        
        with col2:
            st.metric("🟡 Medium Risk", medium_risk_count)
        
        with col3:
            st.metric("🟢 Low Risk", low_risk_count)
        
        with col4:
            st.metric("❌ Invalid Phone", invalid_count)
        
        # Display results table
        st.header("📋 Results Table")
        
        # Add risk emoji to the display
        display_df = results_df.copy()
        display_df['Risk Score'] = display_df['Risk Score'].apply(
            lambda x: f"{get_risk_emoji(x)} {x}"
        )
        
        # Make WhatsApp links clickable in the display
        display_df['WhatsApp Link'] = display_df.apply(
            lambda row: f"[Open WhatsApp]({row['WhatsApp Link']})" 
            if row['WhatsApp Link'] != 'N/A' else 'N/A', axis=1
        )
        
        # Configure column display
        column_config = {
            "WhatsApp Link": st.column_config.LinkColumn(
                "WhatsApp Link",
                help="Click to open WhatsApp with pre-filled message"
            )
        }
        
        # Hide Send Status column if not using auto-send
        if not auto_send:
            display_df = display_df.drop('Send Status', axis=1, errors='ignore')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config=column_config
        )
        
        # Download results
        st.header("💾 Download Results")
        
        # Create downloadable CSV
        csv_buffer = io.StringIO()
        results_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_data,
            file_name=f"lead_risk_assessment_results.csv",
            mime="text/csv",
            help="Download the processed results as a CSV file"
        )
        
        # Filter options
        st.header("🔍 Filter Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            risk_filter = st.selectbox(
                "Filter by Risk Score:",
                options=['All', 'High', 'Medium', 'Low', 'Invalid Phone'],
                index=0
            )
        
        with col2:
            search_term = st.text_input(
                "Search Lead Names:",
                placeholder="Enter lead name to search..."
            )
        
        # Apply filters
        filtered_df = results_df.copy()
        
        if risk_filter != 'All':
            filtered_df = filtered_df[filtered_df['Risk Score'] == risk_filter]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['Lead Name'].astype(str).str.contains(search_term, case=False, na=False)
            ]
        
        if len(filtered_df) != len(results_df):
            st.subheader(f"Filtered Results ({len(filtered_df)} leads)")
            
            # Add emoji to filtered display
            filtered_display_df = filtered_df.copy()
            filtered_display_df['Risk Score'] = filtered_display_df['Risk Score'].astype(str).apply(
                lambda x: f"{get_risk_emoji(x)} {x}"
            )
            
            filtered_display_df['WhatsApp Link'] = filtered_display_df.apply(
                lambda row: f"[Open WhatsApp]({row['WhatsApp Link']})" 
                if row['WhatsApp Link'] != 'N/A' else 'N/A', axis=1
            )
            
            st.dataframe(
                filtered_display_df,
                use_container_width=True,
                column_config={
                    "WhatsApp Link": st.column_config.LinkColumn(
                        "WhatsApp Link",
                        help="Click to open WhatsApp with pre-filled message"
                    )
                }
            )
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.info("Please ensure your file is a valid Excel file with all required columns.")

else:
    # Show sample data format
    st.info("👆 Please upload an Excel file to get started.")
    
    with st.expander("📋 Sample Data Format", expanded=False):
        sample_data = {
            'Lead Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'Channel': ['Website', 'Social Media', 'Referral', 'Email'],
            'Contact Number': ['+1234567890', '9876543210', '+44123456789', '5551234567'],
            'Scheduled By': ['Agent', 'Self', 'Agent', 'Self'],
            'Link Clicked': ['Yes', 'No', 'Yes', 'No'],
            'Contact Shared': ['Yes', 'No', 'N/A', 'Yes'],
            'Last Interaction Days': [3, 15, 'N/A', 8],
            'Missed Demos': [0, 2, 1, 0],
            'Showed Up for Demo': ['Yes', 'No', 'No', 'Yes']
        }
        
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Notes:**")
st.markdown("- Ensure you have the OpenAI API key configured for AI message generation")
st.markdown("- For automatic WhatsApp sending, configure the WhatsApp Cloud API credentials")
st.markdown("- Manual WhatsApp links work without any API configuration")
