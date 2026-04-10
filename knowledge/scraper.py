#!/usr/bin/env python3.11
"""
NISA Knowledge Web Scraper v3.0
Deep domain coverage - multiple sub-queries per topic, 200 results each.
Goal: Nisaba as subject matter expert across all 33+ domains.
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
DELAY = 2
AR = 200  # ArXiv results per query
MAX_CONTENT = 80000
PDF_PRIORITY_DOMAINS = {"radar_ew", "radar_ew_deep", "security", "quantum_advanced", "physics_advanced", "combat_medicine"}

def A(name, query, pdf=False):
    return {"name": name, "url": f"https://export.arxiv.org/api/query?search_query={query.replace(' ','+')}&max_results={AR}&sortBy=submittedDate", "type": "arxiv", "pdf": pdf}

def T(name, url):
    return {"name": name, "url": url, "type": "text"}

def NVD(name, url):
    return {"name": name, "url": url, "type": "nvd"}

def MITRE(name, url):
    return {"name": name, "url": url, "type": "mitre"}

SOURCES = {

    # ── MATHEMATICS ───────────────────────────────────────────────
    "mathematics": [
        # Numerical Analysis
        A("Num_Analysis_Algorithms", "numerical analysis algorithms approximation computation"),
        A("Num_Matrix_Inversion", "matrix inversion decomposition numerical linear algebra"),
        A("Num_Integration_Methods", "numerical integration quadrature Gaussian methods"),
        A("Num_Root_Finding", "root finding Newton Raphson bisection numerical methods"),
        A("Num_Interpolation", "interpolation spline polynomial approximation numerical"),
        # Differential Equations
        A("ODE_Theory", "ordinary differential equations solutions existence uniqueness"),
        A("PDE_Methods", "partial differential equations boundary value problems finite element"),
        A("Fluid_Dynamics_Math", "fluid dynamics Navier Stokes mathematical modeling equations"),
        A("Population_Dynamics", "population dynamics mathematical biology differential equations"),
        A("Chaos_Dynamical", "chaos theory dynamical systems bifurcation attractor"),
        # Mathematical Modeling
        A("Math_Modeling_Pandemic", "mathematical modeling epidemic pandemic SIR SEIR"),
        A("Math_Climate_Models", "climate mathematical modeling simulation differential equations"),
        A("Math_Finance_Models", "mathematical finance stochastic differential equations Black Scholes"),
        A("Math_Physics_Models", "mathematical physics modeling quantum classical mechanics"),
        A("Agent_Based_Models", "agent based modeling simulation complex systems"),
        # Optimization
        A("Optimization_Theory", "optimization theory convex linear programming algorithms"),
        A("Gradient_Descent", "gradient descent stochastic optimization machine learning convergence"),
        A("Integer_Programming", "integer programming combinatorial optimization NP hard"),
        A("Multi_Objective_Opt", "multi objective optimization Pareto front evolutionary"),
        A("Logistics_Optimization", "logistics supply chain optimization operations research"),
        # Probability and Statistics
        A("Probability_Theory", "probability theory measure theoretic foundations"),
        A("Statistical_Inference", "statistical inference hypothesis testing confidence intervals"),
        A("Bayesian_Statistics", "Bayesian statistics inference posterior prior"),
        A("Stochastic_Processes", "stochastic processes Markov chain Brownian motion"),
        A("Risk_Analysis_Stats", "risk analysis statistics actuarial quality control"),
        # Core Mathematics
        A("Linear_Algebra_Deep", "linear algebra eigenvalue eigenvector SVD matrix applications"),
        A("Fourier_Analysis", "Fourier analysis transform signal wavelet applications"),
        A("Graph_Theory", "graph theory network algorithms combinatorics"),
        A("Information_Theory", "information theory Shannon entropy channel capacity"),
        A("Number_Theory", "cat:math.NT"),
        A("Abstract_Algebra", "cat:math.RA"),
        A("Topology_Deep", "cat:math.AT"),
        A("Real_Analysis", "real analysis measure theory Lebesgue integration"),
        A("Complex_Analysis", "complex analysis holomorphic functions Riemann"),
        T("Euclid_Elements", "https://www.gutenberg.org/cache/epub/21076/pg21076.txt"),
    ],

    # ── PHYSICS ───────────────────────────────────────────────────
    "physics_advanced": [
        # Electromagnetism
        A("EM_Maxwell_Equations", "Maxwell equations electromagnetic fields waves propagation", True),
        A("EM_Antenna_Theory", "antenna theory radiation pattern electromagnetic design", True),
        A("EM_Microwave_Engineering", "microwave engineering waveguide transmission line RF", True),
        A("EM_Radar_Propagation", "radar wave propagation atmosphere refraction scattering", True),
        A("EM_Plasma_Physics", "plasma physics electromagnetics ionosphere propagation", True),
        # Quantum Mechanics
        A("QM_Foundations", "quantum mechanics wavefunction Schrodinger measurement interpretation", True),
        A("QM_Entanglement", "quantum entanglement Bell inequality nonlocality EPR", True),
        A("QM_Applications", "quantum mechanics applications semiconductors lasers materials", True),
        A("QFT_Standard_Model", "quantum field theory standard model gauge symmetry", True),
        A("QM_Many_Body", "many body quantum mechanics condensed matter correlated", True),
        # Classical Mechanics
        A("Classical_Lagrangian", "Lagrangian Hamiltonian mechanics canonical transformation"),
        A("Classical_Rigid_Body", "rigid body dynamics rotation inertia mechanics"),
        A("Classical_Chaos", "classical chaos Lyapunov exponent sensitive dependence"),
        # Relativity
        A("Special_Relativity", "special relativity Lorentz transformation spacetime invariance"),
        A("General_Relativity", "general relativity curvature Einstein field equations"),
        A("Gravitational_Waves", "gravitational waves LIGO detection binary merger"),
        # Statistical Physics
        A("Stat_Mech_Entropy", "statistical mechanics entropy thermodynamics Boltzmann"),
        A("Phase_Transitions", "phase transitions critical phenomena universality renormalization"),
        A("Condensed_Matter", "cat:cond-mat"),
        # Applied Physics
        A("Applied_Physics_Sensors", "cat:physics.app-ph"),
        A("Optics_Photonics", "optics photonics laser fiber imaging systems"),
        A("Nuclear_Physics", "cat:nucl-th"),
        A("Astrophysics", "cat:astro-ph"),
        T("Feynman_Lectures", "https://archive.org/stream/feynmanlectures01feyn/feynmanlectures01feyn_djvu.txt"),
    ],

    # ── QUANTUM ADVANCED ─────────────────────────────────────────
    "quantum_advanced": [
        A("Quantum_Computing_Algorithms", "quantum algorithm Grover Shor speedup complexity", True),
        A("Quantum_Error_Correction", "quantum error correction fault tolerant surface code", True),
        A("Quantum_Hardware", "quantum hardware qubit superconducting ion trap photonic", True),
        A("Post_Quantum_Crypto", "post quantum cryptography NIST lattice CRYSTALS ML-DSA", True),
        A("QKD_Protocols", "quantum key distribution BB84 E91 security proof", True),
        A("Quantum_Sensing", "quantum sensing metrology precision measurement Heisenberg", True),
        A("Quantum_Radar", "quantum radar illumination entanglement target detection", True),
        A("Quantum_Communication", "quantum communication teleportation repeater network", True),
        A("Quantum_AI_ML", "quantum machine learning variational circuit optimization", True),
        A("Quantum_Simulation", "quantum simulation many body Hamiltonian chemistry", True),
        A("Quantum_Cryptanalysis", "quantum cryptanalysis Shor algorithm RSA ECC breaking", True),
        A("Quantum_Defense", "quantum technology defense military national security applications", True),
        A("Quantum_Supremacy", "quantum supremacy advantage computational complexity experiment", True),
        A("Topological_Quantum", "topological quantum computing anyons fault tolerant", True),
    ],

    # ── RADAR / EW ────────────────────────────────────────────────
    "radar_ew": [
        A("Radar_Waveform_Design", "radar waveform design ambiguity function LFM optimization", True),
        A("LPI_Radar_Deep", "LPI radar low probability intercept waveform design", True),
        A("Phased_Array_AESA", "phased array AESA digital beamforming adaptive", True),
        A("SAR_ISAR_Imaging", "SAR ISAR synthetic aperture radar imaging processing", True),
        A("EW_Jamming_ECM", "electronic warfare jamming ECM DRFM deceptive", True),
        A("Radar_ML_Detection", "radar machine learning target detection classification", True),
        A("FMCW_Automotive", "FMCW radar automotive pedestrian detection 77GHz", True),
        A("Pulse_Compression", "pulse compression chirp Barker matched filter sidelobe", True),
        A("Doppler_MTI_MTD", "Doppler processing MTI MTD moving target indicator", True),
        A("Radar_Cross_Section", "radar cross section RCS stealth reduction signature", True),
        A("ESM_ELINT_Systems", "electronic support measures ELINT signal intercept emitter", True),
        A("Cognitive_Adaptive_Radar", "cognitive radar adaptive waveform spectrum environment", True),
        A("MIMO_Radar", "MIMO radar multiple input output diversity waveform", True),
        A("Radar_Clutter_CFAR", "radar clutter suppression CFAR constant false alarm", True),
        A("EW_Defense_ECCM", "electronic countermeasure counter ECCM protection", True),
        A("EOB_Emitter_ID", "electronic order of battle emitter identification classification", True),
        A("Polyphase_Codes", "polyphase codes Frank P1 P2 P4 radar waveform LPI", True),
        A("Frequency_Hopping_LPI", "frequency hopping spread spectrum LPI radar intercept", True),
        A("Noise_Radar_Random", "noise radar random waveform LPI covert detection", True),
        A("Quantum_Radar_Apps", "quantum radar illumination signal noise ratio detection", True),
        A("SDR_GNU_Radio", "software defined radio SDR GNU Radio waveform implementation"),
        A("Radar_Deep_Learning", "radar deep learning neural network classification recognition"),
        A("Spectrum_Sensing", "spectrum sensing cognitive radio interference detection"),
        A("Over_Horizon_Radar", "over horizon radar OTH HF skywave detection"),
        {"name": "NASA_Radar", "url": "https://ntrs.nasa.gov/api/citations/search?q=radar&rows=30", "type": "nasa"},
    ],

    # ── SECURITY ─────────────────────────────────────────────────
    "security": [
        NVD("NVD_CRITICAL", "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100&cvssV3Severity=CRITICAL"),
        NVD("NVD_HIGH", "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100&cvssV3Severity=HIGH"),
        MITRE("MITRE_Enterprise", "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"),
        MITRE("MITRE_Mobile", "https://raw.githubusercontent.com/mitre/cti/master/mobile-attack/mobile-attack.json"),
        MITRE("MITRE_ICS", "https://raw.githubusercontent.com/mitre/cti/master/ics-attack/ics-attack.json"),
        A("Malware_Detection_ML", "malware detection machine learning neural network"),
        A("APT_Campaign_Analysis", "advanced persistent threat APT campaign attribution"),
        A("Ransomware_Analysis", "ransomware attack defense recovery analysis"),
        A("Intrusion_Detection", "intrusion detection system anomaly network"),
        A("Vulnerability_Research", "vulnerability assessment exploit CVE disclosure"),
        A("Zero_Trust_Architecture", "zero trust security architecture NIST implementation"),
        A("AI_Adversarial_Security", "adversarial machine learning security attack defense"),
        A("Network_Threat_Detection", "network threat detection SOC analytics"),
        A("Phishing_Social_Eng", "phishing social engineering spear BEC"),
        A("Cryptography_PQC", "cryptography encryption post quantum NIST"),
        A("SIEM_Detection_Rules", "SIEM detection rules sigma analytics log"),
        A("Threat_Intelligence", "cyber threat intelligence STIX TAXII sharing"),
        A("Cloud_Security", "cloud security misconfiguration AWS Azure GCP"),
        A("ICS_SCADA_Security", "ICS SCADA industrial control security"),
        A("Supply_Chain_Attack", "supply chain attack software dependency"),
        A("Active_Directory_Attack", "Active Directory Kerberos attack lateral"),
        A("Web_App_Security", "web application security injection XSS CSRF"),
        A("Digital_Forensics_IR", "digital forensics incident response DFIR"),
        A("Red_Team_Pentest", "red team penetration testing offensive security"),
        T("GTFOBins", "https://raw.githubusercontent.com/GTFOBins/GTFOBins.github.io/master/README.md"),
        T("PayloadsAllTheThings", "https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master/README.md"),
        T("PortSwigger_SQLi", "https://portswigger.net/web-security/sql-injection"),
        T("PortSwigger_XSS", "https://portswigger.net/web-security/cross-site-scripting"),
        T("PortSwigger_SSRF", "https://portswigger.net/web-security/ssrf"),
        T("PortSwigger_XXE", "https://portswigger.net/web-security/xxe"),
        T("PortSwigger_Auth", "https://portswigger.net/web-security/authentication"),
        T("Sigma_Rules", "https://raw.githubusercontent.com/SigmaHQ/sigma/master/README.md"),
        T("Impacket", "https://raw.githubusercontent.com/fortra/impacket/master/README.md"),
    ],

    # ── SECURITY HISTORICAL ───────────────────────────────────────
    "security_historical": [
        A("Stuxnet_Full", "Stuxnet worm ICS SCADA Iran nuclear centrifuge"),
        A("SolarWinds_Sunburst", "SolarWinds Sunburst supply chain attack analysis"),
        A("WannaCry_EternalBlue", "WannaCry ransomware EternalBlue NHS analysis"),
        A("NotPetya_Wiper", "NotPetya cyberattack Ukraine Maersk wiper malware"),
        A("Colonial_Pipeline", "Colonial Pipeline ransomware DarkSide critical infrastructure"),
        A("Mirai_IoT_Botnet", "Mirai botnet IoT DDoS Dyn DNS attack"),
        A("Equifax_Breach", "Equifax data breach Apache Struts PII exposure"),
        A("Target_POS_Breach", "Target breach POS malware retail credit card"),
        A("Log4Shell_Log4j", "Log4Shell Log4j CVE-2021-44228 analysis exploitation"),
        A("MOVEit_Cl0p", "MOVEit Cl0p ransomware file transfer breach"),
        A("Volt_Typhoon_China", "Volt Typhoon China critical infrastructure living land"),
        A("Midnight_Blizzard", "Midnight Blizzard APT29 Microsoft email espionage"),
        A("APT28_Fancy_Bear", "APT28 Fancy Bear GRU Russia election interference"),
        A("Lazarus_DPRK", "Lazarus DPRK North Korea cryptocurrency theft"),
        A("Nation_State_Cyber", "nation state cyberattack attribution espionage"),
        A("Cyber_Warfare_History", "cyber warfare history Estonia Georgia Ukraine"),
        A("Zero_Day_Market", "zero day exploit market Pwn2Own Zerodium history"),
        A("NSA_TAO_Tools", "NSA TAO hacking tools Shadow Brokers leak"),
        A("APT41_China_Dual", "APT41 China espionage financial crime dual mission"),
        A("FIN7_Carbanak", "FIN7 Carbanak financial crime point of sale"),
    ],

    # ── SECURITY OFFENSIVE ────────────────────────────────────────
    "security_offensive": [
        A("Exploit_Dev_Buffer", "exploit development buffer overflow ROP chain shellcode"),
        A("Living_Off_Land", "living off the land LOLBAS fileless malware"),
        A("C2_Framework_Design", "command control C2 framework Cobalt Strike Sliver detection"),
        A("Kerberoasting_PTH", "Kerberoasting Pass Hash Golden Ticket AD attack"),
        A("Lateral_Movement_SMB", "lateral movement SMB WMI PsExec detection"),
        A("Privilege_Escalation", "privilege escalation Windows Linux technique UAC bypass"),
        A("Persistence_Mechanisms", "persistence registry scheduled task backdoor implant"),
        A("Credential_Dumping", "credential dumping Mimikatz LSASS NTLM hash extraction"),
        A("Defense_Evasion_AV", "defense evasion AV bypass obfuscation AMSI EDR"),
        A("Wireless_Attack_WiFi", "wireless attack WiFi WPA2 evil twin PMKID"),
        A("Social_Engineering_Adv", "social engineering vishing pretexting BEC wire fraud"),
        A("Physical_Pentest", "physical security access control RFID badge cloning"),
        A("AI_LLM_Attack", "AI LLM prompt injection jailbreak model extraction"),
        A("BloodHound_AD_Paths", "BloodHound attack path AD graph analysis"),
        A("DNS_Exfiltration", "data exfiltration DNS tunneling covert channel"),
        A("Web_App_Exploitation", "web application exploitation chain bypass WAF"),
        A("Mobile_App_Attack", "mobile application security Android iOS pentest"),
        A("Cloud_Pentest", "cloud penetration testing AWS Azure misconfiguration IAM"),
        A("Hardware_Hacking", "hardware hacking JTAG UART firmware extraction"),
        A("Malware_Development", "malware development evasion shellcode loader technique"),
    ],

    # ── SECURITY DEFENSIVE ────────────────────────────────────────
    "security_defensive": [
        A("Detection_Engineering", "detection engineering SIEM rule sigma alert"),
        A("Threat_Hunting", "threat hunting hypothesis driven proactive detection"),
        A("SOC_Operations", "SOC security operations center analyst playbook triage"),
        A("Incident_Response", "incident response containment eradication recovery"),
        A("EDR_XDR_Telemetry", "EDR XDR endpoint detection response telemetry"),
        A("Blue_Team_Hardening", "blue team defensive hardening baselines"),
        A("Honeypot_Deception", "honeypot deception technology canary token"),
        A("Vulnerability_Management", "vulnerability management patch prioritization CVSS"),
        A("Security_Architecture", "security architecture design defense in depth"),
        A("Purple_Team_Exercise", "purple team red blue collaboration ATT&CK"),
        A("Threat_Modeling", "threat modeling STRIDE PASTA architecture review"),
        A("Security_Automation", "security automation SOAR orchestration response"),
        A("MITRE_Coverage", "MITRE ATT&CK detection coverage gap analysis"),
        A("Deception_Technology", "deception technology adversary engagement honeypot"),
        A("Zero_Trust_Impl", "zero trust implementation microsegmentation identity"),
        T("Sigma_Readme", "https://raw.githubusercontent.com/SigmaHQ/sigma/master/README.md"),
    ],

    # ── DEFENSE COMPLIANCE ────────────────────────────────────────
    "defense_compliance": [
        A("NIST_800_171_Deep", "NIST 800-171 CUI defense contractor compliance"),
        A("CMMC_Framework", "CMMC cybersecurity maturity model certification DoD"),
        A("FedRAMP_Authorization", "FedRAMP federal cloud authorization ATO process"),
        A("RMF_Process", "Risk Management Framework RMF ATO authorization NIST"),
        A("FISMA_Compliance", "FISMA federal information security management compliance"),
        A("IL_Classification", "DoD impact level IL2 IL4 IL5 cloud classification"),
        A("Security_Clearance", "security clearance SF-86 adjudication background investigation"),
        A("PII_Privacy_Law", "PII privacy data protection GDPR CCPA compliance"),
        A("SOC2_ISO27001", "SOC2 ISO 27001 security audit compliance framework"),
        A("PQC_Compliance", "post quantum cryptography NIST FIPS 204 migration compliance", True),
        A("AI_Governance_NIST", "AI governance risk management framework NIST AI RMF"),
        A("Insider_Threat_Program", "insider threat program detection monitoring"),
        A("ITAR_EAR_Export", "ITAR EAR export control technology defense"),
        A("CUI_Handling", "controlled unclassified information CUI handling marking"),
        A("Continuous_Monitoring", "continuous monitoring ISCM cybersecurity posture"),
    ],

    # ── BUSINESS CONTRACTS ────────────────────────────────────────
    "business_contracts": [
        A("Federal_Contracting", "federal government contracting procurement defense"),
        A("Proposal_Writing_RFP", "government proposal writing RFP technical volume"),
        A("IDIQ_GWAC_Vehicles", "IDIQ GWAC indefinite delivery contract government"),
        A("Defense_Acquisition", "defense acquisition DoD program management"),
        A("SBIR_STTR_Programs", "SBIR STTR small business innovation research DoD"),
        A("SOW_PWS_Writing", "statement of work performance work specification"),
        A("Contract_Negotiation", "contract negotiation terms conditions government"),
        A("BD_Capture_Mgmt", "business development capture management pipeline"),
        A("Technical_White_Papers", "technical white paper capability brief proposal"),
        A("Startup_Commercialization", "startup commercialization innovation technology transfer"),
        A("IP_Patent_Strategy", "intellectual property patent strategy technology"),
        A("Project_Mgmt_DoD", "project management agile earned value DoD"),
        A("Pricing_Cost_Analysis", "government contract pricing cost analysis strategy"),
        A("Small_Business_DoD", "small business DoD contracting 8a HUBZone SDVOSB"),
        A("Past_Performance", "past performance contractor evaluation CPARS PPIRS"),
        T("FAR_Overview", "https://raw.githubusercontent.com/GSA/GSA-Acquisition-FAR/main/README.md"),
    ],

    # ── LINUX COMMANDS ────────────────────────────────────────────
    "linux_commands": [
        T("GNU_Bash_Manual", "https://www.gnu.org/software/bash/manual/bash.html"),
        T("GTFOBins_Full", "https://raw.githubusercontent.com/GTFOBins/GTFOBins.github.io/master/README.md"),
        T("TLDR_grep", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/grep.md"),
        T("TLDR_awk", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/awk.md"),
        T("TLDR_sed", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/sed.md"),
        T("TLDR_find", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/find.md"),
        T("TLDR_ssh", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/ssh.md"),
        T("TLDR_nmap", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/nmap.md"),
        T("TLDR_curl", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/curl.md"),
        T("TLDR_tcpdump", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/tcpdump.md"),
        T("TLDR_ps", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/ps.md"),
        T("TLDR_netstat", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/netstat.md"),
        T("TLDR_git", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/git.md"),
        T("TLDR_docker", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/docker.md"),
        T("TLDR_python", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/python.md"),
        T("TLDR_tar", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/tar.md"),
        T("TLDR_rsync", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/rsync.md"),
        T("TLDR_vim", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/vim.md"),
        T("TLDR_tmux", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/tmux.md"),
        T("TLDR_chmod", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/chmod.md"),
        T("TLDR_cron", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/cron.md"),
        T("TLDR_systemctl", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/linux/systemctl.md"),
        T("TLDR_ip", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/linux/ip.md"),
        T("TLDR_iptables", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/linux/iptables.md"),
        T("TLDR_strace", "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/linux/strace.md"),
        A("Bash_Scripting", "bash shell scripting automation linux command"),
        A("Linux_Admin_Deep", "Linux system administration security hardening"),
        A("Network_Commands", "network diagnostic commands tcpdump netstat ss linux"),
        A("Forensics_Commands", "forensics command line dd strings file analysis linux"),
        A("Git_Workflow", "git version control workflow branching collaboration"),
        A("Docker_Operations", "Docker container operations management security"),
        A("Python_Automation", "Python automation scripting DevOps command line"),
        A("Regex_Text_Processing", "regular expressions grep sed awk text processing"),
        A("Systemd_Service_Mgmt", "systemd service management unit files Linux"),
        A("Package_Management", "Linux package manager apt yum brew pip conda"),
    ],

    # ── COMBAT MEDICINE ───────────────────────────────────────────
    "combat_medicine": [
        T("Gray_Anatomy", "https://www.gutenberg.org/cache/epub/39722/pg39722.txt"),
        T("US_Army_Survival", "https://www.gutenberg.org/files/17007/17007-0.txt"),
        A("TCCC_Protocol", "tactical combat casualty care TCCC prehospital military", True),
        A("Hemorrhage_Control", "hemorrhage control tourniquet hemostatic agent junctional", True),
        A("Airway_Field_Mgmt", "airway management intubation cricothyrotomy field", True),
        A("MARCH_PAWS", "MARCH PAWS protocol combat trauma military medicine", True),
        A("Blast_TBI_Injury", "blast injury IED traumatic brain injury military", True),
        A("Combat_Medic_68W", "combat medic 68W field medicine Afghanistan Iraq", True),
        A("Wound_Ballistics", "wound ballistics gunshot injury penetrating trauma treatment", True),
        A("MEDEVAC_9Line", "MEDEVAC medical evacuation 9-line casualty transport", True),
        A("PTSD_Combat_Trauma", "PTSD veterans combat trauma treatment VA", True),
        A("TBI_Cognitive", "traumatic brain injury TBI veterans blast cognitive", True),
        A("Damage_Control_Surgery", "damage control surgery trauma resuscitation REBOA", True),
        A("Military_Pharmacology", "military pharmacology ketamine tranexamic acid morphine pain", True),
        A("Point_of_Care_Austere", "point of care diagnostics field hospital austere environment", True),
        A("Tactical_Medicine_EMS", "tactical medicine TEMS law enforcement emergency", True),
        A("Mass_Casualty", "mass casualty incident MASCAL triage START JumpSTART", True),
        A("Hypovolemic_Shock", "hypovolemic shock resuscitation fluid management trauma", True),
        A("Battlefield_Anesthesia", "battlefield anesthesia ketamine sedation field surgery", True),
        A("Combat_Stress_Reaction", "combat stress reaction acute battle fatigue resilience", True),
        A("Extremity_Trauma", "extremity trauma amputation wound care military", True),
    ],

    # ── HEALTH ────────────────────────────────────────────────────
    "health": [
        # Mental Health
        A("Mental_Health_PTSD", "PTSD treatment veterans trauma therapy CBT EMDR"),
        A("Anxiety_Depression", "anxiety depression treatment therapy medication evidence"),
        A("Mindfulness_Clinical", "mindfulness based stress reduction MBSR clinical outcomes"),
        A("Resilience_Psychology", "resilience psychological hardiness stress coping"),
        A("Positive_Psychology", "positive psychology flourishing wellbeing strengths"),
        A("Trauma_Healing", "trauma healing somatic therapy nervous system regulation"),
        A("Sleep_Mental_Health", "sleep mental health insomnia CBT-I circadian"),
        # Fitness and Performance
        A("Strength_Training_Science", "strength training hypertrophy muscle physiology program"),
        A("Endurance_Performance", "endurance performance VO2 max lactate threshold training"),
        A("HIIT_Conditioning", "HIIT high intensity interval training conditioning metabolic"),
        A("Mobility_Flexibility", "mobility flexibility joint health movement quality"),
        A("Athletic_Recovery", "athletic recovery sleep nutrition HRV adaptation"),
        A("Military_Fitness", "military fitness physical readiness training program"),
        A("Periodization_Programming", "periodization programming training cycles peaking"),
        # Yoga
        A("Yoga_Science", "yoga science physiology benefits clinical research"),
        A("Yoga_Mental_Health", "yoga mental health anxiety depression mindfulness practice"),
        A("Yoga_Styles_Practice", "yoga styles Hatha Vinyasa Ashtanga Yin practice"),
        A("Breathwork_Pranayama", "pranayama breathing yoga respiratory nervous system"),
        # Nutrition
        A("Nutrition_Performance", "nutrition athletic performance macronutrients timing"),
        A("Anti_Inflammatory_Diet", "anti-inflammatory diet chronic disease prevention"),
        A("Gut_Microbiome", "gut microbiome health nutrition brain axis"),
        A("Fasting_Metabolic", "intermittent fasting metabolic health longevity"),
        A("Supplements_Evidence", "supplements evidence based performance health"),
        # Meditation / Transcendental
        A("Transcendental_Meditation", "transcendental meditation TM mantra brainwave EEG"),
        A("Meditation_Neuroscience", "meditation neuroscience brain plasticity cortex"),
        A("Guided_Meditation_Research", "guided meditation visualization relaxation script outcomes"),
        A("Vipassana_Mindfulness", "Vipassana insight meditation technique retreat outcomes"),
        A("Loving_Kindness_Metta", "loving kindness metta meditation compassion research"),
        # Wellness
        A("Longevity_Science", "longevity aging healthspan lifestyle intervention"),
        A("Stress_Physiology", "stress physiology cortisol HPA axis nervous system"),
        A("Cold_Exposure_Sauna", "cold exposure Wim Hof sauna heat therapy health"),
        A("Cardiovascular_Health", "cardiovascular health heart fitness prevention"),
        A("Hormonal_Health", "hormonal health testosterone cortisol optimization"),
        # Clinical (lighter touch)
        A("Anatomy_Systems", "human anatomy physiology organ systems function"),
        A("Disease_Mechanisms", "disease pathophysiology mechanisms chronic illness"),
        A("Pharmacology_Basics", "pharmacology drug mechanisms interactions clinical"),
    ],

    # ── SPIRITUALITY ADVANCED ─────────────────────────────────────
    "spiritual_advanced": [
        # Sacred Texts - Primary Sources
        T("Bible_KJV", "https://www.gutenberg.org/cache/epub/10/pg10.txt"),
        T("Quran_English", "https://www.gutenberg.org/cache/epub/2800/pg2800.txt"),
        T("Bhagavad_Gita", "https://www.gutenberg.org/cache/epub/2388/pg2388.txt"),
        T("Upanishads", "https://www.gutenberg.org/cache/epub/68171/pg68171.txt"),
        T("Dhammapada", "https://www.gutenberg.org/cache/epub/2017/pg2017.txt"),
        T("Tao_Te_Ching", "https://www.gutenberg.org/cache/epub/216/pg216.txt"),
        T("Tibetan_Book_Dead", "https://www.gutenberg.org/cache/epub/55060/pg55060.txt"),
        T("Egyptian_Book_Dead", "https://www.gutenberg.org/cache/epub/55060/pg55060.txt"),
        T("Rig_Veda", "https://www.gutenberg.org/cache/epub/16295/pg16295.txt"),
        T("Mahabharata", "https://www.gutenberg.org/cache/epub/15474/pg15474.txt"),
        T("Ramayana", "https://www.gutenberg.org/cache/epub/24869/pg24869.txt"),
        T("Book_of_Job", "https://www.gutenberg.org/cache/epub/83/pg83.txt"),
        T("Gospel_Thomas", "https://www.gutenberg.org/cache/epub/18824/pg18824.txt"),
        T("Zoroastrian_Avesta", "https://www.gutenberg.org/cache/epub/2081/pg2081.txt"),
        T("CIA_Gateway_Experience", "https://www.cia.gov/readingroom/document/cia-rdp96-00788r001700210016-5"),
        # Ancient Mythology
        T("Greek_Mythology_Bulfinch", "https://www.gutenberg.org/cache/epub/4928/pg4928.txt"),
        T("Norse_Mythology_Prose_Edda", "https://www.gutenberg.org/cache/epub/25946/pg25946.txt"),
        T("Egyptian_Myths_Legends", "https://www.gutenberg.org/cache/epub/9411/pg9411.txt"),
        T("Sumerian_Mythology", "https://www.gutenberg.org/cache/epub/10767/pg10767.txt"),
        T("Celtic_Mythology", "https://www.gutenberg.org/cache/epub/14707/pg14707.txt"),
        # Academic Research
        A("Consciousness_Science_NCC", "consciousness science neural correlates awareness qualia"),
        A("Gateway_Monroe_Hemi", "Monroe Institute hemi-sync binaural beats consciousness"),
        A("OBE_Sleep_Paralysis", "out of body experience sleep paralysis autoscopy"),
        A("Remote_Viewing_Stargate", "remote viewing Stargate psi CIA parapsychology"),
        A("Lucid_Dream_WILD_MILD", "lucid dreaming WILD MILD technique REM induction"),
        A("NDE_Consciousness", "near death experience NDE consciousness afterlife cardiac"),
        A("Psychedelics_Mystical", "psilocybin DMT mystical experience ego dissolution"),
        A("Shamanism_Indigenous", "shamanism indigenous ceremony vision quest healing"),
        A("UAP_Scientific", "UAP UFO unexplained aerial phenomena scientific analysis"),
        A("Quantum_Consciousness", "quantum consciousness Penrose Orch OR microtubule"),
        A("Dogon_People_Sirius", "Dogon people Sirius star Mali West Africa cosmology"),
        A("Ancient_Egypt_Religion", "ancient Egypt religion Osiris Ra cosmology afterlife"),
        A("African_Traditional_Religion", "African traditional religion Yoruba Vodou Akan ancestors"),
        A("Aboriginal_Dreamtime", "Aboriginal Australian dreamtime spirituality tradition"),
        A("Native_American_Spiritual", "Native American spirituality ceremony medicine wheel"),
        A("Rastafari_Religion", "Rastafari religion Ethiopia Haile Selassie Jamaica"),
        A("Kabbalah_Jewish_Mysticism", "Kabbalah Jewish mysticism Zohar Sefirot tree of life"),
        A("Sufism_Islamic_Mysticism", "Sufism Islamic mysticism Rumi whirling dervish"),
        A("Zen_Buddhism_Practice", "Zen Buddhism koan meditation Soto Rinzai practice"),
        A("Tibetan_Buddhism_Bardo", "Tibetan Buddhism Bardo Thodol reincarnation consciousness"),
        A("Hindu_Advaita_Vedanta", "Hinduism Advaita Vedanta non-dual consciousness Brahman"),
        A("Christianity_Mysticism", "Christian mysticism contemplative prayer desert fathers"),
        A("Dead_Sea_Scrolls", "Dead Sea Scrolls Qumran Essenes biblical manuscripts"),
        A("Gnostic_Texts", "Gnostic texts Nag Hammadi Gospel Thomas Sophia"),
        A("Breathwork_Holotropic", "Stanislav Grof holotropic breathwork non-ordinary states"),
        A("Meditation_Brainwave", "meditation brainwave alpha theta delta gamma EEG"),
    ],

    # ── MUSIC ─────────────────────────────────────────────────────
    "music": [
        # Hip Hop Craft
        A("HipHop_Flow_Rhyme", "hip hop flow rhyme scheme multisyllabic internal"),
        A("HipHop_Lyricism_Craft", "hip hop lyricism wordplay metaphor punchline technique"),
        A("Rap_Delivery_Voice", "rap vocal delivery cadence breath control performance"),
        A("HipHop_Battle_Freestyle", "hip hop battle rap freestyle cipher improvisation"),
        A("HipHop_Storytelling", "hip hop storytelling narrative concept album"),
        A("Beat_Production_Sampling", "music production beat making sampling drum machine"),
        A("Mixing_Mastering", "mixing mastering audio engineering EQ compression"),
        A("Sound_Design_Synthesis", "sound design synthesis oscillator filter modular"),
        # Music Theory Deep
        A("Harmony_Counterpoint", "harmony counterpoint voice leading chord progression"),
        A("Modal_Theory", "modal theory modes Dorian Phrygian Lydian jazz"),
        A("Rhythm_Meter_Deep", "rhythm meter polyrhythm syncopation groove feel"),
        A("Orchestration_Arrangement", "orchestration arrangement instrumentation score"),
        A("Music_Composition", "music composition form structure sonata rondo"),
        A("Jazz_Theory_Improv", "jazz theory improvisation bebop chord substitution"),
        A("Music_Cognition_Emotion", "music cognition emotion brain perception memory"),
        A("Psychoacoustics", "psychoacoustics auditory perception loudness pitch timbre"),
        # Music History
        A("African_American_Music", "African American music history blues gospel soul funk"),
        A("Jazz_History_Deep", "jazz history New Orleans bebop hard bop free fusion"),
        A("Blues_Origins", "blues origins Delta Chicago electric history"),
        A("Soul_RnB_History", "soul RnB Motown Philadelphia history"),
        A("HipHop_History_Culture", "hip hop history culture Bronx Kool Herc evolution"),
        A("Rap_Generations", "rap generations golden age gangsta conscious trap evolution"),
        A("Electronic_Music_History", "electronic music history techno house EDM"),
        A("Rock_Classical_Influence", "rock classical music influence Beatles Led Zeppelin"),
        A("Music_African_Roots", "music African roots drumming polyrhythm diaspora"),
        A("Songwriting_Craft", "songwriting hook bridge verse chorus craft"),
        A("Music_Business", "music business industry streaming royalties contracts"),
    ],

    # ── PHILOSOPHY ────────────────────────────────────────────────
    "philosophy": [
        T("Plato_Republic", "https://www.gutenberg.org/files/1497/1497-0.txt"),
        T("Aristotle_Ethics", "https://www.gutenberg.org/files/8438/8438-0.txt"),
        T("Marcus_Aurelius", "https://www.gutenberg.org/cache/epub/2680/pg2680.txt"),
        T("Seneca_Letters", "https://www.gutenberg.org/cache/epub/1464/pg1464.txt"),
        T("Epictetus_Discourses", "https://www.gutenberg.org/cache/epub/4135/pg4135.txt"),
        T("Nietzsche_Zarathustra", "https://www.gutenberg.org/files/1998/1998-0.txt"),
        T("Nietzsche_Beyond_Good", "https://www.gutenberg.org/cache/epub/4363/pg4363.txt"),
        T("Descartes_Meditations", "https://www.gutenberg.org/files/59/59-0.txt"),
        T("Kant_Critique", "https://www.gutenberg.org/cache/epub/4280/pg4280.txt"),
        T("Hume_Enquiry", "https://www.gutenberg.org/cache/epub/9662/pg9662.txt"),
        T("Spinoza_Ethics", "https://www.gutenberg.org/cache/epub/3800/pg3800.txt"),
        T("Schopenhauer_World", "https://www.gutenberg.org/cache/epub/38427/pg38427.txt"),
        T("Plato_Dialogues", "https://www.gutenberg.org/cache/epub/1656/pg1656.txt"),
        T("Aristotle_Politics", "https://www.gutenberg.org/cache/epub/6762/pg6762.txt"),
        A("Stoicism_Practice", "Stoicism virtue reason practice Marcus Aurelius"),
        A("Existentialism_Deep", "existentialism Sartre Camus Heidegger being nothingness"),
        A("Philosophy_Mind", "philosophy of mind consciousness qualia hard problem"),
        A("Ethics_Moral_Theory", "ethics moral theory deontology consequentialism virtue"),
        A("Epistemology", "epistemology knowledge belief justification"),
        A("Political_Philosophy", "political philosophy justice Rawls liberty democracy"),
        A("Philosophy_Science", "philosophy of science Kuhn paradigm falsification Popper"),
        A("Eastern_Philosophy", "Eastern philosophy Taoism Confucianism Buddhism Zen"),
        A("African_Philosophy", "African philosophy Ubuntu Dogon cosmology tradition"),
        A("Indigenous_Philosophy", "indigenous philosophy Native American cosmology knowledge"),
        A("AI_Ethics_Philosophy", "AI ethics moral philosophy autonomous systems"),
        A("Free_Will_Determinism", "free will determinism compatibilism moral responsibility"),
        A("Metaphysics_Reality", "metaphysics ontology reality substance causation"),
        A("Philosophy_Language", "philosophy of language meaning reference truth"),
    ],

    # ── PSYCHOLOGY ────────────────────────────────────────────────
    "psychology": [
        A("Cognitive_Psychology", "cognitive psychology memory attention perception learning"),
        A("Social_Psychology", "social psychology conformity obedience influence Milgram"),
        A("Developmental_Psychology", "developmental psychology lifespan Erikson Piaget"),
        A("Personality_Theory", "personality theory Big Five MBTI traits assessment"),
        A("Motivation_Theory", "motivation theory self determination Maslow needs"),
        A("Behavioral_Psychology", "behavioral psychology conditioning reinforcement Skinner"),
        A("Neuropsychology", "neuropsychology brain behavior prefrontal executive"),
        A("Trauma_Psychology", "trauma psychology PTSD complex developmental ACE"),
        A("Positive_Psychology_Deep", "positive psychology flourishing Seligman PERMA"),
        A("Grief_Loss_Models", "grief loss Kubler Ross stages bereavement coping"),
        A("Attachment_Theory", "attachment theory Bowlby secure avoidant anxious"),
        A("Leadership_Psychology", "leadership psychology organizational behavior management"),
        A("Body_Language_Science", "body language nonverbal communication microexpression"),
        A("Deescalation_Psychology", "de-escalation conflict resolution crisis intervention"),
        A("Cognitive_Bias", "cognitive bias heuristics Kahneman decision making"),
        A("Flow_State", "flow state optimal experience Csikszentmihalyi performance"),
        T("William_James_Psychology", "https://www.gutenberg.org/cache/epub/630/pg630.txt"),
    ],

    # ── SOCIAL DYNAMICS ───────────────────────────────────────────
    "social_dynamics": [
        A("Persuasion_Influence", "persuasion influence psychology Cialdini compliance"),
        A("Negotiation_Strategy", "negotiation strategy psychology BATNA Harvard"),
        A("Emotional_Intelligence", "emotional intelligence empathy social awareness Goleman"),
        A("Rapport_Trust_Building", "rapport building trust interpersonal communication"),
        A("Rhetoric_Argumentation", "rhetoric argumentation persuasive communication Aristotle"),
        A("Power_Dynamics", "power dynamics social hierarchy influence status"),
        A("Nonverbal_Microexpressions", "nonverbal microexpression body language Ekman"),
        A("Cultural_Intelligence", "cultural intelligence cross cultural communication"),
        A("Professional_Networking", "professional networking career relationship building"),
        A("Conflict_Resolution", "conflict resolution mediation restorative justice"),
        A("Group_Dynamics", "group dynamics team cohesion social loafing"),
        A("Charisma_Presence", "charisma executive presence leadership communication"),
        A("Active_Listening", "active listening empathic communication technique"),
        A("Veteran_Reintegration", "veteran military reintegration transition civilian"),
        A("Interpersonal_Skills", "interpersonal skills relationship psychology communication"),
    ],

    # ── HISTORY ───────────────────────────────────────────────────
    "history": [
        T("Sun_Tzu_Art_War", "https://www.gutenberg.org/cache/epub/132/pg132.txt"),
        T("Machiavelli_Prince", "https://www.gutenberg.org/cache/epub/1232/pg1232.txt"),
        T("Caesar_Gallic_Wars", "https://www.gutenberg.org/cache/epub/10657/pg10657.txt"),
        T("Clausewitz_On_War", "https://www.gutenberg.org/cache/epub/1946/pg1946.txt"),
        T("Herodotus_Histories", "https://www.gutenberg.org/cache/epub/2707/pg2707.txt"),
        T("Thucydides", "https://www.gutenberg.org/cache/epub/7142/pg7142.txt"),
        T("US_Constitution", "https://www.gutenberg.org/cache/epub/5/pg5.txt"),
        T("Declaration_Independence", "https://www.gutenberg.org/cache/epub/1/pg1.txt"),
        A("Military_Strategy_History", "military strategy doctrine warfare history"),
        A("Afghanistan_Iraq_COIN", "Afghanistan Iraq war counterinsurgency COIN lessons"),
        A("Cold_War_Intelligence", "Cold War nuclear deterrence intelligence CIA KGB"),
        A("American_Military_History", "American military history Civil War WW2 Korea Vietnam"),
        A("Ancient_Greece_Rome", "ancient Greece Rome empire civilization culture"),
        A("Medieval_History", "medieval history Byzantine Islamic empire crusades"),
        A("African_History_Deep", "African history empire Mali Songhai Egypt civilization"),
        A("Slavery_Civil_Rights", "American slavery civil rights movement history"),
        A("WW2_History", "World War 2 strategy campaigns Holocaust Pacific"),
        A("Cold_War_Deep", "Cold War proxy wars Berlin Wall Cuban Missile Crisis"),
        A("Intelligence_History", "intelligence history espionage OSS CIA history"),
        A("Native_American_History", "Native American history tribes culture resistance"),
    ],

    # ── CREATIVE WRITING ─────────────────────────────────────────
    "creative_writing": [
        T("Poe_Tales", "https://www.gutenberg.org/cache/epub/2147/pg2147.txt"),
        T("Lovecraft_Cthulhu", "https://www.gutenberg.org/cache/epub/68595/pg68595.txt"),
        T("Stoker_Dracula", "https://www.gutenberg.org/cache/epub/345/pg345.txt"),
        T("Shelley_Frankenstein", "https://www.gutenberg.org/cache/epub/84/pg84.txt"),
        T("Doyle_Sherlock", "https://www.gutenberg.org/cache/epub/1661/pg1661.txt"),
        T("Strunk_White", "https://www.gutenberg.org/cache/epub/37134/pg37134.txt"),
        T("Aristotle_Poetics", "https://www.gutenberg.org/cache/epub/1974/pg1974.txt"),
        A("Narrative_Structure", "narrative structure three act hero journey Campbell"),
        A("Character_Development", "character development arc motivation protagonist"),
        A("Supernatural_Horror_Craft", "supernatural horror gothic fiction craft technique"),
        A("Dialogue_Subtext", "dialogue subtext voice character fiction craft"),
        A("Publishing_Industry", "publishing industry literary agent query manuscript"),
        A("Genre_Fiction_Market", "genre fiction thriller mystery romance market"),
        A("Prose_Style_Voice", "prose style literary voice technique fiction"),
        A("World_Building", "world building speculative fiction mythology lore"),
        A("Mystery_Thriller_Craft", "mystery thriller suspense craft plot structure"),
        A("Paranormal_Supernatural", "paranormal supernatural fiction research craft"),
        A("Memoir_Personal_Narrative", "memoir personal narrative creative nonfiction craft"),
        A("Revision_Editing", "revision editing manuscript feedback craft"),
        A("Pacing_Tension", "pacing tension narrative structure suspense fiction"),
    ],

    # ── POETRY ────────────────────────────────────────────────────
    "poetry": [
        T("Rumi_Masnavi", "https://www.gutenberg.org/files/57438/57438-0.txt"),
        T("Whitman_Leaves_Grass", "https://www.gutenberg.org/files/1322/1322-0.txt"),
        T("Dickinson_Poems", "https://www.gutenberg.org/files/12242/12242-0.txt"),
        T("Shakespeare_Sonnets", "https://www.gutenberg.org/files/1041/1041-0.txt"),
        T("Gibran_Prophet", "https://www.gutenberg.org/files/58585/58585-0.txt"),
        T("Dante_Divine_Comedy", "https://www.gutenberg.org/files/8800/8800-0.txt"),
        T("Blake_Songs", "https://www.gutenberg.org/cache/epub/574/pg574.txt"),
        T("Keats_Poems", "https://www.gutenberg.org/cache/epub/2490/pg2490.txt"),
        T("Shakespeare_Hamlet", "https://www.gutenberg.org/cache/epub/1524/pg1524.txt"),
        T("Frost_Poems", "https://www.gutenberg.org/cache/epub/59824/pg59824.txt"),
        A("Langston_Hughes", "Langston Hughes Harlem Renaissance poetry analysis"),
        A("HipHop_as_Poetry", "hip hop poetry spoken word artistic literary analysis"),
        A("African_Poetry", "African poetry oral tradition Yoruba Swahili literature"),
        A("Sufi_Poetry_Rumi", "Sufi poetry Rumi Hafiz Kabir mystical verse"),
        A("Spoken_Word_Slam", "spoken word slam poetry performance technique"),
        A("Poetry_Craft_Form", "poetry craft form meter sonnet free verse technique"),
        A("Indigenous_Poetry", "indigenous poetry Native American oral tradition verse"),
        A("Harlem_Renaissance", "Harlem Renaissance poetry literature cultural movement"),
    ],

    # ── CERTIFICATIONS ────────────────────────────────────────────
    "certifications": [
        # CompTIA
        A("CompTIA_Security_Plus", "CompTIA Security+ exam domains cybersecurity fundamentals"),
        A("CompTIA_Network_Plus", "CompTIA Network+ networking protocols TCP IP exam"),
        A("CompTIA_A_Plus", "CompTIA A+ hardware software troubleshooting exam"),
        A("CompTIA_CySA_Plus", "CompTIA CySA+ cybersecurity analyst threat detection"),
        A("CompTIA_Pentest_Plus", "CompTIA PenTest+ penetration testing methodology exam"),
        A("CompTIA_CASP_Plus", "CompTIA CASP+ advanced security practitioner enterprise"),
        A("CompTIA_Linux_Plus", "CompTIA Linux+ system administration exam"),
        A("CompTIA_Cloud_Plus", "CompTIA Cloud+ cloud infrastructure security"),
        # ISC2
        A("CISSP_Domains", "CISSP domains security management architecture exam"),
        A("CISSP_Access_Control", "CISSP access control authentication identity management"),
        A("CISSP_Cryptography", "CISSP cryptography PKI certificate management"),
        A("CISSP_Network_Security", "CISSP network security architecture firewall VPN"),
        A("ISC2_SSCP", "SSCP systems security certified practitioner ISC2"),
        A("ISC2_CCSP", "CCSP cloud security professional ISC2 certification"),
        A("ISC2_CSSLP", "CSSLP certified secure software lifecycle professional"),
        # ISACA
        A("CISM_Domains", "CISM certified information security manager ISACA domains"),
        A("CISA_Auditing", "CISA certified information systems auditor audit"),
        A("CRISC_Risk", "CRISC risk information systems control ISACA"),
        # EC-Council
        A("CEH_Ethical_Hacking", "CEH certified ethical hacker EC-Council exam"),
        A("CHFI_Forensics", "CHFI computer hacking forensic investigator EC-Council"),
        A("CPENT_Pentest", "CPENT certified penetration testing professional"),
        A("ECSA_Security_Analyst", "ECSA EC-Council security analyst methodology"),
        # GIAC / SANS
        A("GSEC_Security", "GSEC GIAC security essentials certification SANS"),
        A("GPEN_Pentest", "GPEN GIAC penetration tester certification"),
        A("GCIH_Incident_Handler", "GCIH GIAC certified incident handler response"),
        A("GWAPT_Web_App", "GWAPT web application penetration testing GIAC"),
        A("GREM_Malware", "GREM reverse engineering malware GIAC analyst"),
        # Wireless / 5G / 6G
        A("5G_Security_Fundamentals", "5G network security architecture 3GPP standards"),
        A("5G_Red_Team", "5G network red team penetration testing attack"),
        A("6G_Security_Research", "6G network security resilience future wireless"),
        A("Spectrum_Monitoring", "spectrum monitoring security RF signal 5G 6G"),
        A("Wireless_Security_Certs", "wireless security CWSP certified wireless professional"),
        # Cloud and Container
        A("AWS_Security_Cert", "AWS certified security specialty cloud exam"),
        A("Azure_Security_Cert", "Azure security engineer associate certification Microsoft"),
        A("Container_Security_Cert", "container security Docker Kubernetes CKS certification"),
        A("DevSecOps_Cert", "DevSecOps certification secure development pipeline"),
        # Network
        A("CCNA_Networking", "CCNA Cisco networking routing switching certification"),
        A("CCNP_Security", "CCNP security Cisco advanced networking certification"),
        # Access Control and PKI
        A("Access_Control_IAM", "access control identity management IAM RBAC ABAC"),
        A("PKI_Certificate_Mgmt", "PKI public key infrastructure certificate authority TLS"),
        A("Authentication_MFA", "authentication multifactor MFA biometric zero trust"),
        A("Privileged_Access_Mgmt", "privileged access management PAM CyberArk BeyondTrust"),
        # Study Methodology
        A("Certification_Study_Methods", "certification exam study methodology practice test"),
        A("Security_Cert_Roadmap", "cybersecurity certification roadmap career path"),
    ],

    # ── TOOLS ────────────────────────────────────────────────────
    "tools": [
        T("Nmap_Reference", "https://raw.githubusercontent.com/nmap/nmap/master/docs/nmap.usage.txt"),
        T("Metasploit_README", "https://raw.githubusercontent.com/rapid7/metasploit-framework/master/README.md"),
        T("SQLMap_Docs", "https://raw.githubusercontent.com/sqlmapproject/sqlmap/master/README.md"),
        T("Hashcat_Docs", "https://raw.githubusercontent.com/hashcat/hashcat/master/README.md"),
        T("Hydra_Docs", "https://raw.githubusercontent.com/vanhauser-thc/thc-hydra/master/README.md"),
        T("Nikto_Docs", "https://raw.githubusercontent.com/sullo/nikto/master/README.md"),
        T("Gobuster_Docs", "https://raw.githubusercontent.com/OJ/gobuster/master/README.md"),
        T("Impacket_Docs", "https://raw.githubusercontent.com/fortra/impacket/master/README.md"),
        T("SecLists_README", "https://raw.githubusercontent.com/danielmiessler/SecLists/master/README.md"),
        T("OWASP_WSTG", "https://raw.githubusercontent.com/OWASP/wstg/master/document/README.md"),
        A("Pentesting_Tools", "penetration testing tools automation methodology"),
        A("Exploit_Dev_Tools", "exploit development tools GDB pwndbg pwntools"),
        A("Wireless_Security_Tools", "wireless security tools aircrack hashcat WiFi"),
        A("Forensics_Tools", "digital forensics tools Volatility Autopsy FTK"),
        A("OSINT_Tools", "OSINT open source intelligence Maltego Shodan Recon-ng"),
    ],

    # ── NISABA SOUL ───────────────────────────────────────────────
    "nisaba_soul": [
        A("AI_Alignment_Values", "AI alignment values safety beneficial AGI"),
        A("AI_Identity_Persona", "AI personality character identity language model"),
        A("LLM_Memory_RAG", "LLM memory retrieval augmented generation vector"),
        A("Sumerian_Nisaba", "Sumerian civilization Nisaba goddess writing wisdom"),
        A("AI_Human_Trust", "AI trust human machine collaboration relationship"),
        A("Conversational_AI", "conversational AI dialogue persona design"),
        A("Explainable_AI", "explainable AI XAI interpretability transparency"),
        A("AI_Consciousness", "AI consciousness sentience philosophy mind"),
        A("Human_AI_Collab", "human AI collaboration augmentation partnership"),
    ],

    # ── GENERAL ───────────────────────────────────────────────────
    "general": [
        A("General_AI_Survey", "cat:cs.AI"),
        A("LLM_Capabilities", "large language model capabilities survey benchmark"),
        A("Future_Technology", "emerging technology future society impact"),
        A("Interdisciplinary_Research", "interdisciplinary research cross domain innovation"),
    ],

    # ── FINANCES ─────────────────────────────────────────────────
    "finances": [
        # Trading Strategies
        A("Technical_Analysis_Trading", "technical analysis chart patterns candlestick indicators trading"),
        A("Fundamental_Analysis", "fundamental analysis valuation DCF earnings stock"),
        A("Algorithmic_Trading", "algorithmic trading quantitative strategy backtesting"),
        A("Options_Derivatives", "options trading derivatives strategies Greeks risk"),
        A("Day_Trading_Swing", "day trading swing trading momentum strategies"),
        A("Forex_Currency_Trading", "forex currency trading strategy analysis"),
        A("Crypto_Trading_Strategy", "cryptocurrency trading strategy Bitcoin altcoin DeFi"),
        A("Risk_Management_Trading", "risk management position sizing stop loss portfolio"),
        A("Market_Microstructure", "market microstructure order flow liquidity execution"),
        A("Behavioral_Finance", "behavioral finance investor psychology bias market"),
        # Investment
        A("Value_Investing", "value investing Graham Buffett intrinsic value margin safety"),
        A("Growth_Investing", "growth investing momentum factor returns"),
        A("Portfolio_Theory", "modern portfolio theory Markowitz Sharpe ratio diversification"),
        A("ETF_Index_Investing", "ETF index fund passive investing Bogle"),
        A("Real_Estate_Investing", "real estate investing rental REIT cash flow"),
        A("Alternative_Investments", "alternative investments hedge fund private equity venture"),
        A("Dividend_Investing", "dividend investing income yield strategy"),
        # Savings and Wealth Building
        A("Personal_Finance_Deep", "personal finance budgeting savings emergency fund"),
        A("Retirement_Planning", "retirement planning 401k IRA Roth compound interest"),
        A("Tax_Optimization", "tax optimization strategy deductions harvesting"),
        A("Financial_Independence", "financial independence FIRE early retirement savings"),
        A("Wealth_Building_Strategy", "wealth building strategy net worth accumulation"),
        # Macroeconomics
        A("Macroeconomics_Deep", "macroeconomics GDP inflation monetary fiscal policy"),
        A("Federal_Reserve_Policy", "Federal Reserve monetary policy interest rates QE"),
        A("Inflation_Deflation", "inflation deflation CPI purchasing power hedging"),
        A("Economic_Cycles", "economic cycles recession expansion bull bear market"),
        A("Global_Economy_Trends", "global economy trends emerging markets geopolitics"),
        A("Microeconomics", "microeconomics supply demand price elasticity market"),
        A("Behavioral_Economics", "behavioral economics Kahneman Thaler nudge theory"),
        # Current Trends - Multiple Perspectives
        A("AI_Economy_Impact", "artificial intelligence economy jobs productivity disruption"),
        A("Deglobalization_Trends", "deglobalization supply chain reshoring geopolitical risk"),
        A("Energy_Transition_Finance", "energy transition renewable finance ESG investing"),
        A("Digital_Currency_CBDC", "central bank digital currency CBDC Bitcoin gold"),
        A("Debt_Crisis_Analysis", "national debt crisis fiscal sustainability analysis"),
        A("Market_Outlook_2025", "market outlook 2025 2026 equity bonds forecast"),
        A("Geopolitical_Risk_Finance", "geopolitical risk finance markets war sanctions"),
        A("Crypto_Regulation", "cryptocurrency regulation SEC policy institutional adoption"),
    ],

    # ── RESUME / CAREER ───────────────────────────────────────────
    "resume_career": [
        A("AI_Security_Jobs", "AI security career skills workforce demand"),
        A("Defense_Contractor_Jobs", "defense contractor Leidos SAIC Booz Allen careers"),
        A("Veteran_Tech_Transition", "veteran technology career transition military civilian"),
        A("Technical_Interview", "technical interview software security engineering hiring"),
        A("Portfolio_Building", "technical portfolio GitHub projects showcase"),
        A("Salary_Negotiation", "salary negotiation compensation technology career"),
        A("Security_Clearance_Career", "security clearance career cleared professional DoD"),
        A("Networking_Career", "professional networking career advancement strategy"),
        A("Personal_Branding", "personal branding thought leadership LinkedIn career"),
    ],

    # ── GARDENING ────────────────────────────────────────────────
    "gardening": [
        T("Henderson_Gardening", "https://www.gutenberg.org/cache/epub/43500/pg43500.txt"),
        # Zone 7B Specific
        A("Zone7B_Planting_Guide", "USDA zone 7B planting guide frost dates vegetables"),
        A("Zone7B_Alabama", "Alabama zone 7B gardening climate Southeast vegetables"),
        A("Zone7B_Perennials", "zone 7B perennial plants hardy climate Southeast"),
        A("Zone7B_Winter_Garden", "zone 7B winter garden cool season crops frost"),
        A("Southeast_Vegetable_Garden", "Southeast vegetable gardening heat humidity summer"),
        A("Heat_Tolerant_Plants", "heat tolerant plants vegetables Southeast summer"),
        # Edible Gardens
        A("Edible_Landscape_Design", "edible landscape design food garden aesthetics"),
        A("Vegetable_Garden_Planning", "vegetable garden planning layout spacing companion"),
        A("Herb_Garden_Culinary", "herb garden culinary cooking medicinal growing"),
        A("Fruit_Trees_Southeast", "fruit trees Southeast zone 7 apple peach fig"),
        A("Berry_Growing", "berry growing blueberry strawberry blackberry cultivation"),
        A("Root_Vegetables", "root vegetables carrots beets turnips growing"),
        A("Tomato_Pepper_Growing", "tomato pepper eggplant nightshade growing care"),
        A("Leafy_Greens_Season", "leafy greens kale collards lettuce season extension"),
        A("Squash_Melon_Cucumber", "squash melon cucumber vine vegetables growing"),
        # Flowers
        A("Native_Flowers_Southeast", "native flowers Southeast wildflowers pollinator garden"),
        A("Cut_Flower_Garden", "cut flower garden design growing harvest"),
        A("Perennial_Flower_Design", "perennial flower garden design color season bloom"),
        A("Annual_Flowers_Summer", "annual flowers summer heat color bedding plants"),
        A("Bulb_Growing", "bulb growing spring tulip daffodil dahlia seasonal"),
        A("Rose_Growing_Care", "rose growing care pruning disease resistant varieties"),
        A("Pollinator_Garden", "pollinator garden bee butterfly habitat native plants"),
        # Greenhouse
        A("Greenhouse_Building", "greenhouse building construction design materials"),
        A("Greenhouse_Management", "greenhouse management temperature humidity ventilation"),
        A("Season_Extension_Greenhouse", "season extension greenhouse cold frame hoop house"),
        A("Greenhouse_Hydroponics", "greenhouse hydroponics aquaponics growing systems"),
        A("Small_Greenhouse_Home", "small home greenhouse backyard DIY construction"),
        # Plant Care
        A("Plant_Disease_ID", "plant disease identification treatment fungal bacterial"),
        A("Soil_Amendment_Fertility", "soil amendment fertility composting organic matter"),
        A("Watering_Irrigation", "plant watering irrigation drip system schedule"),
        A("Pruning_Techniques", "pruning techniques trees shrubs timing method"),
        A("Transplanting_Propagation", "transplanting propagation cuttings division seed"),
        A("Plant_Nutrient_Deficiency", "plant nutrient deficiency identification treatment"),
        A("Organic_Pest_Control", "organic pest control beneficial insects companion plants"),
        A("Mycorrhizal_Fungi", "mycorrhizal fungi soil biology plant symbiosis"),
        A("Composting_Deep", "composting methods hot cold vermicomposting ratio"),
        A("Raised_Bed_Construction", "raised bed construction materials soil mix depth"),
        A("Seed_Starting_Indoors", "seed starting indoors timing light heat germination"),
        A("Seed_Saving_Heirloom", "seed saving heirloom varieties open pollinated storage"),
        A("Food_Forest_Design", "food forest agroforestry seven layers design"),
        A("Permaculture_Zone7", "permaculture design Southeast zone 7 climate"),
        A("Water_Harvesting", "water harvesting rain barrel swale conservation garden"),
        A("Medicinal_Herb_Growing", "medicinal herbs growing harvesting drying storage"),
    ],

    # ── SURVIVAL ─────────────────────────────────────────────────
    "survival": [
        T("US_Army_Survival", "https://www.gutenberg.org/files/17007/17007-0.txt"),
        T("Scouting_Handbook", "https://www.gutenberg.org/cache/epub/29558/pg29558.txt"),
        A("Wilderness_Survival", "wilderness survival navigation shelter water food"),
        A("Emergency_Preparedness", "emergency preparedness FEMA disaster readiness"),
        A("Navigation_Orientation", "navigation land wilderness compass map terrain"),
        A("Emergency_Medicine_Field", "emergency medicine field trauma first aid"),
        A("Urban_Survival", "urban survival grid down SHTF preparedness"),
        A("Water_Purification", "water purification filtration survival techniques"),
        A("Fire_Starting", "fire starting primitive skills friction bow drill"),
        A("Food_Foraging", "food foraging wild edibles plants identification"),
    ],

    # ── PROGRAMMING ──────────────────────────────────────────────
    "programming": [
        T("Python_Tutorial", "https://docs.python.org/3/tutorial/index.html"),
        T("GNU_Bash", "https://www.gnu.org/software/bash/manual/bash.html"),
        A("Python_Security", "Python security development libraries tools"),
        A("JavaScript_React", "JavaScript React frontend development modern"),
        A("API_Design", "REST API design FastAPI microservices architecture"),
        A("Database_SQL", "database SQL PostgreSQL query optimization"),
        A("ML_Implementation", "machine learning implementation PyTorch TensorFlow"),
        A("Software_Architecture", "software architecture patterns design systems"),
        A("DevOps_CI_CD", "DevOps CI CD deployment automation pipeline"),
        A("Algorithms_DS", "algorithms data structures complexity analysis"),
        A("Cybersecurity_Coding", "cybersecurity coding secure development OWASP"),
        A("Signal_Processing_Code", "MATLAB Python signal processing implementation DSP"),
    ],

    # ── LOGIC / PARADOXES ─────────────────────────────────────────
    "logic_puzzles": [
        A("Logic_Foundations", "formal logic propositional predicate modal foundations"),
        A("Game_Theory_Deep", "game theory Nash equilibrium strategy optimal"),
        A("Paradoxes_Philosophy", "Zeno Liar Russell paradox philosophy logic"),
        A("Fermi_Estimation", "Fermi estimation paradox problem solving"),
        A("Cryptanalysis_Cipher", "cryptanalysis cipher breaking historical"),
        A("Decision_Theory", "decision theory rational choice probability utility"),
        A("Deductive_Reasoning", "deductive reasoning inference logic argumentation"),
        T("Lewis_Carroll_Logic", "https://www.gutenberg.org/cache/epub/28696/pg28696.txt"),
    ],

    # ── WRITING CRAFT ────────────────────────────────────────────
    "writing_craft": [
        T("Strunk_White_Style", "https://www.gutenberg.org/cache/epub/37134/pg37134.txt"),
        T("Aristotle_Poetics_Full", "https://www.gutenberg.org/cache/epub/1974/pg1974.txt"),
        A("Writing_Style_Prose", "writing style prose craft technique voice"),
        A("Technical_Writing", "technical writing documentation engineering report"),
        A("Rhetoric_Persuasion", "rhetoric persuasive writing composition argument"),
        A("Grammar_Linguistics", "grammar linguistics syntax English structure"),
        A("Narrative_Voice", "narrative voice point of view perspective fiction"),
        A("Editing_Revision_Process", "editing revision writing process manuscript"),
        A("Publishing_Query", "publishing industry query letter agent submission"),
        A("Metaphor_Language", "metaphor figurative language cognitive linguistics"),
        A("Academic_Writing", "academic writing research paper structure citation"),
    ],

    # ── TECHNOLOGY DEEP ───────────────────────────────────────────
    "technology": [
        A("AI_ML_Survey", "cat:cs.AI"),
        A("LLM_Architecture", "large language model architecture transformer attention"),
        A("IoT_Security", "IoT internet of things security vulnerability"),
        A("Cloud_Architecture", "cloud architecture AWS Azure GCP design"),
        A("Container_Kubernetes", "Docker Kubernetes container orchestration"),
        A("Hardware_Security", "hardware security side channel CPU architecture"),
        A("5G_Network_Security", "5G network security vulnerability protocol"),
        A("Firmware_Embedded", "firmware embedded systems security analysis"),
        A("Quantum_Computing_Tech", "quantum computing technology qubit hardware"),
        A("Robotics_Autonomy", "cat:cs.RO"),
        A("Windows_Security", "Windows Active Directory security hardening"),
        A("Linux_Kernel_Security", "Linux kernel security privilege escalation"),
        A("macOS_Security", "macOS Apple silicon security vulnerability"),
        A("Mobile_Security", "mobile iOS Android security vulnerability"),
        A("SCADA_ICS_Security", "SCADA ICS industrial control security"),
    ],

    # ── RESEARCH METHODOLOGY ─────────────────────────────────────
    "research": [
        A("Research_Methods", "research methodology scientific method design"),
        A("Technical_Writing_Research", "technical writing scientific paper documentation"),
        A("Data_Analysis_Stats", "data analysis statistical methods research"),
        A("Literature_Review", "systematic literature review methodology"),
        A("Signal_Research_Methods", "signal processing research methods DSP"),
        A("Interdisciplinary_Research", "interdisciplinary research cross domain"),
        A("Patent_Research", "patent writing claims intellectual property"),
        A("Grant_Writing", "grant writing proposal research funding"),
    ],
}

# ─── SCRAPING ENGINE ─────────────────────────────────────────────
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
    ts = datetime.now().strftime("%Y%m%d")
    fname = f"{name}_{ts}.txt"
    fpath = os.path.join(domain_path, fname)
    with open(fpath, "w", encoding="utf-8", errors="ignore") as f:
        f.write(f"Source: {url}\nScraped: {datetime.now().isoformat()}\n{'='*60}\n\n{content}")
    print(f"    Saved: {fname} ({len(content)//1024}KB)")
    return fpath

def scrape_text(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip: {source['name']}")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Knowledge-Bot/3.0"}, timeout=30)
        r.raise_for_status()
        save_document(domain, source["name"], r.text[:MAX_CONTENT], url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
    except requests.HTTPError as e:
        code = e.response.status_code
        if code == 429:
            print(f"    RATE LIMITED: {source['name']} — wait 5 min then resume")
        else:
            print(f"    HTTP {code}: {source['name']}")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

def fetch_pdf(domain, name, title, pdf_url, idx, state):
    uid = url_hash(pdf_url)
    if uid in state["scraped"]:
        return
    tmp = None
    try:
        r = requests.get(pdf_url, headers={"User-Agent": "NISA-Knowledge-Bot/3.0"}, timeout=60, stream=True)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
            tmp = f.name
        result = subprocess.run(["pdftotext", tmp, "-"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and len(result.stdout) > 500:
            clean = f"{name}_PDF{idx}_{title[:40].replace(' ','_').replace('/','')}"
            save_document(domain, clean, result.stdout[:MAX_CONTENT], pdf_url)
            state["scraped"][uid] = {"name": clean, "ts": datetime.now().isoformat(), "type": "pdf"}
            print(f"    PDF: {title[:50]}")
        if tmp:
            os.unlink(tmp)
    except subprocess.TimeoutExpired:
        print(f"    PDF timeout: {title[:40]}")
        if tmp:
            try: os.unlink(tmp)
            except: pass
    except Exception as e:
        print(f"    PDF err: {title[:40]}: {e}")
        if tmp:
            try: os.unlink(tmp)
            except: pass

def scrape_arxiv(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip: {source['name']}")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Knowledge-Bot/3.0"}, timeout=45)
        r.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        content = f"ArXiv: {source['name']}\nQuery: {url}\nPapers: {len(entries)}\n\n"
        pdf_urls = []
        for entry in entries:
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            authors = entry.findall("atom:author", ns)
            published = entry.find("atom:published", ns)
            links = entry.findall("atom:link", ns)
            if title and summary:
                names = [a.find("atom:name", ns).text for a in authors[:3] if a.find("atom:name", ns) is not None]
                pub = published.text[:10] if published is not None else ""
                content += f"Title: {title.text.strip()}\n"
                content += f"Authors: {', '.join(names)}\nPublished: {pub}\n"
                content += f"Abstract: {summary.text.strip()[:800]}\n\n"
                if source.get("pdf") and domain in PDF_PRIORITY_DOMAINS:
                    for lnk in links:
                        if lnk.get("type") == "application/pdf":
                            pdf_urls.append((title.text.strip()[:60], lnk.get("href")))
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat(), "count": len(entries)}
        print(f"    {len(entries)} abstracts")
        if pdf_urls and source.get("pdf"):
            for i, (title, purl) in enumerate(pdf_urls[:3]):
                time.sleep(DELAY)
                fetch_pdf(domain, source["name"], title, purl, i, state)
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print(f"    RATE LIMITED — wait 5 min")
        else:
            print(f"    HTTP {e.response.status_code}: {source['name']}")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

def scrape_nvd(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip: {source['name']}")
        return
    try:
        headers = {"User-Agent": "NISA-Knowledge-Bot/3.0"}
        key = os.environ.get("NVD_API_KEY", "")
        if key:
            headers["apiKey"] = key
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        vulns = r.json().get("vulnerabilities", [])
        content = f"NIST NVD CVE Database\nSource: {url}\n\n"
        for v in vulns:
            cve = v.get("cve", {})
            cid = cve.get("id", "")
            desc = next((d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"), "")
            m = cve.get("metrics", {})
            cvss = m.get("cvssMetricV31", [{}])[0].get("cvssData", {}) or m.get("cvssMetricV30", [{}])[0].get("cvssData", {})
            refs = [x.get("url", "") for x in cve.get("references", [])[:2]]
            content += f"CVE: {cid}\nSeverity: {cvss.get('baseSeverity','N/A')} | Score: {cvss.get('baseScore','N/A')}\n"
            content += f"Vector: {cvss.get('vectorString','N/A')}\nDescription: {desc[:400]}\n"
            if refs:
                content += f"Refs: {' | '.join(refs)}\n"
            content += "\n"
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat(), "count": len(vulns)}
        print(f"    {len(vulns)} CVEs")
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print(f"    NVD RATE LIMITED — wait 30 sec (or get free API key at nvd.nist.gov)")
        else:
            print(f"    HTTP {e.response.status_code}: {source['name']}")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

def scrape_mitre(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"    Skip: {source['name']}")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Knowledge-Bot/3.0"}, timeout=90)
        r.raise_for_status()
        data = r.json()
        techniques = [o for o in data.get("objects", []) if o.get("type") == "attack-pattern"]
        content = f"MITRE ATT&CK - {source['name']}\nTotal: {len(techniques)}\n\n"
        for t in techniques[:200]:
            phases = [k.get("phase_name", "") for k in t.get("kill_chain_phases", [])]
            tid = next((e.get("external_id", "") for e in t.get("external_references", []) if e.get("source_name") == "mitre-attack"), "")
            content += f"ID: {tid} | Name: {t.get('name', '')}\n"
            content += f"Tactics: {', '.join(phases)}\n"
            content += f"Description: {t.get('description', '')[:600]}\n\n"
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat(), "count": len(techniques)}
        print(f"    {len(techniques)} techniques")
    except Exception as e:
        print(f"    Error: {source['name']}: {e}")

def run_scraper(domains=None, force=False):
    print("=" * 60)
    print("  NISA Knowledge Scraper v3.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  ArXiv per query: {AR} | PDF domains: {PDF_PRIORITY_DOMAINS}")
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

    target = domains or list(SOURCES.keys())
    total = sum(len(SOURCES[d]) for d in target if d in SOURCES)
    done = 0

    for domain in target:
        if domain not in SOURCES:
            print(f"Unknown domain: {domain}")
            continue
        sources = SOURCES[domain]
        print(f"\n[{domain.upper()}] ({len(sources)} sources)")
        for source in sources:
            done += 1
            print(f"  [{done}/{total}] {source['name']}")
            fn = dispatch.get(source["type"], scrape_text)
            fn(source, domain, state)
            time.sleep(DELAY)
        save_state(state)
        print(f"  Saved. Total: {len(state['scraped'])}")

    save_state(state)
    print(f"\n{'='*60}")
    print(f"  COMPLETE. {len(state['scraped'])} sources total.")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    domains = [a for a in sys.argv[1:] if not a.startswith("--")] or None
    run_scraper(domains=domains, force=force)
