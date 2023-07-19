Build Command	
pip install -r requirements.txt

Start Command	
gunicorn app:app -w 1 --threads 12
gunicorn app:app -w 4 --timeout 1200

gunicorn --worker-class=gevent --worker-connections=1000 --workers=4 app:app  --timeout 1200

<!-- Understand about threads on Gunicorn -->
<!-- https://medium.com/building-the-system/gunicorn-3-means-of-concurrency-efbb547674b7#:~:text=Gunicorn%20allows%20for%20the%20usage,setting%20their%20corresponding%20worker%20class.&text=worker%2Dconnections%20is%20a%20specific,ll%20be%20using%203%20workers. -->