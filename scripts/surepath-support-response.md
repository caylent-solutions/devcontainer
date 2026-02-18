Visited Claude and ChatGPT in the browser via SurePath just before retesting. Still getting empty replies:

```
curl -v --proxy http://edge.surepath.ai:8080 http://httpbin.org/ip
→ curl: (52) Empty reply from server
```

Same result on all three resolved IPs (69.67.160.114, .115, .116).

A few questions:

1. You mentioned my integration method was TLS proxy — should we be using a different endpoint/port? We're currently configured for `http://edge.surepath.ai:8080` (non-TLS). If TLS is the correct method, what's the endpoint and port?

2. Is there anything on your side that shows our connection attempts and why they're being rejected? The TCP connect succeeds but we get an empty reply immediately.

3. This was working as recently as last week with the exact same tinyproxy config forwarding all traffic to `edge.surepath.ai:8080`. Nothing changed on our end.
