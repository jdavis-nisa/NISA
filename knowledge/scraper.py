#!/usr/bin/env python3.11
"""
NISA Knowledge Web Scraper v2.0
Upgraded: 200 results per ArXiv query, PDF full-text extraction,
10 new domains, deeper coverage across all existing domains.
Maintains security and integrity - only verified public sources.
"""
import os
import time
import json
import hashlib
import requests
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

SSD_BASE = "/Volumes/Share Drive/NISA/knowledge"
SCRAPER_STATE = "/Users/joshuadavis/NISA/knowledge/scraper_state.json"
DELAY = 2         # seconds between requests
ARXIV_RESULTS = 200   # abstracts per query (was 50)
MAX_CONTENT = 80000   # chars per file (was 50000)

# High-value domains that get PDF full-text extraction
PDF_PRIORITY_DOMAINS = {"radar_ew", "security", "quantum_advanced", "physics_advanced"}

# ─── SOURCES ──────────────────────────────────────────────────────
SOURCES = {

    # ── SECURITY ──────────────────────────────────────────────────
    "security": [
        {"name": "NIST_NVD_CRITICAL", "url": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100&cvssV3Severity=CRITICAL", "type": "nvd"},
        {"name": "NIST_NVD_HIGH", "url": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100&cvssV3Severity=HIGH", "type": "nvd"},
        {"name": "NIST_NVD_2024", "url": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100&pubStartDate=2024-01-01T00:00:00.000&pubEndDate=2024-12-31T23:59:59.999", "type": "nvd"},
        {"name": "NIST_NVD_2023", "url": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100&pubStartDate=2023-01-01T00:00:00.000&pubEndDate=2023-12-31T23:59:59.999", "type": "nvd"},
        {"name": "MITRE_ATTACK_Enterprise", "url": "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json", "type": "mitre"},
        {"name": "MITRE_ATTACK_Mobile", "url": "https://raw.githubusercontent.com/mitre/cti/master/mobile-attack/mobile-attack.json", "type": "mitre"},
        {"name": "MITRE_ATTACK_ICS", "url": "https://raw.githubusercontent.com/mitre/cti/master/ics-attack/ics-attack.json", "type": "mitre"},
        {"name": "OWASP_Top10_2021", "url": "https://raw.githubusercontent.com/OWASP/Top10/master/2021/docs/A00_2021_Introduction.md", "type": "text"},
        {"name": "OWASP_Top10_API", "url": "https://raw.githubusercontent.com/OWASP/API-Security/master/editions/2023/en/0x00-header.md", "type": "text"},
        {"name": "OWASP_Testing_Guide", "url": "https://raw.githubusercontent.com/OWASP/wstg/master/document/4-Web_Application_Security_Testing/README.md", "type": "text"},
        {"name": "NIST_CSF_2", "url": "https://raw.githubusercontent.com/usnistgov/NIST-Cybersecurity-Framework/main/README.md", "type": "text"},
        {"name": "NIST_800_53", "url": "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/markdown/SP800-53_Rev5_catalog.md", "type": "text"},
        {"name": "ArXiv_Malware_Detection", "url": f"https://export.arxiv.org/api/query?search_query=malware+detection+machine+learning&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_APT_Campaigns", "url": f"https://export.arxiv.org/api/query?search_query=advanced+persistent+threat+APT+campaign+attribution&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Ransomware", "url": f"https://export.arxiv.org/api/query?search_query=ransomware+attack+analysis+defense+recovery&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Intrusion_Detection", "url": f"https://export.arxiv.org/api/query?search_query=intrusion+detection+system+neural+network&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Vulnerability_Research", "url": f"https://export.arxiv.org/api/query?search_query=vulnerability+assessment+exploit+CVE&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_ZeroTrust", "url": f"https://export.arxiv.org/api/query?search_query=zero+trust+security+architecture+NIST&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_AI_Security", "url": f"https://export.arxiv.org/api/query?search_query=adversarial+machine+learning+security+attack&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Network_Defense", "url": f"https://export.arxiv.org/api/query?search_query=network+defense+threat+detection+SOC&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Phishing", "url": f"https://export.arxiv.org/api/query?search_query=phishing+social+engineering+spear+phishing&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cryptography", "url": f"https://export.arxiv.org/api/query?search_query=cryptography+encryption+post+quantum&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SIEM_Analytics", "url": f"https://export.arxiv.org/api/query?search_query=SIEM+security+analytics+log+analysis+detection&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Threat_Intel", "url": f"https://export.arxiv.org/api/query?search_query=cyber+threat+intelligence+STIX+TAXII&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cloud_Security", "url": f"https://export.arxiv.org/api/query?search_query=cloud+security+misconfiguration+AWS+Azure&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_ICS_SCADA", "url": f"https://export.arxiv.org/api/query?search_query=ICS+SCADA+industrial+control+security+Stuxnet&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Supply_Chain", "url": f"https://export.arxiv.org/api/query?search_query=supply+chain+attack+software+dependency+SolarWinds&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Active_Directory", "url": f"https://export.arxiv.org/api/query?search_query=Active+Directory+Kerberos+attack+lateral+movement&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Web_App_Security", "url": f"https://export.arxiv.org/api/query?search_query=web+application+security+SQL+injection+XSS+CSRF&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Forensics_IR", "url": f"https://export.arxiv.org/api/query?search_query=digital+forensics+incident+response+DFIR&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Red_Team", "url": f"https://export.arxiv.org/api/query?search_query=red+team+penetration+testing+offensive+security&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "PayloadsAllTheThings", "url": "https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master/README.md", "type": "text"},
        {"name": "HackTricks_Linux_Privesc", "url": "https://raw.githubusercontent.com/carlospolop/hacktricks/master/linux-hardening/privilege-escalation/README.md", "type": "text"},
        {"name": "HackTricks_Windows_Privesc", "url": "https://raw.githubusercontent.com/carlospolop/hacktricks/master/windows-hardening/windows-local-privilege-escalation/README.md", "type": "text"},
        {"name": "HackTricks_Active_Directory", "url": "https://raw.githubusercontent.com/carlospolop/hacktricks/master/windows-hardening/active-directory-methodology/README.md", "type": "text"},
        {"name": "GTFOBins", "url": "https://raw.githubusercontent.com/GTFOBins/GTFOBins.github.io/master/README.md", "type": "text"},
        {"name": "OWASP_WSTG", "url": "https://raw.githubusercontent.com/OWASP/wstg/master/document/README.md", "type": "text"},
        {"name": "PortSwigger_SQLi", "url": "https://portswigger.net/web-security/sql-injection", "type": "text"},
        {"name": "PortSwigger_XSS", "url": "https://portswigger.net/web-security/cross-site-scripting", "type": "text"},
        {"name": "PortSwigger_SSRF", "url": "https://portswigger.net/web-security/ssrf", "type": "text"},
        {"name": "PortSwigger_XXE", "url": "https://portswigger.net/web-security/xxe", "type": "text"},
        {"name": "PortSwigger_Auth", "url": "https://portswigger.net/web-security/authentication", "type": "text"},
        {"name": "Impacket_Docs", "url": "https://raw.githubusercontent.com/fortra/impacket/master/README.md", "type": "text"},
        {"name": "Scapy_Docs", "url": "https://raw.githubusercontent.com/secdev/scapy/master/README.rst", "type": "text"},
    ],

    # ── SECURITY HISTORICAL ──────────────────────────────────────
    "security_historical": [
        {"name": "ArXiv_Stuxnet_Analysis", "url": f"https://export.arxiv.org/api/query?search_query=Stuxnet+worm+ICS+SCADA+Iran+nuclear&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SolarWinds", "url": f"https://export.arxiv.org/api/query?search_query=SolarWinds+Sunburst+supply+chain+attack+analysis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_WannaCry", "url": f"https://export.arxiv.org/api/query?search_query=WannaCry+ransomware+EternalBlue+NHS+analysis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_NotPetya", "url": f"https://export.arxiv.org/api/query?search_query=NotPetya+cyberattack+Ukraine+Maersk+wiper&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Colonial_Pipeline", "url": f"https://export.arxiv.org/api/query?search_query=Colonial+Pipeline+ransomware+DarkSide+critical+infrastructure&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Mirai_Botnet", "url": f"https://export.arxiv.org/api/query?search_query=Mirai+botnet+IoT+DDoS+Dyn+DNS&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Equifax_Breach", "url": f"https://export.arxiv.org/api/query?search_query=Equifax+data+breach+Apache+Struts+PII&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Target_Breach", "url": f"https://export.arxiv.org/api/query?search_query=Target+breach+POS+malware+retail+credit+card&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Log4Shell_Analysis", "url": f"https://export.arxiv.org/api/query?search_query=Log4Shell+Log4j+CVE-2021-44228+analysis+patch&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_MOVEit_Breach", "url": f"https://export.arxiv.org/api/query?search_query=MOVEit+Cl0p+ransomware+file+transfer+breach&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Volt_Typhoon", "url": f"https://export.arxiv.org/api/query?search_query=Volt+Typhoon+China+critical+infrastructure+living+off+land&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Midnight_Blizzard", "url": f"https://export.arxiv.org/api/query?search_query=Midnight+Blizzard+APT29+Microsoft+email+hack&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Nation_State_Attacks", "url": f"https://export.arxiv.org/api/query?search_query=nation+state+cyberattack+attribution+espionage&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_APT28_Fancy_Bear", "url": f"https://export.arxiv.org/api/query?search_query=APT28+Fancy+Bear+GRU+Russia+campaign&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Lazarus_DPRK", "url": f"https://export.arxiv.org/api/query?search_query=Lazarus+DPRK+North+Korea+cryptocurrency+theft&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Timeline_Major_Breaches", "url": f"https://export.arxiv.org/api/query?search_query=major+data+breach+timeline+history+cybersecurity&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cyber_Warfare_History", "url": f"https://export.arxiv.org/api/query?search_query=cyber+warfare+history+Estonia+Georgia+Ukraine&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Zero_Day_History", "url": f"https://export.arxiv.org/api/query?search_query=zero+day+exploit+history+Pwn2Own+Zerodium&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── SECURITY OFFENSIVE ────────────────────────────────────────
    "security_offensive": [
        {"name": "ArXiv_Exploit_Development", "url": f"https://export.arxiv.org/api/query?search_query=exploit+development+buffer+overflow+ROP+chain&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Living_Off_Land", "url": f"https://export.arxiv.org/api/query?search_query=living+off+the+land+LOLBAS+fileless+malware&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_C2_Frameworks", "url": f"https://export.arxiv.org/api/query?search_query=command+control+C2+framework+Cobalt+Strike+detection&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Kerberoasting", "url": f"https://export.arxiv.org/api/query?search_query=Kerberoasting+Pass+the+Hash+Active+Directory+attack&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Lateral_Movement", "url": f"https://export.arxiv.org/api/query?search_query=lateral+movement+SMB+WMI+PsExec+detection&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Privilege_Escalation", "url": f"https://export.arxiv.org/api/query?search_query=privilege+escalation+Windows+Linux+technique&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Persistence_Techniques", "url": f"https://export.arxiv.org/api/query?search_query=persistence+mechanisms+registry+scheduled+task+backdoor&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Credential_Dumping", "url": f"https://export.arxiv.org/api/query?search_query=credential+dumping+Mimikatz+LSASS+NTLM+hash&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Defense_Evasion", "url": f"https://export.arxiv.org/api/query?search_query=defense+evasion+AV+bypass+obfuscation+AMSI&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Wireless_Attacks", "url": f"https://export.arxiv.org/api/query?search_query=wireless+attack+WiFi+WPA2+PMKID+evil+twin&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Social_Engineering", "url": f"https://export.arxiv.org/api/query?search_query=social+engineering+vishing+pretexting+BEC&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Physical_Security", "url": f"https://export.arxiv.org/api/query?search_query=physical+security+access+control+RFID+bypass&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_AI_Attacks", "url": f"https://export.arxiv.org/api/query?search_query=AI+LLM+prompt+injection+jailbreak+model+attack&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_BloodHound_Methodology", "url": f"https://export.arxiv.org/api/query?search_query=BloodHound+AD+attack+path+graph+analysis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Exfiltration", "url": f"https://export.arxiv.org/api/query?search_query=data+exfiltration+covert+channel+DNS+tunneling&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── SECURITY DEFENSIVE ────────────────────────────────────────
    "security_defensive": [
        {"name": "ArXiv_Detection_Engineering", "url": f"https://export.arxiv.org/api/query?search_query=detection+engineering+SIEM+rule+sigma&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Threat_Hunting", "url": f"https://export.arxiv.org/api/query?search_query=threat+hunting+hypothesis+driven+detection&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SOC_Operations", "url": f"https://export.arxiv.org/api/query?search_query=SOC+security+operations+center+analyst+playbook&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Incident_Response", "url": f"https://export.arxiv.org/api/query?search_query=incident+response+containment+eradication+recovery&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_EDR_XDR", "url": f"https://export.arxiv.org/api/query?search_query=EDR+XDR+endpoint+detection+response+telemetry&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Blue_Team", "url": f"https://export.arxiv.org/api/query?search_query=blue+team+defensive+security+hardening&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Deception_Honeypot", "url": f"https://export.arxiv.org/api/query?search_query=honeypot+deception+technology+canary+token&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Vulnerability_Management", "url": f"https://export.arxiv.org/api/query?search_query=vulnerability+management+patch+prioritization+CVSS&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Security_Metrics", "url": f"https://export.arxiv.org/api/query?search_query=security+metrics+KPI+measurement+risk+quantification&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "NIST_IR_Guide", "url": "https://raw.githubusercontent.com/usnistgov/SP800-61r3/main/README.md", "type": "text"},
        {"name": "Sigma_Rules", "url": "https://raw.githubusercontent.com/SigmaHQ/sigma/master/README.md", "type": "text"},
        {"name": "MITRE_D3FEND", "url": f"https://export.arxiv.org/api/query?search_query=MITRE+D3FEND+defensive+countermeasure+framework&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Threat_Modeling", "url": f"https://export.arxiv.org/api/query?search_query=threat+modeling+STRIDE+PASTA+architecture+security&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Purple_Team", "url": f"https://export.arxiv.org/api/query?search_query=purple+team+exercise+red+blue+collaboration&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_MITRE_ATT_Coverage", "url": f"https://export.arxiv.org/api/query?search_query=MITRE+ATT+CK+detection+coverage+gap+analysis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── RADAR / EW ────────────────────────────────────────────────
    "radar_ew": [
        {"name": "DTIC_Radar_Signal", "url": "https://apps.dtic.mil/sti/api/search?q=radar+signal+processing&fields=title,abstract&rows=50", "type": "dtic"},
        {"name": "NASA_Radar_Papers", "url": "https://ntrs.nasa.gov/api/citations/search?q=radar&rows=30", "type": "nasa"},
        {"name": "ArXiv_Radar_ML", "url": f"https://export.arxiv.org/api/query?search_query=radar+machine+learning+target+detection&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Signal_Processing", "url": f"https://export.arxiv.org/api/query?search_query=cat:eess.SP&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Phased_Array", "url": f"https://export.arxiv.org/api/query?search_query=phased+array+antenna+beamforming+digital&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_SAR_Imaging", "url": f"https://export.arxiv.org/api/query?search_query=synthetic+aperture+radar+SAR+imaging&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_LPI_Radar", "url": f"https://export.arxiv.org/api/query?search_query=LPI+radar+low+probability+intercept+waveform&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_EW_Jamming", "url": f"https://export.arxiv.org/api/query?search_query=electronic+warfare+jamming+ECM+DRFM&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_FMCW_Radar", "url": f"https://export.arxiv.org/api/query?search_query=FMCW+radar+automotive+range+doppler&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Radar_Waveform_Design", "url": f"https://export.arxiv.org/api/query?search_query=radar+waveform+design+ambiguity+function+LFM&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Polyphase_Codes", "url": f"https://export.arxiv.org/api/query?search_query=polyphase+codes+Frank+P1+P2+P4+radar+waveform&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Frequency_Hopping", "url": f"https://export.arxiv.org/api/query?search_query=frequency+hopping+spread+spectrum+radar+LPI&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Doppler_Processing", "url": f"https://export.arxiv.org/api/query?search_query=Doppler+processing+MTI+MTD+moving+target&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Radar_Cross_Section", "url": f"https://export.arxiv.org/api/query?search_query=radar+cross+section+RCS+stealth+signature&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_ESM_ELINT", "url": f"https://export.arxiv.org/api/query?search_query=electronic+support+measures+ELINT+signal+intercept&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Cognitive_Radar", "url": f"https://export.arxiv.org/api/query?search_query=cognitive+radar+adaptive+waveform+environment&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_MIMO_Radar", "url": f"https://export.arxiv.org/api/query?search_query=MIMO+radar+multiple+input+output+waveform&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Radar_Clutter", "url": f"https://export.arxiv.org/api/query?search_query=radar+clutter+suppression+CFAR+detection&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_EW_Defense", "url": f"https://export.arxiv.org/api/query?search_query=electronic+warfare+defense+counter+countermeasure&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Radar_Deep_Learning", "url": f"https://export.arxiv.org/api/query?search_query=radar+deep+learning+classification+recognition&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_EOB", "url": f"https://export.arxiv.org/api/query?search_query=electronic+order+of+battle+emitter+identification&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_SDR_Waveform", "url": f"https://export.arxiv.org/api/query?search_query=software+defined+radio+SDR+waveform+GNU+Radio&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Pulse_Compression", "url": f"https://export.arxiv.org/api/query?search_query=pulse+compression+chirp+Barker+matched+filter&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Spectrum_Sensing", "url": f"https://export.arxiv.org/api/query?search_query=spectrum+sensing+cognitive+radio+interference&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── BUSINESS / FEDERAL CONTRACTS ─────────────────────────────
    "business_contracts": [
        {"name": "ArXiv_Federal_Contracting", "url": f"https://export.arxiv.org/api/query?search_query=federal+government+contracting+procurement+defense&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Proposal_Writing", "url": f"https://export.arxiv.org/api/query?search_query=government+proposal+writing+RFP+technical+volume&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_IDIQ_Contracts", "url": f"https://export.arxiv.org/api/query?search_query=IDIQ+GWAC+indefinite+delivery+contract+government&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Defense_Acquisition", "url": f"https://export.arxiv.org/api/query?search_query=defense+acquisition+DoD+program+management+DoDI&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SBIR_STTR", "url": f"https://export.arxiv.org/api/query?search_query=SBIR+STTR+small+business+innovation+research+DoD&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SOW_PWS", "url": f"https://export.arxiv.org/api/query?search_query=statement+of+work+performance+work+specification&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Contract_Negotiation", "url": f"https://export.arxiv.org/api/query?search_query=contract+negotiation+terms+conditions+government&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Business_Development", "url": f"https://export.arxiv.org/api/query?search_query=business+development+capture+management+BD+pipeline&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Technical_Reports", "url": f"https://export.arxiv.org/api/query?search_query=technical+report+white+paper+capability+brief&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Startup_Entrepreneurship", "url": f"https://export.arxiv.org/api/query?search_query=startup+entrepreneurship+innovation+commercialization&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_IP_Patents", "url": f"https://export.arxiv.org/api/query?search_query=intellectual+property+patent+strategy+technology+transfer&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Project_Management", "url": f"https://export.arxiv.org/api/query?search_query=project+management+agile+scrum+earned+value&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "FAR_Overview", "url": "https://raw.githubusercontent.com/GSA/GSA-Acquisition-FAR/main/README.md", "type": "text"},
        {"name": "ArXiv_CUI_Handling", "url": f"https://export.arxiv.org/api/query?search_query=controlled+unclassified+information+CUI+handling+NIST&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_ITAR_EAR", "url": f"https://export.arxiv.org/api/query?search_query=ITAR+EAR+export+control+technology+defense&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Pricing_Strategy", "url": f"https://export.arxiv.org/api/query?search_query=government+contract+pricing+strategy+cost+analysis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── DEFENSE / COMPLIANCE ─────────────────────────────────────
    "defense_compliance": [
        {"name": "ArXiv_NIST_800_171", "url": f"https://export.arxiv.org/api/query?search_query=NIST+800-171+CUI+defense+contractor+compliance&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_CMMC", "url": f"https://export.arxiv.org/api/query?search_query=CMMC+cybersecurity+maturity+model+certification+DoD&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_FedRAMP", "url": f"https://export.arxiv.org/api/query?search_query=FedRAMP+federal+cloud+authorization+ATO&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_RMF", "url": f"https://export.arxiv.org/api/query?search_query=Risk+Management+Framework+RMF+ATO+authorization&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_FISMA", "url": f"https://export.arxiv.org/api/query?search_query=FISMA+federal+information+security+management+compliance&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_IL_Levels", "url": f"https://export.arxiv.org/api/query?search_query=DoD+impact+level+IL2+IL4+IL5+cloud+classification&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Security_Clearance", "url": f"https://export.arxiv.org/api/query?search_query=security+clearance+SF-86+adjudication+background+investigation&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_PII_Privacy", "url": f"https://export.arxiv.org/api/query?search_query=PII+privacy+data+protection+GDPR+compliance&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SOC2_ISO27001", "url": f"https://export.arxiv.org/api/query?search_query=SOC2+ISO+27001+security+audit+compliance+framework&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Post_Quantum_Compliance", "url": f"https://export.arxiv.org/api/query?search_query=post+quantum+cryptography+NIST+FIPS+204+compliance+migration&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_AI_Governance", "url": f"https://export.arxiv.org/api/query?search_query=AI+governance+risk+management+framework+NIST+AI+RMF&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Insider_Threat_Program", "url": f"https://export.arxiv.org/api/query?search_query=insider+threat+program+detection+monitoring&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── LINUX / TERMINAL COMMANDS ─────────────────────────────────
    "linux_commands": [
        {"name": "GNU_Bash_Manual", "url": "https://www.gnu.org/software/bash/manual/bash.html", "type": "text"},
        {"name": "Linux_Man_Pages_Core", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/linux/README.md", "type": "text"},
        {"name": "TLDR_Linux", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/grep.md", "type": "text"},
        {"name": "GTFOBins_Full", "url": "https://raw.githubusercontent.com/GTFOBins/GTFOBins.github.io/master/README.md", "type": "text"},
        {"name": "Linux_Command_101", "url": "https://raw.githubusercontent.com/nicowillis/linux-commands/main/README.md", "type": "text"},
        {"name": "ArXiv_Linux_Admin", "url": f"https://export.arxiv.org/api/query?search_query=Linux+system+administration+command+line+tutorial&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Bash_Scripting", "url": f"https://export.arxiv.org/api/query?search_query=bash+shell+scripting+automation+linux+command&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Network_Commands", "url": f"https://export.arxiv.org/api/query?search_query=network+diagnostic+commands+tcpdump+netstat+ss+linux&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Grep_Sed_Awk", "url": f"https://export.arxiv.org/api/query?search_query=grep+sed+awk+regular+expressions+text+processing+linux&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Systemd", "url": f"https://export.arxiv.org/api/query?search_query=systemd+service+management+Linux+init+system&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Docker_Commands", "url": f"https://export.arxiv.org/api/query?search_query=Docker+container+command+line+management&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Git_Commands", "url": f"https://export.arxiv.org/api/query?search_query=Git+version+control+command+workflow+branch&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SSH_OpenSSL", "url": f"https://export.arxiv.org/api/query?search_query=SSH+OpenSSL+TLS+certificate+command+line&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Python_CLI", "url": f"https://export.arxiv.org/api/query?search_query=Python+command+line+automation+script+argparse&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Terminal_Productivity", "url": f"https://export.arxiv.org/api/query?search_query=terminal+productivity+vim+tmux+zsh+workflow&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Forensics_Commands", "url": f"https://export.arxiv.org/api/query?search_query=forensics+command+line+dd+strings+file+analysis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Package_Management", "url": f"https://export.arxiv.org/api/query?search_query=Linux+package+manager+apt+yum+brew+pip&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "TLDR_Nmap", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/nmap.md", "type": "text"},
        {"name": "TLDR_Curl", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/curl.md", "type": "text"},
        {"name": "TLDR_Find", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/find.md", "type": "text"},
        {"name": "TLDR_SSH", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/ssh.md", "type": "text"},
        {"name": "TLDR_Tcpdump", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/tcpdump.md", "type": "text"},
        {"name": "TLDR_Awk", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/awk.md", "type": "text"},
        {"name": "TLDR_Sed", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/sed.md", "type": "text"},
        {"name": "TLDR_Grep", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/grep.md", "type": "text"},
        {"name": "TLDR_Ps", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/ps.md", "type": "text"},
        {"name": "TLDR_Netstat", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/netstat.md", "type": "text"},
        {"name": "TLDR_Git", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/git.md", "type": "text"},
        {"name": "TLDR_Docker", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/docker.md", "type": "text"},
        {"name": "TLDR_Python", "url": "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/python.md", "type": "text"},
    ],

    # ── COMBAT MEDICINE / TCCC ────────────────────────────────────
    "combat_medicine": [
        {"name": "ArXiv_TCCC", "url": f"https://export.arxiv.org/api/query?search_query=tactical+combat+casualty+care+TCCC+prehospital&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Hemorrhage_Control", "url": f"https://export.arxiv.org/api/query?search_query=hemorrhage+control+tourniquet+hemostatic+agent+trauma&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Airway_Management", "url": f"https://export.arxiv.org/api/query?search_query=airway+management+intubation+cricothyrotomy+field&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_MARCH_Protocol", "url": f"https://export.arxiv.org/api/query?search_query=MARCH+PAWS+protocol+combat+trauma+military+medicine&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Blast_Injury", "url": f"https://export.arxiv.org/api/query?search_query=blast+injury+IED+TBI+trauma+military&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Combat_Medic", "url": f"https://export.arxiv.org/api/query?search_query=combat+medic+68W+field+medicine+Afghanistan+Iraq&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Wound_Ballistics", "url": f"https://export.arxiv.org/api/query?search_query=wound+ballistics+gunshot+injury+treatment&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_MEDEVAC", "url": f"https://export.arxiv.org/api/query?search_query=MEDEVAC+medical+evacuation+9-line+casualty+transport&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_PTSD_Veterans", "url": f"https://export.arxiv.org/api/query?search_query=PTSD+veterans+combat+trauma+treatment+VA&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_TBI_Veterans", "url": f"https://export.arxiv.org/api/query?search_query=traumatic+brain+injury+TBI+veterans+blast+cognitive&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Trauma_Surgery", "url": f"https://export.arxiv.org/api/query?search_query=damage+control+surgery+trauma+resuscitation&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Military_Pharmacology", "url": f"https://export.arxiv.org/api/query?search_query=military+pharmacology+ketamine+tranexamic+acid+morphine&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Point_of_Care", "url": f"https://export.arxiv.org/api/query?search_query=point+of+care+diagnostics+field+hospital+austere&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Gray_Anatomy", "url": "https://www.gutenberg.org/cache/epub/39722/pg39722.txt", "type": "text"},
        {"name": "US_Army_Survival_Manual", "url": "https://www.gutenberg.org/files/17007/17007-0.txt", "type": "text"},
    ],

    # ── EXISTING DOMAINS (enhanced) ───────────────────────────────
    "radar_ew_deep": [
        {"name": "ArXiv_Barker_Codes", "url": f"https://export.arxiv.org/api/query?search_query=Barker+code+sidelobe+pulse+compression+binary&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Noise_Radar", "url": f"https://export.arxiv.org/api/query?search_query=noise+radar+random+waveform+LPI+covert&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Stepped_Frequency", "url": f"https://export.arxiv.org/api/query?search_query=stepped+frequency+radar+waveform+high+resolution&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_OFDM_Radar", "url": f"https://export.arxiv.org/api/query?search_query=OFDM+radar+waveform+orthogonal+frequency+division&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_JSR_Calculations", "url": f"https://export.arxiv.org/api/query?search_query=jamming+signal+ratio+JSR+radar+performance+equation&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Intercept_Receiver", "url": f"https://export.arxiv.org/api/query?search_query=intercept+receiver+ESM+threat+radar+warning&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Chaff_Flare", "url": f"https://export.arxiv.org/api/query?search_query=chaff+flare+countermeasure+missile+seeker&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Airborne_Radar", "url": f"https://export.arxiv.org/api/query?search_query=airborne+radar+AESA+fighter+aircraft+radar+system&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Ground_Penetrating", "url": f"https://export.arxiv.org/api/query?search_query=ground+penetrating+radar+GPR+subsurface+detection&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Over_Horizon_Radar", "url": f"https://export.arxiv.org/api/query?search_query=over+horizon+radar+OTH+HF+skywave&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
    ],

    # ── PHILOSOPHY ────────────────────────────────────────────────
    "philosophy": [
        {"name": "Plato_Republic", "url": "https://www.gutenberg.org/files/1497/1497-0.txt", "type": "text"},
        {"name": "Plato_Dialogues", "url": "https://www.gutenberg.org/cache/epub/1656/pg1656.txt", "type": "text"},
        {"name": "Aristotle_Ethics", "url": "https://www.gutenberg.org/files/8438/8438-0.txt", "type": "text"},
        {"name": "Aristotle_Politics", "url": "https://www.gutenberg.org/cache/epub/6762/pg6762.txt", "type": "text"},
        {"name": "Nietzsche_Zarathustra", "url": "https://www.gutenberg.org/files/1998/1998-0.txt", "type": "text"},
        {"name": "Nietzsche_Beyond_Good_Evil", "url": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt", "type": "text"},
        {"name": "Marcus_Aurelius_Meditations", "url": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt", "type": "text"},
        {"name": "Seneca_Letters", "url": "https://www.gutenberg.org/cache/epub/1464/pg1464.txt", "type": "text"},
        {"name": "Epictetus_Discourses", "url": "https://www.gutenberg.org/cache/epub/4135/pg4135.txt", "type": "text"},
        {"name": "Descartes_Meditations", "url": "https://www.gutenberg.org/files/59/59-0.txt", "type": "text"},
        {"name": "Kant_Critique_Pure_Reason", "url": "https://www.gutenberg.org/cache/epub/4280/pg4280.txt", "type": "text"},
        {"name": "Locke_Human_Understanding", "url": "https://www.gutenberg.org/cache/epub/10615/pg10615.txt", "type": "text"},
        {"name": "Hume_Enquiry", "url": "https://www.gutenberg.org/cache/epub/9662/pg9662.txt", "type": "text"},
        {"name": "Spinoza_Ethics", "url": "https://www.gutenberg.org/cache/epub/3800/pg3800.txt", "type": "text"},
        {"name": "Schopenhauer_World_Will", "url": "https://www.gutenberg.org/cache/epub/38427/pg38427.txt", "type": "text"},
        {"name": "Kierkegaard_Fear_Trembling", "url": "https://www.gutenberg.org/cache/epub/34888/pg34888.txt", "type": "text"},
        {"name": "ArXiv_Philosophy_Mind", "url": f"https://export.arxiv.org/api/query?search_query=philosophy+of+mind+consciousness+qualia&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Ethics_AI", "url": f"https://export.arxiv.org/api/query?search_query=AI+ethics+moral+philosophy+autonomous+systems&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Philosophy_Science", "url": f"https://export.arxiv.org/api/query?search_query=philosophy+of+science+epistemology+Kuhn+paradigm&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Existentialism", "url": f"https://export.arxiv.org/api/query?search_query=existentialism+Sartre+Camus+Heidegger+being&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Stoicism", "url": f"https://export.arxiv.org/api/query?search_query=Stoicism+Stoic+philosophy+virtue+reason&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── SPIRITUALITY ADVANCED ─────────────────────────────────────
    "spiritual_advanced": [
        {"name": "CIA_Gateway_Experience", "url": "https://www.cia.gov/readingroom/document/cia-rdp96-00788r001700210016-5", "type": "text"},
        {"name": "Bhagavad_Gita", "url": "https://www.gutenberg.org/cache/epub/2388/pg2388.txt", "type": "text"},
        {"name": "Dhammapada", "url": "https://www.gutenberg.org/cache/epub/2017/pg2017.txt", "type": "text"},
        {"name": "Tao_Te_Ching", "url": "https://www.gutenberg.org/cache/epub/216/pg216.txt", "type": "text"},
        {"name": "Upanishads", "url": "https://www.gutenberg.org/cache/epub/68171/pg68171.txt", "type": "text"},
        {"name": "Quran_English", "url": "https://www.gutenberg.org/cache/epub/2800/pg2800.txt", "type": "text"},
        {"name": "Bible_KJV", "url": "https://www.gutenberg.org/cache/epub/10/pg10.txt", "type": "text"},
        {"name": "ArXiv_Consciousness_NCC", "url": f"https://export.arxiv.org/api/query?search_query=consciousness+neural+correlates+NCC+awareness&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Gateway_Monroe", "url": f"https://export.arxiv.org/api/query?search_query=Monroe+Institute+hemi-sync+binaural+consciousness&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_OBE_Research", "url": f"https://export.arxiv.org/api/query?search_query=out+of+body+experience+OBE+sleep+paralysis+autoscopy&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Remote_Viewing_CIA", "url": f"https://export.arxiv.org/api/query?search_query=remote+viewing+Stargate+psi+parapsychology&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Lucid_Dream_WILD", "url": f"https://export.arxiv.org/api/query?search_query=lucid+dreaming+WILD+MILD+technique+REM+induction&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Meditation_Neuroscience", "url": f"https://export.arxiv.org/api/query?search_query=meditation+neuroscience+EEG+alpha+theta+gamma&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_UAP_Scientific", "url": f"https://export.arxiv.org/api/query?search_query=UAP+UFO+unexplained+aerial+phenomena+scientific&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_NDE_Consciousness", "url": f"https://export.arxiv.org/api/query?search_query=near+death+experience+NDE+consciousness+afterlife&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Psychedelics_Mystical", "url": f"https://export.arxiv.org/api/query?search_query=psilocybin+DMT+mystical+experience+ego+dissolution&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Indigenous_Shamanism", "url": f"https://export.arxiv.org/api/query?search_query=shamanism+indigenous+ceremony+vision+quest&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Breathwork_Pranayama", "url": f"https://export.arxiv.org/api/query?search_query=pranayama+Wim+Hof+holotropic+breathwork+altered+state&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_World_Religions", "url": f"https://export.arxiv.org/api/query?search_query=comparative+religion+world+traditions+mysticism&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Guided_Visualization", "url": f"https://export.arxiv.org/api/query?search_query=guided+imagery+visualization+meditation+script+relaxation&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Consciousness", "url": f"https://export.arxiv.org/api/query?search_query=quantum+consciousness+Penrose+Orch+OR+microtubule&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── PHYSICS ADVANCED ─────────────────────────────────────────
    "physics_advanced": [
        {"name": "ArXiv_Electromagnetics_MW", "url": f"https://export.arxiv.org/api/query?search_query=electromagnetics+microwave+propagation+antenna+field&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Wave_Propagation", "url": f"https://export.arxiv.org/api/query?search_query=wave+propagation+scattering+diffraction+medium&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Quantum_Mechanics", "url": f"https://export.arxiv.org/api/query?search_query=quantum+mechanics+wavefunction+measurement+superposition&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Statistical_Mechanics", "url": f"https://export.arxiv.org/api/query?search_query=statistical+mechanics+entropy+thermodynamics+Boltzmann&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_General_Relativity", "url": f"https://export.arxiv.org/api/query?search_query=general+relativity+spacetime+curvature+Einstein&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Field_Theory", "url": f"https://export.arxiv.org/api/query?search_query=quantum+field+theory+standard+model+gauge&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Plasma_Physics", "url": f"https://export.arxiv.org/api/query?search_query=plasma+physics+fusion+electromagnetic+discharge&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Condensed_Matter", "url": f"https://export.arxiv.org/api/query?search_query=cat:cond-mat&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cosmology", "url": f"https://export.arxiv.org/api/query?search_query=cat:astro-ph.CO&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Applied_Physics", "url": f"https://export.arxiv.org/api/query?search_query=cat:physics.app-ph&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── QUANTUM ADVANCED ─────────────────────────────────────────
    "quantum_advanced": [
        {"name": "ArXiv_Quantum_Radar", "url": f"https://export.arxiv.org/api/query?search_query=quantum+radar+illumination+entanglement+SNR&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Quantum_Sensing", "url": f"https://export.arxiv.org/api/query?search_query=quantum+sensing+metrology+precision+measurement&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Post_Quantum", "url": f"https://export.arxiv.org/api/query?search_query=post+quantum+cryptography+NIST+lattice+ML-DSA&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Quantum_Computing", "url": f"https://export.arxiv.org/api/query?search_query=quantum+computing+qubit+gate+algorithm&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Quantum_Communication", "url": f"https://export.arxiv.org/api/query?search_query=quantum+communication+QKD+entanglement+teleportation&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Quantum_Error_Correction", "url": f"https://export.arxiv.org/api/query?search_query=quantum+error+correction+fault+tolerant+surface+code&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Quantum_Defense", "url": f"https://export.arxiv.org/api/query?search_query=quantum+technology+defense+military+national+security&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
        {"name": "ArXiv_Quantum_AI", "url": f"https://export.arxiv.org/api/query?search_query=quantum+machine+learning+variational+circuit&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv", "pdf": True},
    ],

    # ── MATHEMATICS ADVANCED ─────────────────────────────────────
    "mathematics_advanced": [
        {"name": "ArXiv_Linear_Algebra", "url": f"https://export.arxiv.org/api/query?search_query=linear+algebra+matrix+eigenvalue+SVD+applications&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Fourier_Analysis", "url": f"https://export.arxiv.org/api/query?search_query=Fourier+analysis+transform+signal+processing+wavelet&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Probability_Stats", "url": f"https://export.arxiv.org/api/query?search_query=cat:math.PR&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Optimization", "url": f"https://export.arxiv.org/api/query?search_query=cat:math.OC&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Number_Theory", "url": f"https://export.arxiv.org/api/query?search_query=cat:math.NT&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Differential_Equations", "url": f"https://export.arxiv.org/api/query?search_query=differential+equations+dynamical+systems+control&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Graph_Theory", "url": f"https://export.arxiv.org/api/query?search_query=graph+theory+network+algorithm+complexity&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Numerical_Methods", "url": f"https://export.arxiv.org/api/query?search_query=numerical+methods+computation+approximation+algorithm&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Information_Theory", "url": f"https://export.arxiv.org/api/query?search_query=information+theory+Shannon+entropy+channel+capacity&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_ML_Mathematics", "url": f"https://export.arxiv.org/api/query?search_query=mathematics+machine+learning+theory+convergence&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Euclid_Elements", "url": "https://www.gutenberg.org/cache/epub/21076/pg21076.txt", "type": "text"},
    ],

    # ── MUSIC ─────────────────────────────────────────────────────
    "music": [
        {"name": "ArXiv_HipHop_Lyricism", "url": f"https://export.arxiv.org/api/query?search_query=hip+hop+lyricism+flow+rhyme+multisyllabic&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Music_Theory", "url": f"https://export.arxiv.org/api/query?search_query=music+theory+harmony+chord+progression+composition&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Beat_Production", "url": f"https://export.arxiv.org/api/query?search_query=music+production+beat+sampling+drum+machine&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rap_Culture", "url": f"https://export.arxiv.org/api/query?search_query=hip+hop+culture+African+American+music+history&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rhyme_Meter", "url": f"https://export.arxiv.org/api/query?search_query=rhyme+scheme+meter+verse+poetry+rap+analysis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Sound_Engineering", "url": f"https://export.arxiv.org/api/query?search_query=audio+engineering+mixing+mastering+acoustics&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Music_Cognition", "url": f"https://export.arxiv.org/api/query?search_query=music+cognition+emotion+brain+perception&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Blues_Jazz_Lineage", "url": f"https://export.arxiv.org/api/query?search_query=blues+jazz+soul+funk+lineage+African+American+music&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Songwriting_Craft", "url": f"https://export.arxiv.org/api/query?search_query=songwriting+hook+bridge+verse+chorus+craft&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Internal_Rhyme", "url": f"https://export.arxiv.org/api/query?search_query=internal+rhyme+alliteration+assonance+poetry+rap&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── GARDENING ─────────────────────────────────────────────────
    "gardening": [
        {"name": "Henderson_Gardening", "url": "https://www.gutenberg.org/cache/epub/43500/pg43500.txt", "type": "text"},
        {"name": "ArXiv_Soil_Science", "url": f"https://export.arxiv.org/api/query?search_query=soil+science+composition+organic+matter+amendment&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Companion_Planting", "url": f"https://export.arxiv.org/api/query?search_query=companion+planting+intercropping+vegetable+garden&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Permaculture", "url": f"https://export.arxiv.org/api/query?search_query=permaculture+sustainable+food+systems+design&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Raised_Bed", "url": f"https://export.arxiv.org/api/query?search_query=raised+bed+gardening+soil+yield+vegetable&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Composting", "url": f"https://export.arxiv.org/api/query?search_query=composting+soil+amendment+organic+decomposition&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Pest_Management", "url": f"https://export.arxiv.org/api/query?search_query=integrated+pest+management+organic+garden&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Medicinal_Herbs", "url": f"https://export.arxiv.org/api/query?search_query=medicinal+herbs+phytochemistry+therapeutic+garden&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Native_Plants_SE", "url": f"https://export.arxiv.org/api/query?search_query=native+plants+southeastern+United+States+ecology&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Water_Management", "url": f"https://export.arxiv.org/api/query?search_query=irrigation+water+management+garden+drip+system&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Alabama_Gardening", "url": f"https://export.arxiv.org/api/query?search_query=Alabama+Southeast+garden+climate+USDA+zone+7+8&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Seed_Saving", "url": f"https://export.arxiv.org/api/query?search_query=seed+saving+heirloom+varieties+preservation&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── NISABA SOUL / NISA DOCS ───────────────────────────────────
    "nisaba_soul": [
        {"name": "ArXiv_AI_Alignment", "url": f"https://export.arxiv.org/api/query?search_query=AI+alignment+values+safety+beneficial+AGI&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_AI_Personality", "url": f"https://export.arxiv.org/api/query?search_query=AI+personality+character+identity+language+model&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_LLM_Memory", "url": f"https://export.arxiv.org/api/query?search_query=LLM+memory+retrieval+augmented+generation+RAG&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Sumerian_History", "url": f"https://export.arxiv.org/api/query?search_query=Sumerian+civilization+cuneiform+writing+Nisaba&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_AI_Trust", "url": f"https://export.arxiv.org/api/query?search_query=AI+trust+human+machine+relationship+collaboration&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Conversational_AI", "url": f"https://export.arxiv.org/api/query?search_query=conversational+AI+dialogue+system+persona+design&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Explainable_AI", "url": f"https://export.arxiv.org/api/query?search_query=explainable+AI+XAI+interpretability+transparency&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── SOCIAL DYNAMICS ───────────────────────────────────────────
    "social_dynamics": [
        {"name": "ArXiv_Persuasion", "url": f"https://export.arxiv.org/api/query?search_query=persuasion+influence+psychology+Cialdini+compliance&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Negotiation", "url": f"https://export.arxiv.org/api/query?search_query=negotiation+strategy+psychology+conflict+resolution&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Emotional_Intelligence", "url": f"https://export.arxiv.org/api/query?search_query=emotional+intelligence+empathy+social+awareness&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Leadership", "url": f"https://export.arxiv.org/api/query?search_query=leadership+psychology+organizational+behavior&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rhetoric", "url": f"https://export.arxiv.org/api/query?search_query=rhetoric+argumentation+persuasive+communication&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Power_Dynamics", "url": f"https://export.arxiv.org/api/query?search_query=power+dynamics+social+hierarchy+influence+status&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Nonverbal_Communication", "url": f"https://export.arxiv.org/api/query?search_query=nonverbal+communication+body+language+microexpression&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Grief_Bereavement", "url": f"https://export.arxiv.org/api/query?search_query=grief+bereavement+loss+coping+psychology&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Veteran_Reintegration", "url": f"https://export.arxiv.org/api/query?search_query=veteran+military+reintegration+transition+civilian&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cultural_Intelligence", "url": f"https://export.arxiv.org/api/query?search_query=cultural+intelligence+cross+cultural+communication&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── HEALTH ────────────────────────────────────────────────────
    "health": [
        {"name": "Gray_Anatomy", "url": "https://www.gutenberg.org/cache/epub/39722/pg39722.txt", "type": "text"},
        {"name": "ArXiv_Nutrition_Science", "url": f"https://export.arxiv.org/api/query?search_query=nutrition+science+macronutrients+micronutrients+health&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Exercise_Science", "url": f"https://export.arxiv.org/api/query?search_query=exercise+science+strength+training+physiology+performance&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Sleep_Science", "url": f"https://export.arxiv.org/api/query?search_query=sleep+science+circadian+rhythm+recovery+cognition&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_PTSD_Treatment", "url": f"https://export.arxiv.org/api/query?search_query=PTSD+treatment+veterans+trauma+therapy&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Longevity", "url": f"https://export.arxiv.org/api/query?search_query=longevity+aging+healthspan+lifestyle+intervention&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Gut_Microbiome", "url": f"https://export.arxiv.org/api/query?search_query=gut+microbiome+health+nutrition+brain+gut+axis&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Stress_Resilience", "url": f"https://export.arxiv.org/api/query?search_query=stress+resilience+cortisol+nervous+system+military&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Mental_Performance", "url": f"https://export.arxiv.org/api/query?search_query=mental+performance+focus+cognitive+enhancement+nootropics&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cardiovascular", "url": f"https://export.arxiv.org/api/query?search_query=cardiovascular+health+heart+fitness+VO2+max&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── CREATIVE WRITING ─────────────────────────────────────────
    "creative_writing": [
        {"name": "Poe_Tales", "url": "https://www.gutenberg.org/cache/epub/2147/pg2147.txt", "type": "text"},
        {"name": "Lovecraft_Cthulhu", "url": "https://www.gutenberg.org/cache/epub/68595/pg68595.txt", "type": "text"},
        {"name": "Stoker_Dracula", "url": "https://www.gutenberg.org/cache/epub/345/pg345.txt", "type": "text"},
        {"name": "Shelley_Frankenstein", "url": "https://www.gutenberg.org/cache/epub/84/pg84.txt", "type": "text"},
        {"name": "Doyle_Sherlock_Holmes", "url": "https://www.gutenberg.org/cache/epub/1661/pg1661.txt", "type": "text"},
        {"name": "Strunk_White_Style", "url": "https://www.gutenberg.org/cache/epub/37134/pg37134.txt", "type": "text"},
        {"name": "Aristotle_Poetics", "url": "https://www.gutenberg.org/cache/epub/1974/pg1974.txt", "type": "text"},
        {"name": "ArXiv_Narrative_Structure", "url": f"https://export.arxiv.org/api/query?search_query=narrative+structure+fiction+story+arc+Campbell&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Character_Development", "url": f"https://export.arxiv.org/api/query?search_query=character+development+fiction+protagonist+arc+motivation&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Supernatural_Horror", "url": f"https://export.arxiv.org/api/query?search_query=supernatural+horror+gothic+fiction+paranormal+narrative&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Dialogue_Craft", "url": f"https://export.arxiv.org/api/query?search_query=dialogue+writing+fiction+voice+subtext+craft&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Publishing", "url": f"https://export.arxiv.org/api/query?search_query=publishing+industry+literary+agent+manuscript+query&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Genre_Fiction", "url": f"https://export.arxiv.org/api/query?search_query=genre+fiction+thriller+mystery+romance+market&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Prose_Style", "url": f"https://export.arxiv.org/api/query?search_query=prose+style+literary+fiction+voice+technique&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_World_Building", "url": f"https://export.arxiv.org/api/query?search_query=world+building+speculative+fiction+mythology+lore&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── HISTORY ──────────────────────────────────────────────────
    "history": [
        {"name": "US_Constitution", "url": "https://www.gutenberg.org/cache/epub/5/pg5.txt", "type": "text"},
        {"name": "Declaration_Independence", "url": "https://www.gutenberg.org/cache/epub/1/pg1.txt", "type": "text"},
        {"name": "Sun_Tzu_Art_of_War", "url": "https://www.gutenberg.org/cache/epub/132/pg132.txt", "type": "text"},
        {"name": "Machiavelli_Prince", "url": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt", "type": "text"},
        {"name": "Caesar_Gallic_Wars", "url": "https://www.gutenberg.org/cache/epub/10657/pg10657.txt", "type": "text"},
        {"name": "Herodotus_Histories", "url": "https://www.gutenberg.org/cache/epub/2707/pg2707.txt", "type": "text"},
        {"name": "Thucydides_Peloponnesian_War", "url": "https://www.gutenberg.org/cache/epub/7142/pg7142.txt", "type": "text"},
        {"name": "Clausewitz_On_War", "url": "https://www.gutenberg.org/cache/epub/1946/pg1946.txt", "type": "text"},
        {"name": "ArXiv_Military_Strategy", "url": f"https://export.arxiv.org/api/query?search_query=military+strategy+doctrine+warfare+history&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Afghan_Iraq_Wars", "url": f"https://export.arxiv.org/api/query?search_query=Afghanistan+Iraq+war+counterinsurgency+COIN+veteran&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cold_War", "url": f"https://export.arxiv.org/api/query?search_query=Cold+War+nuclear+deterrence+intelligence+CIA&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_American_History", "url": f"https://export.arxiv.org/api/query?search_query=American+history+civil+rights+constitution+democracy&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── TOOLS (SECURITY) ─────────────────────────────────────────
    "tools": [
        {"name": "Nmap_Reference", "url": "https://raw.githubusercontent.com/nmap/nmap/master/docs/nmap.usage.txt", "type": "text"},
        {"name": "Metasploit_README", "url": "https://raw.githubusercontent.com/rapid7/metasploit-framework/master/README.md", "type": "text"},
        {"name": "SQLMap_Docs", "url": "https://raw.githubusercontent.com/sqlmapproject/sqlmap/master/README.md", "type": "text"},
        {"name": "Aircrack_Docs", "url": "https://raw.githubusercontent.com/aircrack-ng/aircrack-ng/master/README.md", "type": "text"},
        {"name": "John_Ripper", "url": "https://raw.githubusercontent.com/openwall/john/bleeding-jumbo/doc/README", "type": "text"},
        {"name": "Hashcat_Docs", "url": "https://raw.githubusercontent.com/hashcat/hashcat/master/README.md", "type": "text"},
        {"name": "Hydra_Docs", "url": "https://raw.githubusercontent.com/vanhauser-thc/thc-hydra/master/README.md", "type": "text"},
        {"name": "Nikto_Docs", "url": "https://raw.githubusercontent.com/sullo/nikto/master/README.md", "type": "text"},
        {"name": "Gobuster_Docs", "url": "https://raw.githubusercontent.com/OJ/gobuster/master/README.md", "type": "text"},
        {"name": "Ffuf_Docs", "url": "https://raw.githubusercontent.com/ffuf/ffuf/master/README.md", "type": "text"},
        {"name": "Impacket_Docs", "url": "https://raw.githubusercontent.com/fortra/impacket/master/README.md", "type": "text"},
        {"name": "Scapy_Docs", "url": "https://raw.githubusercontent.com/secdev/scapy/master/README.rst", "type": "text"},
        {"name": "Wireshark_README", "url": "https://raw.githubusercontent.com/wireshark/wireshark/master/README.md", "type": "text"},
        {"name": "Burp_Suite_README", "url": "https://raw.githubusercontent.com/PortSwigger/burp-extensions-montoya-api/main/README.md", "type": "text"},
        {"name": "SecLists_README", "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/README.md", "type": "text"},
        {"name": "PayloadsAllTheThings", "url": "https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master/README.md", "type": "text"},
        {"name": "PWNDBG_README", "url": "https://raw.githubusercontent.com/pwndbg/pwndbg/dev/README.md", "type": "text"},
        {"name": "Sigma_README", "url": "https://raw.githubusercontent.com/SigmaHQ/sigma/master/README.md", "type": "text"},
        {"name": "ArXiv_Pentesting_Automation", "url": f"https://export.arxiv.org/api/query?search_query=penetration+testing+automation+tools+methodology&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Exploit_Dev", "url": f"https://export.arxiv.org/api/query?search_query=exploit+development+buffer+overflow+ROP+shellcode&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Wireless_Attacks", "url": f"https://export.arxiv.org/api/query?search_query=wireless+attack+WiFi+Bluetooth+RF+security&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── RESUME / CAREER ───────────────────────────────────────────
    "resume_career": [
        {"name": "ArXiv_AI_Security_Jobs", "url": f"https://export.arxiv.org/api/query?search_query=AI+security+career+skills+workforce+hiring&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Defense_Contractor_Careers", "url": f"https://export.arxiv.org/api/query?search_query=defense+contractor+Leidos+SAIC+Booz+Allen+careers&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Veteran_Tech_Transition", "url": f"https://export.arxiv.org/api/query?search_query=veteran+technology+career+transition+military+civilian&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Technical_Interview", "url": f"https://export.arxiv.org/api/query?search_query=technical+interview+software+engineering+security+hiring&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Portfolio_Building", "url": f"https://export.arxiv.org/api/query?search_query=technical+portfolio+github+projects+showcase+hiring&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Salary_Negotiation", "url": f"https://export.arxiv.org/api/query?search_query=salary+negotiation+compensation+technology+career&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Security_Clearance_Career", "url": f"https://export.arxiv.org/api/query?search_query=security+clearance+career+cleared+professional+DoD&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── POETRY ───────────────────────────────────────────────────
    "poetry": [
        {"name": "Rumi_Masnavi", "url": "https://www.gutenberg.org/files/57438/57438-0.txt", "type": "text"},
        {"name": "Whitman_Leaves_of_Grass", "url": "https://www.gutenberg.org/files/1322/1322-0.txt", "type": "text"},
        {"name": "Dickinson_Poems", "url": "https://www.gutenberg.org/files/12242/12242-0.txt", "type": "text"},
        {"name": "Shakespeare_Sonnets", "url": "https://www.gutenberg.org/files/1041/1041-0.txt", "type": "text"},
        {"name": "Gibran_Prophet", "url": "https://www.gutenberg.org/files/58585/58585-0.txt", "type": "text"},
        {"name": "Dante_Divine_Comedy", "url": "https://www.gutenberg.org/files/8800/8800-0.txt", "type": "text"},
        {"name": "Blake_Songs", "url": "https://www.gutenberg.org/cache/epub/574/pg574.txt", "type": "text"},
        {"name": "Keats_Poems", "url": "https://www.gutenberg.org/cache/epub/2490/pg2490.txt", "type": "text"},
        {"name": "Shakespeare_Hamlet", "url": "https://www.gutenberg.org/cache/epub/1524/pg1524.txt", "type": "text"},
        {"name": "Shakespeare_Macbeth", "url": "https://www.gutenberg.org/cache/epub/1533/pg1533.txt", "type": "text"},
        {"name": "Frost_Poems", "url": "https://www.gutenberg.org/cache/epub/59824/pg59824.txt", "type": "text"},
        {"name": "Eliot_Wasteland", "url": "https://www.gutenberg.org/cache/epub/1321/pg1321.txt", "type": "text"},
        {"name": "Langston_Hughes_Analysis", "url": f"https://export.arxiv.org/api/query?search_query=Langston+Hughes+Harlem+Renaissance+poetry+analysis&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Hip_Hop_Poetry", "url": f"https://export.arxiv.org/api/query?search_query=hip+hop+as+poetry+spoken+word+artistic+analysis&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],

    # ── GENERAL ──────────────────────────────────────────────────
    "general": [
        {"name": "ArXiv_General_AI", "url": f"https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_LLM_Survey", "url": f"https://export.arxiv.org/api/query?search_query=large+language+model+survey+capabilities&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Robotics", "url": f"https://export.arxiv.org/api/query?search_query=cat:cs.RO&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Future_Tech", "url": f"https://export.arxiv.org/api/query?search_query=emerging+technology+future+society+impact&max_results={ARXIV_RESULTS}&sortBy=submittedDate", "type": "arxiv"},
    ],
}

# ─── SCRAPING FUNCTIONS ───────────────────────────────────────────
def load_state():
    if os.path.exists(SCRAPER_STATE):
        with open(SCRAPER_STATE) as f:
            return json.load(f)
    return {"scraped": {}}

def save_state(state):
    with open(SCRAPER_STATE, "w") as f:
        json.dump(state, f, indent=2)

def url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:8]

def save_document(domain, name, content, url):
    domain_path = os.path.join(SSD_BASE, domain)
    os.makedirs(domain_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{name}_{timestamp}.txt"
    filepath = os.path.join(domain_path, filename)
    with open(filepath, "w", encoding="utf-8", errors="ignore") as f:
        f.write(f"Source: {url}\nScraped: {datetime.now().isoformat()}\n{'='*60}\n\n{content}")
    size_kb = len(content) // 1024
    print(f"    Saved: {filename} ({size_kb}KB)")
    return filepath

def scrape_text(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip (done): {source['name']}")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Knowledge-Bot/2.0"}, timeout=30)
        r.raise_for_status()
        save_document(domain, source["name"], r.text[:MAX_CONTENT], url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print(f"    RATE LIMITED: {source['name']} — wait 5 min then resume")
        else:
            print(f"    HTTP Error {e.response.status_code}: {source['name']}")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

def scrape_arxiv(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip (done): {source['name']}")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Knowledge-Bot/2.0"}, timeout=45)
        r.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        content = f"ArXiv Papers: {source['name']}\nQuery: {url}\nPapers: {len(entries)}\n\n"
        pdf_urls = []
        for entry in entries:
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            authors = entry.findall("atom:author", ns)
            published = entry.find("atom:published", ns)
            links = entry.findall("atom:link", ns)
            if title is not None and summary is not None:
                author_names = [a.find("atom:name", ns).text for a in authors[:3] if a.find("atom:name", ns) is not None]
                pub_date = published.text[:10] if published is not None else ""
                content += f"Title: {title.text.strip()}\n"
                content += f"Authors: {', '.join(author_names)}\n"
                content += f"Published: {pub_date}\n"
                content += f"Abstract: {summary.text.strip()[:800]}\n\n"
                # Collect PDF links for priority domains
                if source.get("pdf") and domain in PDF_PRIORITY_DOMAINS:
                    for link in links:
                        if link.get("type") == "application/pdf":
                            pdf_urls.append((title.text.strip()[:60], link.get("href")))
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat(), "count": len(entries)}
        print(f"    {len(entries)} abstracts")
        # Fetch top 3 PDFs for priority domains
        if pdf_urls and source.get("pdf"):
            for i, (title, pdf_url) in enumerate(pdf_urls[:3]):
                time.sleep(DELAY)
                fetch_arxiv_pdf(domain, source["name"], title, pdf_url, i, state)
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print(f"    RATE LIMITED — wait 5 min then resume from this domain")
        else:
            print(f"    HTTP Error {e.response.status_code}: {source['name']}")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

def fetch_arxiv_pdf(domain, source_name, title, pdf_url, idx, state):
    uid = url_hash(pdf_url)
    if uid in state["scraped"]:
        return
    try:
        r = requests.get(pdf_url, headers={"User-Agent": "NISA-Knowledge-Bot/2.0"}, timeout=60, stream=True)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
            tmp = f.name
        # Try pdftotext first, fall back to strings
        result = subprocess.run(["pdftotext", tmp, "-"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and len(result.stdout) > 500:
            text = result.stdout[:MAX_CONTENT]
            clean_name = f"{source_name}_FULLTEXT_{idx}_{title[:40].replace(' ','_').replace('/','')}"
            save_document(domain, clean_name, text, pdf_url)
            state["scraped"][uid] = {"name": clean_name, "ts": datetime.now().isoformat(), "type": "pdf_fulltext"}
            print(f"    PDF full-text: {title[:50]}...")
        os.unlink(tmp)
    except subprocess.TimeoutExpired:
        print(f"    PDF timeout: {title[:40]}")
        try: os.unlink(tmp)
        except: pass
    except Exception as e:
        print(f"    PDF error: {title[:40]}: {e}")
        try: os.unlink(tmp)
        except: pass

def scrape_nvd(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip (done): {source['name']}")
        return
    try:
        headers = {"User-Agent": "NISA-Knowledge-Bot/2.0"}
        nvd_key = os.environ.get("NVD_API_KEY", "")
        if nvd_key:
            headers["apiKey"] = nvd_key
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        vulns = data.get("vulnerabilities", [])
        content = f"NIST NVD CVE Database\nSource: {url}\n\n"
        for v in vulns:
            cve = v.get("cve", {})
            cid = cve.get("id", "")
            desc = next((d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"), "")
            metrics = cve.get("metrics", {})
            cvss31 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
            cvss30 = metrics.get("cvssMetricV30", [{}])[0].get("cvssData", {})
            cvss = cvss31 if cvss31 else cvss30
            refs = [r.get("url","") for r in cve.get("references", [])[:3]]
            content += f"CVE: {cid}\n"
            content += f"Severity: {cvss.get('baseSeverity','N/A')} | Score: {cvss.get('baseScore','N/A')}\n"
            content += f"Vector: {cvss.get('vectorString','N/A')}\n"
            content += f"Description: {desc[:400]}\n"
            if refs:
                content += f"References: {' | '.join(refs[:2])}\n"
            content += "\n"
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat(), "count": len(vulns)}
        print(f"    {len(vulns)} CVEs")
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print(f"    NVD RATE LIMITED — wait 30 sec (or get free API key at nvd.nist.gov)")
        else:
            print(f"    HTTP Error {e.response.status_code}: {source['name']}")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

def scrape_mitre(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip (done): {source['name']}")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Knowledge-Bot/2.0"}, timeout=90)
        r.raise_for_status()
        data = r.json()
        techniques = [o for o in data.get("objects", []) if o.get("type") == "attack-pattern"]
        content = f"MITRE ATT&CK - {source['name']}\nTotal techniques: {len(techniques)}\n\n"
        for t in techniques[:200]:
            phases = [k.get("phase_name","") for k in t.get("kill_chain_phases", [])]
            tid = next((er.get("external_id","") for er in t.get("external_references",[]) if er.get("source_name")=="mitre-attack"), "")
            content += f"ID: {tid} | Name: {t.get('name','')}\n"
            content += f"Tactics: {', '.join(phases)}\n"
            content += f"Description: {t.get('description','')[:600]}\n\n"
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat(), "count": len(techniques)}
        print(f"    {len(techniques)} ATT&CK techniques")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

# ─── MAIN ─────────────────────────────────────────────────────────
def run_scraper(domains=None, force=False):
    print("=" * 60)
    print("  NISA Knowledge Scraper v2.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  ArXiv results per query: {ARXIV_RESULTS}")
    print(f"  PDF full-text enabled for: {PDF_PRIORITY_DOMAINS}")
    print("=" * 60)

    state = load_state()
    if force:
        state["scraped"] = {}
        print("Force mode: clearing state\n")

    dispatch = {
        "text": scrape_text,
        "arxiv": scrape_arxiv,
        "nvd": scrape_nvd,
        "mitre": scrape_mitre,
        "dtic": scrape_text,
        "nasa": scrape_text,
        "pubmed_search": scrape_text,
        "pdf": scrape_text,
    }

    target_domains = domains or list(SOURCES.keys())
    total_sources = sum(len(SOURCES[d]) for d in target_domains if d in SOURCES)
    done = 0

    for domain in target_domains:
        if domain not in SOURCES:
            print(f"Unknown domain: {domain}")
            continue
        print(f"\n[{domain.upper()}] ({len(SOURCES[domain])} sources)")
        for source in SOURCES[domain]:
            done += 1
            print(f"  [{done}/{total_sources}] {source['name']}")
            fn = dispatch.get(source["type"], scrape_text)
            fn(source, domain, state)
            time.sleep(DELAY)
        save_state(state)
        print(f"  State saved. Total scraped: {len(state['scraped'])}")

    save_state(state)
    print(f"\n{'='*60}")
    print(f"  COMPLETE. {len(state['scraped'])} sources total.")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    domains = [a for a in sys.argv[1:] if not a.startswith("--")] or None
    run_scraper(domains=domains, force=force)
