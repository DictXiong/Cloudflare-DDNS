import requests, json, sys, os, socket, ctypes, logging, argparse
import time

log_level_table = {
    "notset": logging.NOTSET,
    "debug": logging.DEBUG, 
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
    "fatal": logging.FATAL,
}
dry_run = False
PATH = os.getcwd() + "/"
version = float(str(sys.version_info[0]) + "." + str(sys.version_info[1]))

def getIPs_api():
    logging.debug("Getting IPs by requesting public APIs...")
    a = ""
    aaaa = ""
    try:
        a = requests.get("https://dns.timknowsbest.com/api/ipv4").text
    except Exception as e:
        logging.error("Unable to access IPv4 API: " + str(e))
    try:
        aaaa = requests.get("https://api6.ipify.org?format=json").json().get("ip")
    except Exception as e:
        logging.error("Unable to access IPv6 API: " + str(e))
    ips = []

    if(a.find(".") > -1):
        if (a.startswith(config["get_ip"]["ipv4_prefix"])):
            ips.append({
                "type": "A",
                "ip": a
            })
        else:
            logging.warning(f'IPv4 not detected: IP {a} has no prefix "{config["get_ip"]["ipv4_prefix"]}".')
    else:
        logging.warning("IPv4 not detected.")

    if(aaaa.find(":") > -1):
        if (aaaa.startswith(config["get_ip"]["ipv6_prefix"])):
            ips.append({
                "type": "AAAA",
                "ip": aaaa
            })
        else:
            logging.warning(f'IPv6 not detected: IP {aaaa} has no prefix "{config["get_ip"]["ipv6_prefix"]}".')
    else:
        logging.warning("IPv6 not detected.")

    return ips

def getIPs_self():
    logging.debug("Getting IPs by socket...")
    ips = []

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((config["get_ip"]["ipv4"], 80))
        ipv4 = s.getsockname()[0]
        if (ipv4.startswith(config["get_ip"]["ipv4_prefix"])):
            ips.append({"type": "A", "ip": ipv4})
        else:
            raise Exception(f'IP {ipv4} has no prefix "{config["get_ip"]["ipv4_prefix"]}".')
    except Exception as e:
        logging.warning("IPv4 not detected: " + str(e))
    
    try:
        s6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s6.connect((config["get_ip"]["ipv6"], 80))
        ipv6 = s6.getsockname()[0]
        if (ipv6.startswith(config["get_ip"]["ipv6_prefix"])):
            ips.append({"type": "AAAA", "ip": ipv6})
        else:
            raise Exception(f'IP {ipv6} has no prefix "{config["get_ip"]["ipv6_prefix"]}".')
    except Exception as e:
        logging.warning("IPv6 not detected: " + str(e))

    return ips

def commitRecord(ip):
    stale_record_ids = []
    for c in config["cloudflare"]:
        subdomains = c["subdomains"]
        response = cf_api("zones/" + c['zone_id'], "GET", c)
        base_domain_name = response["result"]["name"]
        for subdomain in subdomains:
            exists = False
            record = {
                "type": ip["type"],
                "name": subdomain,
                "content": ip["ip"],
                "proxied": c["proxied"]
            }
            list = cf_api(
                "zones/" + c['zone_id'] + "/dns_records?per_page=100&type=" + ip["type"], "GET", c)
            
            full_subdomain = base_domain_name
            if subdomain:
                full_subdomain = subdomain + "." + full_subdomain
            
            dns_id = ""
            for r in list["result"]:
                if (r["name"] == full_subdomain):
                    exists = True
                    if (r["content"] != ip["ip"]):
                        if (dns_id == ""):
                            dns_id = r["id"]
                        else:
                            stale_record_ids.append(r["id"])
            if(exists == False):
                logging.warning("Adding new record " + str(record))
                if not dry_run:
                    response = cf_api(
                        "zones/" + c['zone_id'] + "/dns_records", "POST", c, {}, record)
                else: 
                    logging.warning("Didn't work because of dry-run.")
            elif(dns_id != ""):
                # Only update if the record content is different
                logging.warning("Updating record " + str(record))
                if not dry_run:
                    response = cf_api(
                        "zones/" + c['zone_id'] + "/dns_records/" + dns_id, "PUT", c, {}, record)
                else:
                    logging.warning("Didn't work because of dry-run.")

    # Delete duplicate, stale records
    for identifier in stale_record_ids:
        logging.warning("Deleting stale record " + str(identifier))
        if not dry_run:
            response = cf_api(
                "zones/" + c['zone_id'] + "/dns_records/" + identifier, "DELETE", c)
        else:
            logging.warning("Didn't work because of dry-run.")

    return True


def cf_api(endpoint, method, config, headers={}, data=False):
    api_token = config['authentication']['api_token']
    if api_token != '' and api_token != 'api_token_here':
        headers = {
            "Authorization": "Bearer " + api_token,
            **headers
        }
    else:
        headers = {
            "X-Auth-Email": config['authentication']['api_key']['account_email'],
            "X-Auth-Key": config['authentication']['api_key']['api_key'],        
        }

    while True:
        try:
            if(data == False):
                response = requests.request(
                    method, "https://api.cloudflare.com/client/v4/" + endpoint, headers=headers, timeout=60)
            else:
                response = requests.request(
                    method, "https://api.cloudflare.com/client/v4/" + endpoint, headers=headers, json=data, timeout=60)
        except Exception as e:
            logging.error("Unable to access cloudflare API: " + str(e))
            logging.error("Retrying...")
            continue
        break

    return response.json()

def updateIPs():
    for ip in getIPs_self():
        logging.info(f"Committing record {ip}")
        commitRecord(ip)

def keepAwake():
    ES_SYSTEM_REQUIRED   = 0x00000001
    ES_DISPLAY_REQUIRED  = 0x00000002
    ES_AWAYMODE_REQUIRED = 0x00000040
    ES_CONTINUOUS        = 0x80000000
    if hasattr(ctypes, "windll"):
        logging.warning("Will keep windows awake.")
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)



parser = argparse.ArgumentParser()
parser.add_argument("-r", "--repeat", action="store_true", default=False, help="Update every 10 min")
parser.add_argument("-d", "--dry-run", action="store_true", default=False, help="Dry run and will not change your DNS records")
parser.add_argument("-l", "--log-level", action="store", type=str, default="warning", help="Log level, one of notset/debug/info/warning/error/critical/fatal")
args = parser.parse_args()

logging.basicConfig(format='%(asctime)s - %(name)s[line:%(lineno)d] - %(levelname)s - %(message)s')
log_level = args.log_level.lower()
if log_level in log_level_table:
    logging.root.level=log_level_table[log_level]
else:
    logging.warning("Invalid log level, set to warning.")

logging.debug(str(args))
dry_run = args.dry_run

if(version < 3.5):
    logging.critical("This script requires Python 3.5+")
    exit(-1)

with open(PATH + "config.json") as config_file:
    logging.debug("Loading config: " + PATH + "config.json")
    config = json.loads(config_file.read())
    logging.debug(str(config))

if(args.repeat):
    keepAwake()
    logging.warning("Updating A & AAAA records every 10 minutes")
    delay = 10*60 # 10 minutes
    next_time = time.time() + delay
    while True:
        logging.info(f"Working...")
        updateIPs()
        logging.warning(f"Job done.")
        time.sleep(max(0, next_time - time.time()))
        next_time += (time.time() - next_time) // delay * delay + delay
else:
    updateIPs()
logging.warning("Script finished.")