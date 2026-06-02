## Frontend Role

### 1. Security headers
Three nginx headers we added and what they do.
Strict-Transport-Security (HSTS): This tells the browser to never connect to our site over plain HTTP again, 
even if the user types http:// manually. It forces HTTPS for every future visit. 
The attack it mitigates is SSL stripping, where a man in the middle downgrades your connection from HTTPS to HTTP before you notice. 
The risk of setting it too strictly is that if we ever need to move back to HTTP temporarily, 
browsers that have cached the HSTS policy will refuse to connect and users will get errors they can't bypass without clearing their browser data.
X-Frame-Options: This tells the browser not to load our app inside an iframe on another site. 
The attack it mitigates is clickjacking, where an attacker embeds our app invisibly inside their own page and tricks users into clicking buttons they can't see. 
Setting it too strictly is not really a concern for our app since we don't intentionally embed our pages in iframes anywhere. 
If we ever wanted to embed a widget on a partner site, this header would block that.
X-Content-Type-Options: This tells the browser to trust the Content-Type header we send and not try to guess the file type on its own. 
The attack it mitigates is MIME sniffing, where a browser decides an uploaded file is executable JavaScript even though the server said it was plain text. 
For our app this matters because users can submit notes and URLs in job applications. 
Without this header a browser might interpret a crafted input as a script. 
Setting it too strictly is not an issue. This header has one value, nosniff, and it has no downside for a standard web app.

### 2. Static assets
With flask run, Flask served everything including our CSS, Bootstrap, and any JavaScript files out of the static/ folder. 
Every static file request went through Python. In the new stack, nginx serves the static/ folder directly. 
The requests never reach gunicorn or Flask at all.
For our project this means the files in static/js/forms.js and any Bootstrap assets are served by nginx at full speed without waking up a Python worker. 
The performance argument is that nginx is purpose built for serving files and is orders of magnitude faster than Flask for this task. 
The security argument is that fewer requests reach the Python process, which reduces the attack surface. 
A malformed request for a static file gets handled and dropped by nginx before Flask ever sees it.

### 3. Cookie flags in real life
In Week 7 we set SESSION_COOKIE_SECURE=True in our Flask config. On plain HTTP this flag was completely inert. 
The browser ignored it because there was no HTTPS connection to enforce it on. The cookie was being sent on every request regardless.
With nginx terminating HTTPS, the flag now actually does something. The browser will only attach the session cookie to requests going over an encrypted connection. If anything tries to make an HTTP request to our app, the cookie stays behind. What would have broken in development if we had set this earlier is that every local test run over http://localhost would have silently dropped the session cookie, users would have appeared logged out on every request, and it would have been very confusing to debug because no error is thrown. The cookie just quietly doesn't get sent.

### 4. Debugging a user who keeps getting logged out
The first thing I would check as the frontend person is the cookie itself. Open the browser dev tools, go to Application, then Cookies, and look at the session cookie. I want to see whether it exists at all after login, 
what its flags are, and whether the domain and path match the site. If Secure is set and the user is on HTTP, 
the cookie will never be sent and they will appear logged out on every redirect.
The second thing I would check is whether the redirect after login is changing the domain or protocol in a way that drops the cookie. 
For example if the login page is on HTTP and the redirect lands on HTTPS, or vice versa, the cookie scope might not match.
The LLM is useful for explaining what each cookie flag does and what combinations of flags cause this symptom. 
It is not useful for telling me what is actually in the user's browser or what the server is actually sending, 
because it cannot see either of those things. That requires the browser dev tools and the nginx access log.


## Coordinator Questions

### 1. Secrets in three places
I'll use our GitHub OAuth client secret as the example.
It is generated at GitHub, under the team org's OAuth app settings. That is where it is created and where it lives as the source of truth.
It is stored in GitHub Actions secrets, under the team repo settings. That is where the deploy pipeline reads it at runtime without it ever appearing in the code or the logs.
It is used at runtime inside the running container, loaded from the environment variable OAUTH_CLIENT_SECRET via python-dotenv when the app starts.
What goes wrong if it leaks into a fourth place is the problem. If it gets committed to the repo, even briefly, 
it is in the git history forever. Anyone who clones the repo has it. 
GitHub's secret scanning will flag it but the damage is already done. The secret must be rotated immediately, 
which means updating the GitHub OAuth app, the Actions secret, and the .env on the server.

### 2. Tag-driven releases
The argument for tag-driven releases for our project is control. A push to main might be a work in progress, 
a documentation fix, or a half-merged feature. A tag is a deliberate act. Someone looked at the code, 
decided it was ready, and said so explicitly by running git push --tags. That intent matters. 
It means the deploy pipeline only fires when a human made a conscious decision to ship, not every time anyone pushes anything.
The argument against is friction. 
On a three person student project moving fast, creating a tag every time you want to test a deploy adds a step that is easy to forget. 
If the team is already disciplined about what goes into main, pushing directly from main is simpler and fast enough.

### 3. When CI goes red
First I look at the GitHub Actions log for the failed job. I want the exact error message, not a summary. 
The specific line that failed tells me whether this is a build error, a test failure, a missing secret, 
or a network problem reaching the EC2.
Next I check whether the failure is in my code or in the environment. If tests were passing locally and failing in CI, 
the environment is the likely culprit. I check whether secrets are present in the Actions settings and whether the EC2 is reachable.
I would ask the LLM to help interpret an unfamiliar error message or to explain what a specific CI configuration option does. 
What I would not ask the LLM is whether my specific workflow file is correct for my specific repo, 
because it cannot see my repo, my secrets, or my EC2 state. That requires me to paste the actual file and the actual error together.

### 4. The composition problem
An example of the three layers conflicting is the Content Security Policy header and our Bootstrap setup. 
If I set a strict CSP in nginx that blocks inline styles, and our templates use Bootstrap's utility classes that generate inline styles at render time, 
the browser will silently block those styles and the layout will break. 
The nginx header and the Flask templates are in conflict, and neither person working on their own layer would necessarily catch it.

As coordinator I catch this by running the full stack after each personal branch is merged into hardening and checking the browser console for CSP violations. 
A CSP violation shows up as a red error in the console even when the page looks mostly fine. 
That is the signal that two layers are fighting each other. 
The fix gets surfaced to both the frontend person and whoever wrote the conflicting template before it merges to main.
