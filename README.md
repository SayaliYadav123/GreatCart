Step 1 — Clone the repository
git clone https://github.com/your-username/stylenest.git
cd stylenest
cd GreatCart

Step 2 — Create and activate virtual environment
Windows:
python -m venv env
env\Scripts\activate

Mac / Linux:
python -m venv env
source env/bin/activate

Step 3 — Install dependencies
pip install -r requirements.txt

Step 4 — Create your .env file
Create a file named .env in the root project folder (same level as manage.py) and paste the following:
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_SECRET=your-paypal-secret

⚠ Never commit your .env file to Git. Make sure .env is listed in your .gitignore.

Step 5 — Run migrations
python manage.py makemigrations
python manage.py migrate

Step 6 — Create a superuser (admin account)
python manage.py createsuperuser
Follow the prompts to set your email and password.

Step 7 — Collect static files (production only)
python manage.py collectstatic

Step 8 — Run the development server
python manage.py runserver
Open http://127.0.0.1:8000 in your browser.
