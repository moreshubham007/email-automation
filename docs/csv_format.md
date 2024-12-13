# CSV Format Documentation

## Basic Structure
The CSV file must include required columns and can contain additional custom fields that match your template placeholders.

### Required Columns
- `template_name`: Must match exactly with one of your saved templates
- `sender_email`: Gmail account that will send the email (must be authenticated)
- `email`: Recipient's email address

### Common Optional Columns
- `name`: Recipient's full name
- `company`: Company or organization name
- `position`: Job title or position
- Any other columns that match your template placeholders

## Example CSV Format

```csv
template_name,sender_email,name,email,company,position
Welcome_Template,hr.sender@gmail.com,John Doe,john.doe@gmail.com,ACME Inc,Software Engineer
Newsletter_Template,news.sender@gmail.com,Jane Smith,jane.smith@gmail.com,XYZ Corp,Product Manager
```

## Load Distribution Guidelines

1. **Sender Rotation**
   - Distribute recipients across multiple senders
   - Stay within Gmail's daily sending limits (2000/day/account)
   - Example: 
     ```csv
     Welcome_Template,hr.sender1@gmail.com,John Doe,john@example.com,ACME,Engineer
     Welcome_Template,hr.sender2@gmail.com,Jane Smith,jane@example.com,ACME,Designer
     ```

2. **Department-based Distribution**
   - Match senders with appropriate departments
   - Example:
     ```csv
     Welcome_Template,hr.dept@gmail.com,John Doe,john@example.com,ACME,HR
     Sales_Template,sales.dept@gmail.com,Jane Smith,jane@example.com,ACME,Sales
     ```

## Best Practices

1. **Sender Management**
   - Verify all sender emails are authenticated in the system
   - Distribute load evenly across senders
   - Group similar recipients with the same sender

2. **Template Matching**
   - Ensure templates exist for each template_name
   - Match sender expertise with template type
   - Consider time zones when assigning senders

## Example Scenarios

### HR Onboarding
```csv
template_name,sender_email,name,email,company,position,start_date
Welcome_Template,hr.west@gmail.com,John Doe,john@example.com,ACME,Engineer,2024-01-15
Welcome_Template,hr.east@gmail.com,Jane Smith,jane@example.com,ACME,Designer,2024-01-16
```

### Newsletter Distribution
```csv
template_name,sender_email,name,email,department,region
Newsletter_Template,news.us@gmail.com,John Doe,john@example.com,Sales,US
Newsletter_Template,news.eu@gmail.com,Jane Smith,jane@example.com,Marketing,EU
```

## Error Prevention

1. **Sender Verification**
   - Error: "Sender email not authenticated"
   - Solution: Ensure sender is added and authenticated in system

2. **Load Balancing**
   - Error: "Daily sending limit exceeded"
   - Solution: Distribute recipients across more senders

3. **Template Matching**
   - Error: "Template not found"
   - Solution: Verify template names match exactly 