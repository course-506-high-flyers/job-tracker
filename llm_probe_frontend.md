# LLM Probe — Frontend Security Audit
**Role:** Client-side
**Week:** 8
**Tool used:** Claude (Anthropic)
**Date:** June 3, 2026

---

## Prompt submitted

"I'm hardening the frontend of a Flask app. Here's our nginx security
header config and CSP:

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self';
      style-src 'self' https://cdn.jsdelivr.net;
      script-src 'self' https://cdn.jsdelivr.net;
      img-src 'self' data: https://avatars.githubusercontent.com" always;

Evaluate against best practices: (a) what's missing for our case,
(b) what's too strict and would break us, (c) what an attacker could
still do. Tell me what you'd change and why."

---

## LLM response

**What's missing:**

The CSP has no form-action directive. Without it, a form on our
page could submit to any domain, which is a vector for exfiltration
if an attacker injects a form. Adding form-action 'self' closes
that gap cleanly.

There is no frame-ancestors directive in the CSP. We have
X-Frame-Options: DENY which handles older browsers, but the modern
equivalent is frame-ancestors 'none' in the CSP. Both should be
present for full coverage.

The CSP has no connect-src directive. Our app makes no explicit
AJAX calls, but if any JavaScript on the page tries to fetch a URL,
the browser will fall back to default-src 'self' which restricts
it to our own domain. That is probably fine for now but worth naming
explicitly as the app grows.

There is no base-uri directive. Without it, an injected base tag
could redirect all relative URLs on the page to an attacker
controlled domain. Adding base-uri 'self' is a one-line fix.

**What's too strict and would break us:**

The img-src directive allows https://avatars.githubusercontent.com
for GitHub profile pictures, which is correct. However if Clearbit
returns a company logo URL from a different domain, that image will
be silently blocked by the browser. We would need to add Clearbit's
image domain to img-src or use a broader pattern like img-src
'self' data: https: to allow all HTTPS images.

The style-src only allows our own styles and cdn.jsdelivr.net. If
Bootstrap ever loads a font or additional stylesheet from a different
CDN, it will be blocked. This is not a current problem but worth
watching.

**What an attacker could still do:**

The CDN trust in script-src is the biggest remaining risk. We trust
all of cdn.jsdelivr.net, which hosts thousands of packages. If any
package on that CDN is compromised, our CSP would allow it to run on
our pages. The mitigation for this is subresource integrity (SRI)
hashes on our CDN script and link tags, so the browser verifies the
file has not changed before executing it. We have not implemented
SRI yet.

Rate limiting is applied to /login, /register, and /auth routes.
A credential stuffing attack against those endpoints would be slowed
but not stopped at 5 requests per minute. A distributed attack from
many IPs would bypass the per-IP rate limit entirely. At our scale
this is acceptable, but it is worth naming.

The self-signed certificate means browsers will show a security
warning and the connection is not trusted by default. A real
Let's Encrypt certificate is the fix, covered in Week 9.

---

## What I took away

The two immediate changes I would make based on this audit are adding
form-action 'self' and base-uri 'self' to the CSP. Both are
one-line additions that close real attack vectors with no downside
for our app.

The SRI finding is the most interesting one. I knew CDN trust was
a tradeoff but had not thought through the implication that a
compromised package on jsdelivr would pass our CSP check. Adding SRI
hashes to our Bootstrap script and CSS tags is the right fix and is
straightforward to implement.

The Clearbit logo domain gap is a practical one I would have caught
only when testing. The browser would silently block the image with
no obvious error unless you have the console open. That is the kind
of thing the LLM is genuinely useful for surfacing before it becomes
a bug report.

I pushed back on the suggestion to use img-src 'self' data: https:
as a blanket fix. That is too permissive as it allows images from
any HTTPS source. The better fix is to add Clearbit's specific image
domain once we know what it is, or to proxy company logos through
our own server so we control the source.
