# Nura - UI / UX Design Document

# 1. Design Philosophy

Nura is a healthcare-first AI platform.

The design should feel:

* Clean
* Professional
* Trustworthy
* Modern
* Medical
* Accessible

The interface should avoid looking like:

* Crypto dashboards
* Trading applications
* Generic AI chatbots

The interface should resemble:

* Modern healthcare SaaS platforms
* Electronic Health Record systems
* Healthcare patient portals

---

# 2. Design Principles

## Consistency

All pages must use:

* Same sidebar
* Same navbar
* Same spacing system
* Same typography
* Same component library

Users should never feel they are leaving the application.

---

## Accessibility

Requirements:

* High contrast text
* Keyboard navigation
* Mobile responsiveness
* Accessible forms
* Accessible tables

---

## Healthcare First

AI is a feature.

Healthcare is the product.

Navigation should prioritize:

* Health Data
* Doctors
* Appointments
* Reports

before AI interactions.

---

# 3. Layout System

## Global Layout

```text
┌────────────────────────────────────┐
│ Top Navbar                         │
├─────────┬──────────────────────────┤
│ Sidebar │ Main Content             │
│         │                          │
└─────────┴──────────────────────────┘
```

---

## Sidebar Navigation

Patient Sidebar:

```text
Overview

Nura AI

Reports

Doctors

Appointments

Medications & Reminders

Profile
```

Doctor Sidebar:

```text
Dashboard

Appointments

Patients

Availability

Earnings

Profile
```

Admin Sidebar:

```text
Dashboard

Users

Doctors

Appointments

Payments

Analytics

Audit Logs
```

---

# 4. Top Navigation

Contains:

* Global Search
* Notifications
* User Profile
* Settings

Search should support:

* Reports
* Doctors
* Medications
* Appointments

---

# 5. Design Tokens

## Border Radius

```text
Cards: 16px
Buttons: 12px
Inputs: 12px
```

---

## Spacing

```text
4px
8px
16px
24px
32px
48px
```

---

## Shadows

Use soft shadows.

Avoid heavy floating cards.

---

# 6. Patient Screens

---

## Patient Dashboard

Purpose:

Provide health overview.

Sections:

### Health Summary

Cards:

* Reports
* Reminders
* Upcoming Appointments
* Risk Level

---

### Quick Actions

Buttons:

* Chat with Nura
* Upload Report
* Find Doctor
* Book Appointment
* Add Reminder

---

### Upcoming Appointments

Displays:

* Doctor
* Date
* Status

---

### Today's Medications

Displays:

* Medication
* Time
* Status

---

### Recent Reports

Displays:

* Report Name
* Risk Level
* Summary

---

### AI Health Insights

Displays:

* Personalized health insights
* Medication alerts
* Appointment reminders

---

## Nura AI Screen

Layout:

```text
Sidebar

Chat History

Chat Window

Patient Context Panel
```

---

### Chat History

Contains:

* Previous conversations
* Search conversations
* New Chat button

---

### Chat Window

Supports:

* Text queries
* Report questions
* Symptom analysis
* Drug interaction checks
* Doctor recommendations

---

### Context Panel

Displays:

* Recent Reports
* Active Medications
* Upcoming Appointments
* Health Insights

---

## Reports Screen

Sections:

### Upload Report

### Reports Table

Columns:

* Name
* Upload Date
* Risk Level
* Status

---

### Report Analysis Cards

Displays:

* Summary
* Insights
* Recommendations

---

### Health Trends

Charts:

* Blood Pressure
* Cholesterol
* Blood Sugar

---

## Doctors Screen

Sections:

### Search

### Specialty Filters

### Doctor Cards

Doctor Card:

* Photo
* Name
* Specialty
* Experience
* Fee
* Availability
* Rating

---

### Recommended Doctors

AI-generated recommendations.

---

## Appointment Screen

Sections:

### Upcoming Appointments

### Pending Requests

### Consultation History

### Prescriptions

---

Workflow:

```text
Doctor Selection
 ↓
Slot Selection
 ↓
Payment
 ↓
Approval
 ↓
Consultation
```

---

## Medications & Reminders

Sections:

### Active Medications

### Reminder Schedule

### Upcoming Reminders

### Drug Safety Alerts

---

Reminder Creation Flow:

```text
Add Medication
 ↓
Interaction Check
 ↓
Risk Classification
 ↓
Confirmation
 ↓
Reminder Creation
```

---

## Profile Screen

Sections:

* Personal Information
* Security
* Notifications
* Account Settings

---

# 7. Doctor Screens

---

## Doctor Dashboard

Widgets:

* Today's Appointments
* Pending Requests
* Earnings
* Total Patients

---

## Patients Screen

Displays:

* Patient Information
* Reports
* Medical History
* Prescriptions

---

## Availability Screen

Functions:

* Add Slots
* Edit Slots
* Delete Slots

---

## Earnings Screen

Displays:

* Wallet Balance
* Transactions
* Payout History

---

# 8. Admin Screens

---

## Dashboard

Displays:

* Users
* Doctors
* Appointments
* Revenue

---

## Doctor Verification

Functions:

* Approve
* Reject
* Review Documents

---

## Payments

Displays:

* Transactions
* Revenue
* Refunds

---

# 9. Mobile Responsiveness

Tablet:

```text
Sidebar → Collapsible
```

Mobile:

```text
Sidebar → Drawer
```

Navigation:

```text
Hamburger Menu
```

---

# 10. Component Library

Buttons:

* Primary
* Secondary
* Danger

Cards:

* Dashboard Card
* Report Card
* Doctor Card

Inputs:

* Text Input
* Search Input
* Select
* Date Picker

Tables:

* Reports
* Appointments
* Payments

Modals:

* Confirmation
* Drug Interaction Alert
* Payment Success

---

# 11. Empty States

Reports:

```text
No reports uploaded yet.
Upload your first report.
```

Appointments:

```text
No appointments scheduled.
Book your first appointment.
```

Medications:

```text
No medications added.
Add your first medication.
```

---

# 12. Error States

Display:

* Network Errors
* Payment Failures
* Upload Failures
* Validation Errors

Use friendly healthcare-oriented messaging.

---

# 13. Future UI Enhancements

* Dark Mode
* Voice Assistant
* Telemedicine Calls
* AI Health Timeline
* Wearable Integrations
* Mobile Applications
