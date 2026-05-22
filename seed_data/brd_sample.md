# BRD - Customer Self-Service Portal

## 1. Product Overview

The Customer Self-Service Portal allows registered users to manage their account, authenticate securely, update profile information, manage shopping cart items, and submit customer support tickets.

The system is intended for web and mobile-responsive access.

---

## 2. User Roles

### Guest User
A guest user can:
- View public pages
- Register for an account
- Access login page
- Request password reset

### Registered User
A registered user can:
- Login to the portal
- View account dashboard
- Update profile details
- Add products to shopping cart
- Submit support tickets
- View ticket history

### Support Agent
A support agent can:
- View submitted support tickets
- Update ticket status
- Respond to customer queries

---

## 3. Authentication Rules

### Login Rules

- User must login using registered email address and password.
- Email and password are mandatory fields.
- Password must be masked on the UI.
- System must validate credentials securely.
- If credentials are valid, user must be redirected to dashboard.
- If credentials are invalid, system must show a generic error message.
- Error message must not reveal whether email or password is incorrect.
- Account must be locked after 5 consecutive failed login attempts.
- Locked account must not be allowed to login even with valid credentials.
- Account lock status can only be reset by admin or password recovery workflow.

### Session Rules

- A valid session must be created after successful login.
- User should not access authenticated pages without login.
- Session should expire after inactivity as configured by system settings.
- After logout, user should not access dashboard using browser back button.

---

## 4. Password Reset Rules

- User can request password reset using registered email address.
- System must show a generic confirmation message after reset request.
- Confirmation message must not reveal whether the email is registered.
- Password reset link must expire after 15 minutes.
- Expired reset links must not allow password reset.
- Already-used reset links must not be reused.
- New password and confirm password must match.
- New password must comply with password policy.
- After successful password reset, old password must no longer work.

### Password Policy

Password must:
- Be at least 8 characters long
- Be no more than 20 characters long
- Contain at least one uppercase letter
- Contain at least one lowercase letter
- Contain at least one numeric digit
- Contain at least one special character

---

## 5. Profile Management Rules

- Registered user can update first name, last name, mobile number, and address.
- Registered email address must be displayed as read-only.
- Email address must not be editable from profile screen.
- First name and last name are mandatory fields.
- Mobile number must accept numeric values only.
- Mobile number must be exactly 10 digits.
- Address field can contain letters, numbers, spaces, comma, period, slash, and hyphen.
- System must show success message after profile update.
- Updated details must be visible after save and page refresh.

---

## 6. Shopping Cart Rules

- Registered user can add available products to shopping cart.
- User must select a valid quantity before adding product to cart.
- Quantity must be at least 1.
- Quantity must not exceed available stock.
- Out-of-stock products must not be added to cart.
- Cart must display product name, price, quantity, and line total.
- Cart total must be calculated as price multiplied by quantity.
- If quantity is updated, cart total must be recalculated.
- If product is removed, cart total must be updated.
- User must see confirmation message after product is added to cart.

---

## 7. Support Ticket Rules

- Registered user can submit support ticket.
- Subject, category, priority, and description are mandatory fields.
- Category must be selected from predefined values.
- Priority must be Low, Medium, or High.
- Description must contain at least 20 characters.
- System must generate a unique ticket reference number after submission.
- User must see confirmation message after ticket creation.
- Submitted ticket must be visible in user's ticket history.
- Ticket status must default to Open after creation.

### Supported Ticket Categories

- Login Issue
- Payment Issue
- Order Issue
- Profile Issue
- Technical Issue
- Other

---

## 8. Common Validation Rules

- Mandatory fields must display validation error when left blank.
- Whitespace-only values must be treated as blank.
- System must prevent duplicate form submission.
- Error messages must be clear and user-friendly.
- Sensitive technical details must not be exposed in error messages.
- User input must be validated on both UI and backend where applicable.

---

## 9. Security Requirements

- Authenticated pages must not be accessible without login.
- User must not access another user's account data.
- Sensitive values such as password and tokens must not be displayed.
- Password must never be stored or logged in plain text.
- Error messages must not reveal sensitive security details.
- System must handle SQL/script-like input safely.
- Session must be invalidated after logout.

---

## 10. Non-Functional Requirements

- Login response should complete within 3 seconds under normal load.
- Profile update should complete within 3 seconds under normal load.
- Support ticket creation should complete within 5 seconds under normal load.
- System should support common desktop and mobile browser resolutions.
- User-facing pages should follow basic accessibility practices.