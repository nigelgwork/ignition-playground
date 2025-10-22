# Playbook Syntax Reference

Complete guide to writing YAML playbooks.

## Basic Structure

```yaml
name: "Playbook Name"
version: "1.0"
description: "What this playbook does"

parameters:
  - name: param_name
    type: string
    required: true
    description: "Parameter description"

steps:
  - id: step_id
    name: "Step Name"
    type: step.type
    parameters:
      key: value
```

## Parameters

### Parameter Types

- `string` - Text value
- `integer` - Whole number
- `float` - Decimal number
- `boolean` - true/false
- `file` - File path
- `credential` - Credential reference
- `list` - List of values
- `dict` - Dictionary/object

### Parameter Options

```yaml
parameters:
  - name: gateway_url
    type: string
    required: true           # Must be provided
    default: "http://localhost:8088"  # Default value
    description: "Gateway URL"
```

## Steps

### Gateway Steps

```yaml
# Login
- id: login
  type: gateway.login
  parameters:
    username: "admin"
    password: "{{ credential.gateway_admin.password }}"

# List modules
- id: list_modules
  type: gateway.list_modules

# Upload module
- id: upload
  type: gateway.upload_module
  parameters:
    file: "./perspective.modl"

# Wait for module
- id: wait_module
  type: gateway.wait_for_module_installation
  parameters:
    module_name: "Perspective"
    timeout: 300

# Restart Gateway
- id: restart
  type: gateway.restart
  parameters:
    wait_for_ready: true
```

### Browser Steps

```yaml
# Navigate
- id: navigate
  type: browser.navigate
  parameters:
    url: "http://example.com"
    wait_until: "networkidle"

# Click element
- id: click
  type: browser.click
  parameters:
    selector: "#submit-button"

# Fill form field
- id: fill
  type: browser.fill
  parameters:
    selector: "#username"
    value: "admin"

# Take screenshot
- id: screenshot
  type: browser.screenshot
  parameters:
    name: "page_capture"
    full_page: true

# Wait for element
- id: wait
  type: browser.wait
  parameters:
    selector: ".success-message"
    timeout: 10000
```

### Utility Steps

```yaml
# Sleep
- id: wait
  type: utility.sleep
  parameters:
    seconds: 5

# Log message
- id: log
  type: utility.log
  parameters:
    message: "Operation complete"
    level: "info"  # debug, info, warning, error

# Set variable
- id: set_var
  type: utility.set_variable
  parameters:
    name: "result"
    value: "success"
```

## Parameter References

### Types of References

```yaml
# Parameter reference
"{{ parameter.gateway_url }}"

# Credential reference
"{{ credential.gateway_admin }}"
"{{ credential.gateway_admin.username }}"
"{{ credential.gateway_admin.password }}"

# Variable reference (set during execution)
"{{ variable.module_name }}"
```

### Reference in Strings

```yaml
parameters:
  url: "http://{{ parameter.host }}:{{ parameter.port }}"
  message: "User {{ credential.admin.username }} logged in"
```

## Step Options

### Timeout

```yaml
- id: step1
  type: gateway.restart
  timeout: 600  # seconds
```

### Retry

```yaml
- id: step1
  type: gateway.ping
  retry_count: 3      # Retry 3 times
  retry_delay: 5      # Wait 5 seconds between retries
```

### Error Handling

```yaml
- id: step1
  type: gateway.upload_module
  on_failure: abort     # abort, continue, rollback
```

## Complete Example

```yaml
name: "Gateway Module Upgrade"
version: "1.0"
description: "Upload and install a Gateway module"

parameters:
  - name: gateway_url
    type: string
    required: true
    description: "Gateway URL"

  - name: gateway_credential
    type: credential
    required: true
    description: "Gateway admin credential"

  - name: module_file
    type: file
    required: true
    description: "Path to .modl file"

  - name: module_name
    type: string
    required: true
    description: "Module name (e.g., Perspective)"

steps:
  - id: login
    name: "Login to Gateway"
    type: gateway.login
    parameters:
      username: "{{ credential.gateway_credential.username }}"
      password: "{{ credential.gateway_credential.password }}"
    timeout: 30

  - id: list_before
    name: "List Modules Before"
    type: gateway.list_modules
    on_failure: continue

  - id: upload
    name: "Upload Module"
    type: gateway.upload_module
    parameters:
      file: "{{ parameter.module_file }}"
    timeout: 300
    retry_count: 2
    retry_delay: 10

  - id: wait
    name: "Wait for Installation"
    type: gateway.wait_for_module_installation
    parameters:
      module_name: "{{ parameter.module_name }}"
      timeout: 300

  - id: restart
    name: "Restart Gateway"
    type: gateway.restart
    parameters:
      wait_for_ready: true
    timeout: 600

  - id: verify
    name: "Verify Health"
    type: gateway.get_health
    retry_count: 3
    retry_delay: 5

metadata:
  author: "Your Name"
  category: "gateway"
  tags: ["module", "upgrade"]
```

## Best Practices

1. **Use descriptive IDs** - Make step IDs clear and unique
2. **Add descriptions** - Document what parameters do
3. **Set timeouts** - Prevent hanging on slow operations
4. **Handle failures** - Use `on_failure` appropriately
5. **Use retries** - For flaky operations
6. **Secure credentials** - Use credential references, not plain text
7. **Add metadata** - Author, category, tags for organization
