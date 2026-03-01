<h1>lendR – Community Lending Web Platform</h1>

lendR is a Flask-based web application that allows users to lend and borrow items or skills using a simple credit system.
The platform supports posting listings, sending requests, approving or rejecting requests, credit transfers and late-return penalties.

This project was developed as a school website project.

📌 Project Description

lendR is a community lending platform where users can:

post items or skills for lending

request items or skills from others

earn and spend credits

manage requests and returns

track their own listings and borrowing history

The system helps demonstrate backend development using Flask and SQLite.

🛠 Tech Stack

Python

Flask

SQLite

HTML (Jinja templates)

CSS

✨ Features

User registration and login

Credit system for every user

Post items or skills for lending

Browse available listings

Send requests for listings

Accept or reject requests

Automatic credit transfer on acceptance

Return system with late penalty (2 credits per day)

View and manage:

My posted listings

My requests

Requests for my listings

Delete own listings
```
🗂 Project Structure
project/
│
├── app.py
├── database.db
├── requirements.txt
│
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── post.html
│   ├── browse.html
│   ├── my_posts.html
│   ├── my_requests.html
│   └── my_listings.html
│
├── static/
│   ├── style.css
│   ├── style2.css
│   └── lendr.jpeg
│
└── docs/
    ├── architecture.png
    └── screenshots/
```
⚙️ Installation

Create a virtual environment (optional but recommended) and install dependencies.

pip install -r requirements.txt
▶️ Run the Application
python app.py

Open in browser:

http://127.0.0.1:5000
🧪 Default Behaviour

Every new user starts with 10 credits

Listing types:

Item

Skill

When a request is accepted:

credits are transferred from borrower to owner

the listing becomes unavailable

When a borrower returns an item late:

penalty = 2 credits per day late

🖼 Screenshots

<img width="1905" height="991" alt="Screenshot 2026-02-28 082148" src="https://github.com/user-attachments/assets/1d6f0e52-7316-47d8-92fb-115a1c1c03bb" />
<img width="1918" height="998" alt="Screenshot 2026-02-28 082227" src="https://github.com/user-attachments/assets/3253cc13-8ce8-431f-9cc0-c04bef6f3ab1" />
<img width="1903" height="989" alt="Screenshot 2026-02-28 082324" src="https://github.com/user-attachments/assets/87d4ea6c-6687-45ae-a450-3e3e6bc30ddb" />
<img width="1892" height="991" alt="Screenshot 2026-02-28 082348" src="https://github.com/user-attachments/assets/3d176246-dcab-4aff-9e4b-7a753ee97f19" />
<img width="1032" height="529" alt="Screenshot 2026-02-28 090836" src="https://github.com/user-attachments/assets/c4c12d94-6334-45ef-bca6-8aa71b8a2763" />


🎥 Demo Video

Add your demo video link here:

https://drive.google.com/file/d/1F6r2jkQcFvftxaGWfiUIv4p6OK5yyTnj/view?usp=sharing
🧱 Architecture Diagram

<img width="600" height="400" alt="architecture" src="https://github.com/user-attachments/assets/19a2eaa8-03e2-451a-8d27-6d9be7aa8f07" />

High Level Architecture

Browser (Frontend – HTML + CSS)

Flask Web Server

SQLite Database

Flow:

User → Flask Routes → SQLite Database → Flask → HTML Templates
🔌 API / Backend Routes

The application uses Flask routes as backend APIs.

Authentication

GET /login

POST /login

GET /signup

POST /signup

GET /logout

Listings

GET /post

POST /post

GET /browse

GET /my_posts

POST /delete/<listing_id>

Requests

POST /request/<listing_id>

GET /my_requests

GET /my_listings

GET /accept/<request_id>

GET /reject/<request_id>

GET /return/<request_id>

👥 Team Members

Devika G Nair
Anupa Siby

📄 License

This project is licensed under the MIT License.

See the LICENSE file for details.

🤖 AI Tools Used

ChatGPT was used for:

debugging Flask routes

improving HTML and CSS styling

improving project documentation

Prompts mainly focused on:

Flask error fixing

Jinja template corrections

UI styling suggestions

📌 Notes

Only the owner of a listing can delete it.

Only logged-in users can access internal pages.

The database tables are created automatically when the app runs for the first time.

This project is intended for academic and learning purposes.
