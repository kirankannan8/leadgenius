# Lead Risk Assessment & WhatsApp Outreach Tool

## Overview

This is a Streamlit-based lead management application that processes Excel files containing lead data, automatically assesses risk categories based on engagement metrics, and generates personalized WhatsApp outreach messages using AI. The system helps sales teams prioritize follow-ups by categorizing leads into High, Medium, and Low risk categories based on their interaction history and demo attendance patterns.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Streamlit Web Interface**: Single-page application with sidebar instructions and main content area for file upload and results display
- **Responsive Layout**: Wide layout configuration optimized for data table viewing and bulk operations
- **Interactive Components**: File uploader, data validation feedback, and downloadable results

### Backend Architecture
- **Modular Python Design**: Separated into three main modules:
  - `app.py`: Main Streamlit application and UI logic
  - `risk_assessment.py`: Business logic for categorizing leads based on engagement rules
  - `whatsapp_generator.py`: AI-powered message generation with fallback templates

### Risk Assessment Engine
- **Rule-Based Classification**: Deterministic logic using engagement metrics (missed demos, interaction days, contact sharing, link clicks)
- **Three-Tier Risk Categories**: 
  - High Risk: Missed demos, long inactivity, poor engagement
  - Medium Risk: Moderate engagement levels
  - Low Risk: Active participation and recent interactions
- **N/A Value Handling**: Supports N/A values in "Contact Shared" and "Last Interaction Days" columns with appropriate logic:
  - Contact Shared N/A: Treated as unfavorable (like "No")
  - Last Interaction Days N/A: Treated as fresh leads who scheduled but haven't interacted yet (0 days)
- **Data Validation**: Column validation and data type normalization for consistent processing

### Message Generation System
- **AI-Powered Personalization**: OpenAI GPT integration for context-aware message creation
- **Fallback Mechanism**: Template-based messages when AI service is unavailable
- **Risk-Aware Messaging**: Different tone and urgency based on lead risk category
- **Character Limit Optimization**: Messages kept under 160 characters for WhatsApp compatibility

### WhatsApp Integration System
- **Manual WhatsApp Links**: Clickable links that open WhatsApp with pre-filled messages
- **URL Encoding**: Proper encoding of messages for WhatsApp web links
- **Phone Number Formatting**: Automatic cleaning and formatting of phone numbers

### Data Processing Pipeline
- **Excel File Handling**: Pandas-based data ingestion with column validation
- **Batch Processing**: Processes all leads in uploaded file simultaneously
- **Data Export**: Downloadable results with original data plus risk scores and generated messages

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4o model for generating personalized WhatsApp messages
- **Environment Configuration**: API key management through environment variables

### Python Libraries
- **Streamlit**: Web application framework and UI components
- **Pandas**: Data manipulation and Excel file processing
- **OpenAI**: API client for message generation
- **Standard Libraries**: io, os, urllib.parse, re for data handling and utilities

### Data Requirements
- **Excel Input Format**: Requires specific column structure including Lead Name, Channel, Contact Number, Scheduled By, Link Clicked, Contact Shared, Last Interaction Days, Missed Demos, and Showed Up for Demo
- **N/A Support**: Contact Shared and Last Interaction Days columns can contain N/A values with contextual handling:
  - Contact Shared N/A: Treated as unfavorable
  - Last Interaction Days N/A: Treated as fresh leads (0 days - just scheduled)
- **No Database**: Stateless application processing uploaded files without persistent storage