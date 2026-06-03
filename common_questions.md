1. What does nginx do that your Flask app shouldn't or can't?
nginx sits at the front door and handles things Flask was never meant to deal with. 
It terminates HTTPS so Flask never has to manage SSL certificates. 
It serves static files like our CSS and JavaScript directly without touching Python at all. 
It also rate limits requests, blocks known bad paths like /.env and /wp-login.php, 
and sets security headers before a response ever reaches the browser. 
Flask is an application framework. Making it do all that would be the wrong tool for the job.

2. What does gunicorn do that flask run doesn't?
flask run is a single threaded development server. 
It handles one request at a time and was never designed for real traffic. 
gunicorn spawns multiple worker processes so several requests can be handled simultaneously. 
It also handles worker crashes gracefully by restarting them automatically, 
manages timeouts so a slow request doesn't hang the whole app, 
and integrates properly with nginx via a WSGI interface. 
Running flask run in production is like leaving your front door open.

3. What's one specific thing your stack is now harder to misuse?
Session cookies. In Week 7 we set SESSION_COOKIE_SECURE=True but it was inert because we were running on plain HTTP. 
Now that nginx terminates HTTPS, that flag actually fires. 
The browser will only send the session cookie over an encrypted connection. 
Someone sitting on the same network can no longer intercept a login session by sniffing HTTP traffic.

4. If you wanted to add a load balancer, where would it go and what problem would it solve?
It would sit in front of nginx. The order would be: load balancer, nginx, gunicorn, Flask. 
nginx already handles one server well, but it can't spread traffic across multiple servers by itself. 
A load balancer like AWS ALB would distribute incoming requests across multiple EC2 instances running the same stack, 
so if one instance goes down the others keep serving. nginx isn't solving that problem. 
It's managing one server's edge, not a fleet.

5. What's a single point of failure in your current setup?
The EC2 instance itself. Everything, nginx, gunicorn, Flask, and Postgres, runs on one machine. 
If that instance goes down, the entire app goes down. There's no failover, no replica, no backup instance. 
A single bad deployment, a hardware failure, or an AWS maintenance window takes down the whole stack.

6. If someone runs docker-compose down on production, what happens to the database data?
It depends on whether the Postgres container uses a named volume. 
If our docker-compose.yml defines a named volume for the database, for example postgres_data, 
then docker-compose down stops and removes the containers but leaves the volume intact. The data survives. 
If someone runs docker-compose down -v, the -v flag removes volumes too and all data is gone permanently. 
You should check your compose file for the volumes: section to confirm which applies.

7. What's one thing you learned from your LLM this week that surprised you?
I didn't realize that flask run actively prints a warning telling you not to use it in production, 
but most people ignore it or never see it. What surprised me more was learning why. 
It's not just about performance. flask run runs in debug mode by default, which means if an unhandled exception hits, 
it serves an interactive debugger in the browser that lets anyone execute arbitrary Python code on your server. 
That's not a performance problem. It's a remote code execution vulnerability. gunicorn never exposes that.
