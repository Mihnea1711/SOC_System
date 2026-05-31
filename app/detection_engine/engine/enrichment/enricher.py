import os
from typing import Dict, Any, Set
import geoip2.database
import geoip2.errors
from engine.utils.logger import logger

class Enricher:
    """
    Enriches normalized events with additional context before detection.
    Currently supports:
    - Threat Intelligence (checking IPs against a known-bad list)
    - GeoIP lookup (mapping IPs to countries)
    """
    def __init__(self, threat_intel_path: str = None, geoip_path: str = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if threat_intel_path is None:
            threat_intel_path = os.path.join(base_dir, "threat_intel.txt")
            
        if geoip_path is None:
            geoip_path = os.path.join(base_dir, "geoip", "GeoLite2-Country.mmdb")
            
        # Initialize Threat Intel
        self.threat_intel_ips: Set[str] = self._load_threat_intel(threat_intel_path)
        logger.info(f"Enricher initialized. Loaded {len(self.threat_intel_ips)} threat intel IPs.")

        # Initialize GeoIP
        self.geoip_reader = None
        try:
            if os.path.exists(geoip_path):
                self.geoip_reader = geoip2.database.Reader(geoip_path)
                logger.info("GeoIP database loaded successfully.")
            else:
                logger.warning(f"GeoIP database not found at {geoip_path}. GeoIP enrichment will be disabled.")
        except Exception:
            logger.exception(f"Failed to initialize GeoIP reader from {geoip_path}")

    def _load_threat_intel(self, file_path: str) -> Set[str]:
        """Loads a list of malicious IPs from a text file into a fast-lookup Set."""
        ips = set()
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Ignore empty lines and comments
                        if line and not line.startswith('#'):
                            ips.add(line)
            else:
                logger.warning(f"Threat intel file not found at {file_path}. Threat intel enrichment will be disabled.")
        except Exception:
            logger.exception(f"Failed to load threat intel from {file_path}")
            
        return ips

    def enrich(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a normalized event and adds enrichment fields.
        Returns the modified event.
        """
        source_ip = event.get("source_ip")
        
        # 1. Threat Intel Enrichment
        event["is_threat_intel_match"] = False
        if source_ip and source_ip in self.threat_intel_ips:
            event["is_threat_intel_match"] = True
            
        # 2. GeoIP Enrichment
        event["source_country_iso"] = None
        event["source_country_name"] = None
        if self.geoip_reader and source_ip:
            try:
                # We skip local/private Docker IPs to avoid unnecessary exceptions
                if not source_ip.startswith(("10.", "172.", "192.168.", "127.")):
                    response = self.geoip_reader.country(source_ip)
                    event["source_country_iso"] = response.country.iso_code
                    event["source_country_name"] = response.country.name
            except geoip2.errors.AddressNotFoundError:
                pass # IP not found in database, perfectly normal
            except Exception:
                logger.exception(f"Error looking up GeoIP for {source_ip}")
        
        return event
