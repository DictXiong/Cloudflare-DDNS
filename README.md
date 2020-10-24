**Forked from https://github.com/timothymiller/cloudflare-ddns**

Simplified and upgraded. Only python files remain. 

To run it, you should

1. `pip install requests`
2. copy `config-example.json` to `config.json`, then edit it
3. `python cloudflare-ddns.py`, or `python cloudflare-ddns.py --repeat`, or `python cloudflare-ddns.py --dry-run`
4. run `python cloudflare-ddns.py --help` to get help

---by Dict Xiong



# 🚀 Cloudflare DDNS

Dynamic DNS service based on Cloudflare! Access your home network remotely via a custom domain name without a static IP!

## 🇺🇸 Origin

This script was written for the Raspberry Pi platform to enable low cost, simple self hosting to promote a more decentralized internet. On execution, the script fetches public IPv4 and IPv6 addresses and creates/updates DNS records for the subdomains in Cloudflare. Stale, duplicate DNS records are removed for housekeeping.

## 🚦 Getting Started

First copy the example configuration file into the real one.

```bash
cp config-example.json config.json
```

Edit `config.json` and replace the values with your own.

### Authentication methods

You can choose to use either the newer API tokens, or the traditional API keys

To generate a new API tokens, go to your [Cloudflare Profile](https://dash.cloudflare.com/profile/api-tokens) and create a token capable of **Edit DNS**. Then replace the value in
```json
"authentication":
  "api_token": "Your cloudflare API token, including the capability of **Edit DNS**"
```

Alternatively, you can use the traditional API keys by setting appropriate values for: 
```json
"authentication":
  "api_key":
    "api_key": "Your cloudflare API Key",
    "account_email": "The email address you use to sign in to cloudflare",
```

### Other values explained

```json
"zone_id": "The ID of the zone that will get the records. From your dashboard click into the zone. Under the overview tab, scroll down and the zone ID is listed in the right rail",
"subdomains": "Array of subdomains you want to update the A & where applicable, AAAA records. IMPORTANT! Only write subdomain name. Do not include the base domain name. (e.g. foo or an empty string to update the base domain)",
"proxied": false (defaults to false. Make it true if you want CDN/SSL benefits from cloudflare. This usually disables SSH)
```

## 📠 Hosting multiple domains on the same IP?
You can save yourself some trouble when hosting multiple domains pointing to the same IP address (in the case of Traefik) by defining one A & AAAA record  'ddns.example.com' pointing to the IP of the server that will be updated by this DDNS script. For each subdomain, create a CNAME record pointing to 'ddns.example.com'. Now you don't have to manually modify the script config every time you add a new subdomain to your site!

## License

This Template is licensed under the GNU General Public License, version 3 (GPLv3).

## Author

Timothy Miller

[View my GitHub profile 💡](https://github.com/timothymiller)

[View my personal website 💻](https://timknowsbest.com)
