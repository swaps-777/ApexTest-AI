# Testing Best Practices Knowledge Base

This document contains practical testing guidelines for generating high-quality software test cases from JIRA stories, requirements, and acceptance criteria.

---

## 1. Test Case Writing Standard

Every test case should be clear, testable, and traceable to a requirement or acceptance criterion.

A good test case should include:

- Test Case ID
- Test Case Title
- Test Type
- Priority
- Preconditions
- Test Data
- Test Steps
- Expected Result
- Mapped Acceptance Criteria
- Assumptions, if any

A test case should not be vague. Each expected result should be measurable and verifiable.

Bad expected result:

- System should work properly.

Good expected result:

- User should be redirected to the dashboard page after successful login.

---

## 2. Functional Testing Guidelines

Functional test cases verify that the system behaves as expected according to the requirement.

Functional tests should cover:

- Main happy path
- Core business flow
- Valid user actions
- Valid data submission
- Correct system response
- Correct navigation
- Correct status or confirmation message
- Correct data saved or displayed

Example:

For a login feature, functional tests should include:

- Login with valid username and password
- Successful redirection after login
- Correct user dashboard displayed
- Session created after successful login

---

## 3. Negative Testing Guidelines

Negative testing verifies how the system behaves when invalid, unexpected, or incorrect input is provided.

Negative tests should cover:

- Blank mandatory fields
- Invalid input format
- Invalid credentials
- Invalid user role or permission
- Unauthorized access
- Duplicate submission
- Invalid state transition
- Expired session
- Invalid file type
- Invalid API payload
- Invalid authentication token
- Malformed request
- Special characters in input fields
- Very large input values
- Whitespace-only values

Example:

For a login feature, negative tests should include:

- Login with invalid password
- Login with unregistered email
- Login with blank email
- Login with blank password
- Login with locked account
- Login with inactive account

---

## 4. Boundary Value Analysis

Boundary Value Analysis should be used when a field has minimum and maximum limits.

For every field with length, count, amount, date range, or numeric limit, test:

- Minimum valid value
- Maximum valid value
- Just below minimum value
- Just above minimum value
- Empty value
- Null value
- Very large value
- Decimal value, if applicable
- Negative value, if applicable
- Zero, if applicable

Example:

If password length must be 8 to 20 characters, test:

- 7 characters
- 8 characters
- 9 characters
- 19 characters
- 20 characters
- 21 characters

---

## 5. Equivalence Partitioning

Equivalence Partitioning divides input data into valid and invalid groups.

Instead of testing every possible value, test representative values from each class.

Example:

If age must be between 18 and 60:

Valid partitions:

- 18
- 30
- 60

Invalid partitions:

- 17
- 61
- Empty value
- Alphabetic value
- Special characters

---

## 6. Mandatory Field Testing

For every mandatory field, generate test cases for:

- Field left blank
- Field containing only spaces
- Field containing null value
- Valid value entered
- Error message displayed when field is blank
- Form submission blocked when mandatory field is blank

Expected result should verify:

- Correct validation message
- User cannot proceed
- Field is highlighted, if applicable
- No data is saved

---

## 7. UI Testing Checklist

UI test cases should verify that the screen behaves correctly for the user.

UI tests should cover:

- Page loads successfully
- All required fields are visible
- Labels are correct
- Buttons are visible and enabled or disabled correctly
- Mandatory fields are marked
- Error messages appear near the relevant fields
- Success messages are displayed
- Navigation works correctly
- Fields accept correct input
- Fields reject invalid input
- Password fields are masked
- Dropdown values are displayed correctly
- Date picker works correctly
- Form reset or cancel behavior works correctly

---

## 8. API Testing Checklist

API test cases should verify request, response, validation, authentication, and error handling.

API tests should cover:

- Valid request payload
- Missing mandatory field
- Invalid data type
- Invalid field format
- Invalid authentication
- Unauthorized access
- Invalid endpoint
- Invalid HTTP method
- Malformed JSON
- Duplicate request
- Empty request body
- Large request body
- Correct HTTP status code
- Correct response body
- Correct error message
- Response schema validation
- Response time, if required

Common API status code expectations:

- 200 OK for successful read/update
- 201 Created for successful creation
- 400 Bad Request for invalid input
- 401 Unauthorized for missing or invalid authentication
- 403 Forbidden for insufficient permission
- 404 Not Found for unavailable resource
- 409 Conflict for duplicate or conflicting request
- 500 Internal Server Error should not occur for handled validation failures

---

## 9. Security Testing Basics

Basic security-related test cases should be added when applicable.

Security tests should cover:

- Unauthorized user access
- Role-based access control
- Session expiry
- Password masking
- Sensitive data not displayed in error messages
- SQL injection-like input
- Script injection-like input
- Direct URL access without permission
- Token missing or expired
- User cannot access another user's data

For login and authentication stories, include:

- Invalid credentials
- Account lockout
- Password masking
- Session timeout
- Locked account behavior
- Error message should not reveal whether username or password is wrong

---

## 10. Accessibility Testing Basics

Accessibility test cases should be included for user-facing screens when applicable.

Accessibility tests should cover:

- Keyboard navigation
- Tab order
- Field labels
- Error messages readable by screen readers
- Sufficient color contrast
- Button names are meaningful
- Form fields have accessible labels
- Focus moves logically after validation errors

---

## 11. Regression Testing Guidelines

Regression test cases verify that existing functionality is not broken by a new change.

Regression tests should include:

- Existing related business flows
- Previously working happy paths
- Previously reported defects
- Integration points
- Frequently used user journeys
- Critical business scenarios

For every new story, identify:

- Directly impacted feature
- Related screens
- Related APIs
- Related user roles
- Related data validations
- Downstream flows

---

## 12. Traceability Matrix Guidelines

Each test case should be mapped to at least one acceptance criterion.

Traceability should show:

- Acceptance Criterion ID
- Acceptance Criterion Description
- Mapped Test Case IDs
- Test Type
- Coverage Status

Coverage status can be:

- Covered
- Partially Covered
- Not Covered
- Assumption-Based

If an acceptance criterion has no test case, mark it as a coverage gap.

---

## 13. Quality Review Checklist

Before finalizing generated test cases, check:

- Are all acceptance criteria covered?
- Are test cases clear and executable?
- Are expected results specific?
- Are negative scenarios included?
- Are boundary scenarios included?
- Are assumptions clearly marked?
- Are duplicate test cases removed?
- Are unsupported details avoided?
- Are API test cases generated only when API details are available?
- Are UI test cases generated only when UI details are available?
- Are test cases mapped to acceptance criteria?

---

## 14. Assumption Handling

The agent must not invent missing requirement details.

If something is not mentioned in the JIRA story, mark it as an assumption.

Examples:

- Assumption: API endpoint is not provided in the JIRA story, so API test cases are written at a conceptual level.
- Assumption: Maximum field length is not specified, so boundary test cases are based on common validation practices.
- Assumption: User role details are not provided, so role-based access tests are suggested as optional.

---

## 15. Login Feature Testing Checklist

For login-related stories, include:

Functional tests:

- Login with valid credentials
- Successful dashboard redirection
- Session created after login

Negative tests:

- Invalid password
- Invalid email
- Blank email
- Blank password
- Unregistered email
- Locked account
- Inactive account

Boundary/security tests:

- Failed login attempt count
- Account lock after configured number of attempts
- Password field masking
- SQL/script-like input
- Error message should not expose sensitive information

---

## 16. Password Reset Testing Checklist

For forgot password or reset password stories, include:

Functional tests:

- Request reset link with registered email
- Receive reset link
- Reset password with valid link
- Login with new password

Negative tests:

- Request reset with unregistered email
- Use expired reset link
- Use already-used reset link
- New password and confirm password mismatch
- Password does not meet policy

Boundary/security tests:

- Reset link expiry time
- Password minimum and maximum length
- Token tampering
- Multiple reset requests
- Old password should not work after reset

---

## 17. Profile Update Testing Checklist

For profile update stories, include:

Functional tests:

- Update editable fields
- Save valid profile details
- Updated details displayed after save

Negative tests:

- Blank mandatory fields
- Invalid mobile number
- Invalid address format, if applicable
- Attempt to edit non-editable email field

Boundary tests:

- Minimum and maximum name length
- Mobile number length
- Address maximum length
- Special characters in name or address

---

## 18. Shopping Cart Testing Checklist

For shopping cart stories, include:

Functional tests:

- Add available product to cart
- Update product quantity
- Remove product from cart
- Cart total calculated correctly

Negative tests:

- Add out-of-stock product
- Quantity as zero
- Quantity as negative number
- Quantity exceeding stock
- Add product with invalid product ID

Boundary tests:

- Minimum quantity
- Maximum available stock
- Large quantity
- Price calculation for multiple quantities

---

## 19. Support Ticket Testing Checklist

For support ticket stories, include:

Functional tests:

- Submit ticket with valid details
- Ticket reference number generated
- Ticket visible in ticket history

Negative tests:

- Blank subject
- Blank category
- Blank priority
- Blank description
- Description below minimum length
- Invalid attachment, if attachments are supported

Boundary tests:

- Minimum description length
- Maximum description length
- Maximum attachment size, if applicable

---

## 20. Final Test Case Output Standard

The final generated test cases should follow this format:

Test Case ID:
Title:
Type:
Priority:
Preconditions:
Test Data:
Steps:
Expected Result:
Mapped Acceptance Criteria:
Assumptions:

Each test case should be concise but complete enough for a QA engineer to execute manually or convert into automation later.