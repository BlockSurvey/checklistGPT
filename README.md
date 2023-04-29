Build Command	
pip install -r requirements.txt

Start Command	
gunicorn app:app -w 1 --threads 12
