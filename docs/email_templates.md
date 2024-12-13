# Email Templates Guide

## Template Structure
Email templates support both plain text and HTML formats with dynamic content placeholders.

### Available Placeholders
Common placeholders that can be used in templates:

- `{{name}}` - Recipient's full name
- `{{email}}` - Recipient's email address
- `{{company}}` - Company name
- `{{position}}` - Job position/title
- `{{department}}` - Department name
- `{{start_date}}` - Start date
- `{{manager_name}}` - Manager's name
- `{{project}}` - Project name
- `{{office_location}}` - Office location
- `{{team_size}}` - Team size
- `{{salary_band}}` - Salary band/level

## HTML Template Example

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Your CSS styles here */
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome to {{company}}</h1>
    </div>
    
    <div class="content">
        <p>Dear {{name}},</p>
        <!-- Content with placeholders -->
    </div>
    
    <div class="footer">
        <!-- Footer content -->
    </div>
</body>
</html>
```

## Best Practices

1. **HTML Structure**
   - Use inline CSS for email compatibility
   - Keep design mobile-responsive
   - Test across different email clients

2. **Placeholders**
   - Use clear, descriptive placeholder names
   - Document all placeholders used
   - Provide default values where possible

3. **Content**
   - Keep messages concise
   - Use proper formatting for readability
   - Include call-to-action buttons

4. **Testing**
   - Preview with different data sets
   - Test all placeholder replacements
   - Verify in multiple email clients

## Sample Templates

1. **Welcome Email**
   - Purpose: New employee onboarding
   - Key placeholders: name, position, department, start_date
   - [View Template](../examples/sample_templates/welcome_email.html)

2. **Newsletter**
   - Purpose: Regular company updates
   - Key placeholders: name, department, company
   - [View Template](../examples/sample_templates/newsletter.html)

## Bulk Sender Setup

When adding multiple Gmail senders via CSV, use the following format:

```csv
email,project_name,description,department
sender1@gmail.com,Marketing Campaign,Marketing team sender,Marketing
sender2@gmail.com,Sales Outreach,Sales team sender,Sales
```

[Download Sample Senders CSV](../examples/bulk_senders.csv)

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| name | Recipient's name | John Doe |
| email | Email address | john.doe@example.com |
| company | Company name | ACME Inc |
| position | Job title | Software Engineer |
| department | Department | Engineering |
| start_date | Start date | 2024-01-15 |
| manager_name | Manager's name | Sarah Johnson |
| project | Project name | Project X |
| office_location | Office location | New York |
| team_size | Team size | 8 |
| salary_band | Salary band | B4 |

## Troubleshooting

1. **Missing Placeholders**
   - Error: Placeholder not replaced
   - Solution: Verify CSV column names match template placeholders

2. **HTML Rendering Issues**
   - Error: Template not displaying correctly
   - Solution: Use email-safe HTML and CSS

3. **Character Encoding**
   - Error: Special characters not displaying correctly
   - Solution: Ensure UTF-8 encoding for templates and CSV files 