import os
import json
from typing import Dict, Any, Set
import geoip2.database
import geoip2.errors
from engine.utils.logger import logger
from engine.state.base import StateStore

class Enricher:
    """
    Enriches normalized events with additional context before detection.
    Currently supports:
    - Threat Intelligence (checking IPs against a known-bad list with structured data)
    - GeoIP lookup (mapping IPs to countries)
    - First Seen Tracking (behavioral enrichment using StateStore)
    """
    def __init__(self, threat_intel_path: str = None, geoip_city_path: str = None, geoip_asn_path: str = None, geoip_country_path: str = None, state_store: StateStore = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.state_store = state_store
        
        if threat_intel_path is None:
            threat_intel_path = os.path.join(base_dir, "threat_intel.json")
            
        if geoip_city_path is None:
            geoip_city_path = os.path.join(base_dir, "geoip", "GeoLite2-City.mmdb")
            
        if geoip_asn_path is None:
            geoip_asn_path = os.path.join(base_dir, "geoip", "GeoLite2-ASN.mmdb")
            
        if geoip_country_path is None:
            geoip_country_path = os.path.join(base_dir, "geoip", "GeoLite2-Country.mmdb")
            
        # Initialize Threat Intel
        self.threat_intel_data: Dict[str, dict] = self._load_threat_intel(threat_intel_path)
        logger.info(f"Enricher initialized. Loaded {len(self.threat_intel_data)} threat intel IPs.")

        # Initialize GeoIP Readers
        self.geoip_city_reader = None
        self.geoip_asn_reader = None
        self.geoip_country_reader = None
        
        try:
            if os.path.exists(geoip_city_path):
                self.geoip_city_reader = geoip2.database.Reader(geoip_city_path)
                logger.info("GeoIP City database loaded successfully.")
            elif os.path.exists(geoip_country_path):
                self.geoip_country_reader = geoip2.database.Reader(geoip_country_path)
                logger.info("GeoIP Country database loaded successfully (City not found).")
            else:
                logger.warning("No GeoIP City or Country database found. Location enrichment disabled.")
                
            if os.path.exists(geoip_asn_path):
                self.geoip_asn_reader = geoip2.database.Reader(geoip_asn_path)
                logger.info("GeoIP ASN database loaded successfully.")
            else:
                logger.warning("No GeoIP ASN database found. ASN enrichment disabled.")
        except Exception:
            logger.exception("Failed to initialize GeoIP readers")


    def _load_threat_intel(self, file_path: str) -> Dict[str, dict]:
        """Loads structured malicious IPs from a JSON file into a fast-lookup Dictionary."""
        intel_data = {}
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        if "ip" in item:
                            intel_data[item["ip"]] = {
                                "threat_type": item.get("threat_type", "Unknown"),
                                "confidence_score": item.get("confidence_score", 50)
                            }
            else:
                logger.warning(f"Threat intel file not found at {file_path}. Threat intel enrichment will be disabled.")
        except Exception:
            logger.exception(f"Failed to load threat intel from {file_path}")
            
        return intel_data

    def enrich(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a normalized event and adds enrichment fields.
        Returns the modified event.
        """
        source_ip = event.get("source_ip")
        
        # 1. Threat Intel Enrichment
        event["is_threat_intel_match"] = False
        if source_ip and source_ip in self.threat_intel_data:
            event["is_threat_intel_match"] = True
            event["threat_type"] = self.threat_intel_data[source_ip]["threat_type"]
            event["threat_confidence"] = self.threat_intel_data[source_ip]["confidence_score"]
            
         # 2. GeoIP Enrichment
        event["source_country_iso"] = None
        event["source_country_name"] = None
        event["source_city_name"] = None
        event["source_location"] = None
        event["source_asn"] = None
        event["source_isp_name"] = None
        
        # skip local/private Docker IPs to avoid unnecessary exceptions
        if source_ip and not source_ip.startswith(("10.", "172.", "192.168.", "127.")):
            # City / Country Lookup
            try:
                if self.geoip_city_reader:
                    response = self.geoip_city_reader.city(source_ip)
                    event["source_country_iso"] = response.country.iso_code
                    event["source_country_name"] = response.country.name
                    event["source_city_name"] = response.city.name
                    if response.location.latitude and response.location.longitude:
                        event["source_location"] = {
                            "lat": response.location.latitude,
                            "lon": response.location.longitude
                        }

                elif self.geoip_country_reader:
                    response = self.geoip_country_reader.country(source_ip)
                    event["source_country_iso"] = response.country.iso_code
                    event["source_country_name"] = response.country.name
            except geoip2.errors.AddressNotFoundError:
                pass # IP not found in database
            except Exception:
                logger.exception(f"Error looking up GeoIP City/Country for {source_ip}")
                
            # ASN Lookup
            try:
                if self.geoip_asn_reader:
                    response = self.geoip_asn_reader.asn(source_ip)
                    event["source_asn"] = response.autonomous_system_number
                    event["source_isp_name"] = response.autonomous_system_organization
            except geoip2.errors.AddressNotFoundError:
                pass
            except Exception:
                logger.exception(f"Error looking up GeoIP ASN for {source_ip}")
                
        # 3. First Seen Tracking (Behavioral)
        event["is_new_ip"] = False
        if self.state_store and source_ip:
            first_seen_key = f"first_seen_{source_ip}"
            if not self.state_store.get(first_seen_key):
                # never seen this IP before
                event["is_new_ip"] = True
                # Store it so we know we've seen it. TTL could be long (e.g., 24 hours) or infinite if supported.
                # set a 24 hour TTL (86400 seconds)
                self.state_store.set(first_seen_key, True, ttl_seconds=86400)
        
        return event

