# User Guide for Compolvo

Welcome to the Compolvo User Guide. This guide will walk you through the various pages and functionalities of the
Compolvo website, as displayed in the images provided.

#### Table of Contents

* [1. Page Overview](#1-page-overview)
    * [1.1 Welcome Page](#11-welcome-page)
    * [1.2 Login Page](#12-login-page)
    * [1.3 Registration Page](#13-registration-page)
    * [1.4 Homepage](#14-homepage)
    * [1.5 Software Comparison](#15-software-comparison)
    * [1.6 Software Details](#16-software-details)
    * [1.7 Agent Management](#17-agent-management)
* [2. User Flow](#2-user-flow)

---

## 1. Page Overview

### 1.1 Welcome Page

![Homepage](../images/homepage.png)

- **Description**: The homepage welcomes users to the Compolvo site with a logo and a welcome message in German, "
  Willkommen auf der Compolvo-Seite!".
  This is a static welcome page with no interactive elements. To proceed, log in to your account. Once logged in, use
  the navigation bar that appears to explore the website.

---

### 1.2 Login Page

![Login Page](../images/login_page.png)

- **Description**: This page allows users to log into their accounts.
- **Fields**:
    - **E-Mail**: Enter your registered email address.
    - **Password**: Enter your password.
- **Buttons**:
    - **Submit**: Logs the user into the system.
    - **No account yet?**: Redirects to the registration page.

---

### 1.3 Registration Page

![Registration Page](../images/registration.png)

- **Description**: This page is for creating a new user account.
- **Fields**:
    - **First name**: Enter your first name.
    - **Last name**: Enter your last name.
    - **E-Mail**: Enter your email address.
    - **Password**: Create a password (must be at least 10 characters long).
    - **Repeat password**: Re-enter the password for confirmation.
- **Buttons**:
    - **Submit**: Registers the new user.

---

### 1.4 Homepage

![Dashboard](../images/dashboard_ws.jpeg)

- **Description**: The main page and shows a dashboard for logged-in users. If a software is installed by this website,
  its current status is shown.
- **Features**:
    - **Greeting**: Personalized greeting message.
    - **Dashboard**: Shows the status of the installed software (installed, update available, corrupted) and lets you
      uninstall or update it.
- **Navigation Bar**:
    - **Dark Mode**: Toggle between light and dark mode.
    - **Homepage**: This page.
    - **Compare Tab**: Directs to the software comparison page.
    - **Agent Panel**: Allows adding and seeing the status of agents.
    - **Profile**: Shows the user profile and edit options.
    - **Login/Logout**: Lets you log in or log out.
    - **Session Timer**: Shows a countdown of the current session time. After 1 hour, you have to log in again.

---

### 1.5 Software Comparison

![Software Comparison](../images/comparison.png)

- **Description**: This page allows users to compare different software options.
- **Filter Options**:
    - **Tags**: Filter software by tags.
    - **Price**: Adjust the price range filter.
    - **Period**: Select the period (Day, Month, Year).
    - **License**: Filter by software license.
    - **OS**: Filter by operating system.
- **Software List**: Displays various software options with brief descriptions, licenses, OS compatibility, and pricing
  details. Each software card is clickable and routes you to a more detailed view with buying options of the software.

---

### 1.6 Software Details

![Software Details](../images/software_detail.png)

- **Description**: Detailed view of selected software.
- **Features**:
    - **Software Information**: Comprehensive details about the software, including features, compatibility, and
      security.
    - **Purchase Options**: Users can choose between different subscription plans (e.g., 1 month or 1 year).

---

### 1.7 Agent Management

![Agent Management](../images/add_agent.png)

- **Description**: Manage agents associated with the user's account.
- **Features**:
    - **Agent List**: Displays a list of agents with details such as name, IP address, connection status, and
      timestamps.
    - **Buttons**:
        - **Refresh**: Refreshes the agent list.
        - **Delete**: Deletes selected agents.
        - **Create**: Adds a new agent.
    - **Agent ID**: After creating a new agent, the agent ID is saved to your clipboard. Use this ID to connect your
      locally installed agent to the website, allowing you to manage installations on your computer through the website.

---

## 2. User Flow

This section describes the overall user flow on the Compolvo website, guiding users from logging in
to managing/buying software and agents.

1. Create an account by clicking on login and select 'No account yet?'
2. After creating a new account, sign in. You will now be greeted by your own customized homepage
3. Next, install the agent on the machine(s) you want to manage. TODO: At the moment this is
   possible via the GitHub repo.
4. Create an agent in the website by clicking on the agents tab in the navbar and then the blue create button
5. The agent id is saved in your clipboard. Run the agent init script on your machine and paste the
   agent id when prompted to.
6. Inside the agents tab you should now see the name and connection information of your installed
   agent (possibly after refreshing)
7. Make sure to run the agent on the agent's machine using the run command.
8. Add your payment details in the profile tab (after clicking on the edit icon)
9. Compare different software options by clicking on the compare tab in the navbar
10. Filter the available softwares by the criteria that are important to you
11. Select a software to see more details and purchase options
12. Subscribe to software by subscribing to a service offering
13. After positive confirmation, go to the profile tab to install the software.
14. On the home tab, observe the software being installed on the agent.

---