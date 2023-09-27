Greetings App 

A simple Flask web application for sending mass text messages. This project allows users to register, log in, manage contacts, and send text messages using Twilio.

Table of Contents:

Features 
Installation 
Usage 
Testing 
Contributing 
License

Features: 

User registration and authentication. User-friendly web interface for sending text messages. Contact management (add, edit, delete contacts). Flash messages for notifications. Integration with Twilio for sending text messages. Installation Clone the repository:

git clone https://github.com/yourusername/greetings.git Navigate to the project directory:
cd greetings Create a virtual environment (recommended):

python -m venv venv Activate the virtual environment:

On Windows:
venv\Scripts\activate 

On macOS and Linux:
source venv/bin/activate 

Install the project dependencies:
pip install -r requirements.txt Set up the configuration:

.env.example file to .env and configure it with your Twilio credentials and any other necessary environment variables. Initialize the database:
flask db init flask db migrate flask db upgrade Usage Start the Flask development server:

flask run Access the application in your web browser at http://localhost:5000.

Register a new user account or log in if you already have one.

Use the application to manage contacts and send mass text messages.

Testing To run the tests for this project, you can use the following command:
python -m unittest test_routes.py Contributing Contributions are welcome! If you'd like to contribute to this project, please follow these steps:
Fork the repository on GitHub.

Clone your forked repository to your local machine.

Create a new branch for your feature or bug fix:
git checkout -b feature/my-feature Make your changes and commit them with descriptive commit messages.

Push your changes to your fork on GitHub:
git push origin feature/my-feature Create a pull request (PR) from your branch to the main repository.

Wait for feedback and approval from the maintainers.

