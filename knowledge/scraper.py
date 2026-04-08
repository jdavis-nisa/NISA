#!/usr/bin/env python3.11
"""
NISA Knowledge Web Scraper
Pulls content from approved sources across all knowledge domains
Saves to SSD knowledge library for GraphRAG ingestion
"""
import os
import time
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path

SSD_BASE = "/Volumes/Share Drive/NISA/knowledge"
SCRAPER_STATE = "/Users/joshuadavis/NISA/knowledge/scraper_state.json"
DELAY = 2  # seconds between requests

SOURCES = {
    "security": [
        {"name": "NIST_NVD_CVE", "url": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=20&cvssV3Severity=CRITICAL", "type": "nvd"},
        {"name": "OWASP_Top10", "url": "https://raw.githubusercontent.com/OWASP/Top10/master/2021/docs/A00_2021_Introduction.md", "type": "text"},
        {"name": "MITRE_ATTACK", "url": "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json", "type": "mitre"},
        {"name": "NIST_CSF", "url": "https://raw.githubusercontent.com/usnistgov/NIST-Cybersecurity-Framework/main/README.md", "type": "text"},

        {"name": "OWASP_Testing_Guide", "url": "https://raw.githubusercontent.com/OWASP/wstg/master/document/4-Web_Application_Security_Testing/README.md", "type": "text"},
        {"name": "ArXiv_Malware", "url": "https://export.arxiv.org/api/query?search_query=malware+detection+machine+learning&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Intrusion_Detection", "url": "https://export.arxiv.org/api/query?search_query=intrusion+detection+system+neural&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Vulnerability", "url": "https://export.arxiv.org/api/query?search_query=vulnerability+assessment+exploit&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_ZeroTrust", "url": "https://export.arxiv.org/api/query?search_query=zero+trust+security+architecture&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_AI_Security", "url": "https://export.arxiv.org/api/query?search_query=adversarial+machine+learning+security&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "radar_ew": [
        {"name": "DTIC_Radar", "url": "https://apps.dtic.mil/sti/api/search?q=radar+signal+processing&fields=title,abstract&rows=20", "type": "dtic"},
        {"name": "NASA_Radar", "url": "https://ntrs.nasa.gov/api/citations/search?q=radar&rows=10", "type": "nasa"},

        {"name": "ArXiv_Radar_ML", "url": "https://export.arxiv.org/api/query?search_query=radar+machine+learning+detection&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Signal_Processing", "url": "https://export.arxiv.org/api/query?search_query=cat:eess.SP&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Antenna", "url": "https://export.arxiv.org/api/query?search_query=phased+array+antenna+beamforming&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SAR", "url": "https://export.arxiv.org/api/query?search_query=synthetic+aperture+radar+imaging&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "physics": [
        {"name": "Feynman_Lectures_Vol1", "url": "https://archive.org/stream/feynmanlectures01feyn/feynmanlectures01feyn_djvu.txt", "type": "text"},
        {"name": "ArXiv_Physics_Survey", "url": "https://export.arxiv.org/api/query?search_query=cat:physics.class-ph&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_QM_Survey", "url": "https://export.arxiv.org/api/query?search_query=cat:quant-ph&max_results=50&sortBy=submittedDate", "type": "arxiv"},

        {"name": "ArXiv_Electromagnetism", "url": "https://export.arxiv.org/api/query?search_query=electromagnetism+Maxwell+equations&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Relativity", "url": "https://export.arxiv.org/api/query?search_query=general+relativity+spacetime+Einstein&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_NuclearPhysics", "url": "https://export.arxiv.org/api/query?search_query=cat:nucl-th&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Astrophysics", "url": "https://export.arxiv.org/api/query?search_query=cat:astro-ph&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Thermodynamics", "url": "https://export.arxiv.org/api/query?search_query=thermodynamics+statistical+mechanics&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "mathematics": [
        {"name": "ArXiv_Math_Analysis", "url": "https://export.arxiv.org/api/query?search_query=cat:math.CA&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Math_NumberTheory", "url": "https://export.arxiv.org/api/query?search_query=cat:math.NT&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Math_Probability", "url": "https://export.arxiv.org/api/query?search_query=cat:math.PR&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_DiffGeometry", "url": "https://export.arxiv.org/api/query?search_query=cat:math.DG&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Topology", "url": "https://export.arxiv.org/api/query?search_query=cat:math.AT&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Algebra", "url": "https://export.arxiv.org/api/query?search_query=cat:math.AG&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_MathPhysics", "url": "https://export.arxiv.org/api/query?search_query=cat:math-ph&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Euclid_Elements", "url": "https://www.gutenberg.org/cache/epub/21076/pg21076.txt", "type": "text"},

        {"name": "ArXiv_GameTheory", "url": "https://export.arxiv.org/api/query?search_query=cat:math.OC&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_ChaosTheory", "url": "https://export.arxiv.org/api/query?search_query=chaos+theory+dynamical+systems&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_CategoryTheory", "url": "https://export.arxiv.org/api/query?search_query=cat:math.CT&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Trigonometry", "url": "https://export.arxiv.org/api/query?search_query=trigonometry+Fourier+analysis+applications&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "psychology": [
        {"name": "PubMed_Consciousness", "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=consciousness+psychology&retmax=10&retmode=json", "type": "pubmed_search"},
        {"name": "ArXiv_CogSci", "url": "https://export.arxiv.org/api/query?search_query=cat:q-bio.NC&max_results=50&sortBy=submittedDate", "type": "arxiv"},

        {"name": "ArXiv_Social_Psychology", "url": "https://export.arxiv.org/api/query?search_query=social+psychology+behavior+influence&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Leadership", "url": "https://export.arxiv.org/api/query?search_query=leadership+psychology+organizational&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Grief", "url": "https://export.arxiv.org/api/query?search_query=grief+bereavement+psychology+coping&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Body_Language", "url": "https://export.arxiv.org/api/query?search_query=body+language+nonverbal+communication&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Deescalation", "url": "https://export.arxiv.org/api/query?search_query=de-escalation+conflict+resolution+psychology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "William_James_Psychology", "url": "https://www.gutenberg.org/cache/epub/630/pg630.txt", "type": "text"},
    ],
    "philosophy": [
        {"name": "Plato_Republic", "url": "https://www.gutenberg.org/files/1497/1497-0.txt", "type": "text"},
        {"name": "Aristotle_Ethics", "url": "https://www.gutenberg.org/files/8438/8438-0.txt", "type": "text"},
        {"name": "Nietzsche_Zarathustra", "url": "https://www.gutenberg.org/files/1998/1998-0.txt", "type": "text"},
        {"name": "Descartes_Meditations", "url": "https://www.gutenberg.org/files/59/59-0.txt", "type": "text"},

        {"name": "Kant_Critique", "url": "https://www.gutenberg.org/cache/epub/4280/pg4280.txt", "type": "text"},
        {"name": "Plato_Dialogues", "url": "https://www.gutenberg.org/cache/epub/1656/pg1656.txt", "type": "text"},
        {"name": "Marcus_Aurelius_Meditations", "url": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt", "type": "text"},
        {"name": "Seneca_Letters", "url": "https://www.gutenberg.org/cache/epub/1464/pg1464.txt", "type": "text"},
        {"name": "Epictetus_Discourses", "url": "https://www.gutenberg.org/cache/epub/4135/pg4135.txt", "type": "text"},
        {"name": "Locke_Human_Understanding", "url": "https://www.gutenberg.org/cache/epub/10615/pg10615.txt", "type": "text"},
        {"name": "Hume_Enquiry", "url": "https://www.gutenberg.org/cache/epub/9662/pg9662.txt", "type": "text"},
        {"name": "ArXiv_Philosophy_Mind", "url": "https://export.arxiv.org/api/query?search_query=philosophy+of+mind+consciousness&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "poetry": [
        {"name": "Rumi_Masnavi", "url": "https://www.gutenberg.org/files/57438/57438-0.txt", "type": "text"},
        {"name": "Whitman_Leaves_of_Grass", "url": "https://www.gutenberg.org/files/1322/1322-0.txt", "type": "text"},
        {"name": "Dickinson_Poems", "url": "https://www.gutenberg.org/files/12242/12242-0.txt", "type": "text"},
        {"name": "Shakespeare_Sonnets", "url": "https://www.gutenberg.org/files/1041/1041-0.txt", "type": "text"},
        {"name": "Gibran_Prophet", "url": "https://www.gutenberg.org/files/58585/58585-0.txt", "type": "text"},
        {"name": "Dante_Divine_Comedy", "url": "https://www.gutenberg.org/files/8800/8800-0.txt", "type": "text"},

        {"name": "Eliot_Wasteland", "url": "https://www.gutenberg.org/cache/epub/1321/pg1321.txt", "type": "text"},
        {"name": "Frost_Poems", "url": "https://www.gutenberg.org/cache/epub/59824/pg59824.txt", "type": "text"},
        {"name": "Maya_Angelou_Style", "url": "https://export.arxiv.org/api/query?search_query=Maya+Angelou+poetry+analysis&max_results=20&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Sylvia_Plath_Analysis", "url": "https://export.arxiv.org/api/query?search_query=Sylvia+Plath+poetry+confessional&max_results=20&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Shakespeare_Hamlet", "url": "https://www.gutenberg.org/cache/epub/1524/pg1524.txt", "type": "text"},
        {"name": "Shakespeare_Macbeth", "url": "https://www.gutenberg.org/cache/epub/1533/pg1533.txt", "type": "text"},
        {"name": "Blake_Songs", "url": "https://www.gutenberg.org/cache/epub/574/pg574.txt", "type": "text"},
        {"name": "Keats_Poems", "url": "https://www.gutenberg.org/cache/epub/2490/pg2490.txt", "type": "text"},
    ],
    "spirituality": [
        {"name": "Bhagavad_Gita", "url": "https://www.gutenberg.org/cache/epub/2388/pg2388.txt", "type": "text"},
        {"name": "Dhammapada_Buddhism", "url": "https://www.gutenberg.org/cache/epub/2017/pg2017.txt", "type": "text"},
        {"name": "Tao_Te_Ching", "url": "https://www.gutenberg.org/cache/epub/216/pg216.txt", "type": "text"},
        {"name": "CIA_Gateway_Experience", "url": "https://www.cia.gov/readingroom/document/cia-rdp96-00788r001700210016-5", "type": "text"},

        {"name": "Upanishads", "url": "https://www.gutenberg.org/cache/epub/68171/pg68171.txt", "type": "text"},
        {"name": "Book_of_Job", "url": "https://www.gutenberg.org/cache/epub/83/pg83.txt", "type": "text"},
        {"name": "ArXiv_Mindfulness", "url": "https://export.arxiv.org/api/query?search_query=mindfulness+meditation+clinical&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Transcendental", "url": "https://export.arxiv.org/api/query?search_query=transcendental+meditation+EEG+brain&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Lucid_Dreams", "url": "https://export.arxiv.org/api/query?search_query=lucid+dreaming+consciousness+sleep&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "logic_puzzles": [
        {"name": "ArXiv_Cryptanalysis", "url": "https://export.arxiv.org/api/query?search_query=cryptanalysis+cipher&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Peirce_Logic", "url": "https://www.gutenberg.org/cache/epub/69887/pg69887.txt", "type": "text"},

        {"name": "ArXiv_Game_Theory_Logic", "url": "https://export.arxiv.org/api/query?search_query=game+theory+logic+strategy+optimal&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cipher_Breaking", "url": "https://export.arxiv.org/api/query?search_query=cipher+breaking+historical+cryptography&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Deductive_Reasoning", "url": "https://export.arxiv.org/api/query?search_query=deductive+reasoning+logic+inference&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Lewis_Carroll_Logic", "url": "https://www.gutenberg.org/cache/epub/28696/pg28696.txt", "type": "text"},
    ],
    "survival": [
        {"name": "US_Army_Survival_Manual", "url": "https://www.gutenberg.org/files/17007/17007-0.txt", "type": "text"},
        {"name": "FEMA_Prepare", "url": "https://www.ready.gov/be-informed", "type": "text"},

        {"name": "ArXiv_Emergency_Medicine", "url": "https://export.arxiv.org/api/query?search_query=emergency+medicine+trauma+field&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Navigation", "url": "https://export.arxiv.org/api/query?search_query=navigation+orientation+wilderness+survival&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Scouting_Handbook", "url": "https://www.gutenberg.org/cache/epub/29558/pg29558.txt", "type": "text"},
    ],
    "technology": [
        {"name": "ArXiv_AI_ML", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_LLM", "url": "https://export.arxiv.org/api/query?search_query=large+language+models&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_QuantumTech", "url": "https://export.arxiv.org/api/query?search_query=quantum+technology+applications&max_results=50&sortBy=submittedDate", "type": "arxiv"},

        {"name": "ArXiv_Robotics", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.RO&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_HCI", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.HC&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cybersecurity_AI", "url": "https://export.arxiv.org/api/query?search_query=artificial+intelligence+cybersecurity+defense&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],

    "programming": [
        {"name": "Python_Docs_Tutorial", "url": "https://docs.python.org/3/tutorial/index.html", "type": "text"},
        {"name": "Bash_Guide", "url": "https://tldp.org/LDP/Bash-Beginners-Guide/html/Bash-Beginners-Guide.html", "type": "text"},
        {"name": "Linux_Command_Line", "url": "https://www.gnu.org/software/bash/manual/bash.html", "type": "text"},
        {"name": "JavaScript_MDN", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "type": "text"},
        {"name": "ArXiv_ProgrammingLanguages", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.PL&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_SoftwareEngineering", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.SE&max_results=50&sortBy=submittedDate", "type": "arxiv"},

        {"name": "ArXiv_MachineLearning_Code", "url": "https://export.arxiv.org/api/query?search_query=machine+learning+implementation+tutorial&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_AppDevelopment", "url": "https://export.arxiv.org/api/query?search_query=mobile+app+development+architecture&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_MATLAB_Signal", "url": "https://export.arxiv.org/api/query?search_query=MATLAB+signal+processing+implementation&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "history": [
        {"name": "US_Constitution", "url": "https://www.gutenberg.org/cache/epub/5/pg5.txt", "type": "text"},
        {"name": "Declaration_Independence", "url": "https://www.gutenberg.org/cache/epub/1/pg1.txt", "type": "text"},
        {"name": "Herodotus_Histories", "url": "https://www.gutenberg.org/cache/epub/2707/pg2707.txt", "type": "text"},
        {"name": "Greek_Mythology_Bulfinch", "url": "https://www.gutenberg.org/cache/epub/4928/pg4928.txt", "type": "text"},
        {"name": "ArXiv_DigitalHistory", "url": "https://export.arxiv.org/api/query?search_query=historical+analysis+computational&max_results=50&sortBy=submittedDate", "type": "arxiv"},

        {"name": "Sun_Tzu_Art_of_War", "url": "https://www.gutenberg.org/cache/epub/132/pg132.txt", "type": "text"},
        {"name": "Machiavelli_Prince", "url": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt", "type": "text"},
        {"name": "Caesar_Gallic_Wars", "url": "https://www.gutenberg.org/cache/epub/10657/pg10657.txt", "type": "text"},
        {"name": "ArXiv_Military_History", "url": "https://export.arxiv.org/api/query?search_query=military+history+strategy+warfare&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Mythology", "url": "https://export.arxiv.org/api/query?search_query=mythology+ancient+symbolism+archetype&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Unsolved_History", "url": "https://export.arxiv.org/api/query?search_query=historical+mystery+unsolved+ancient&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "paradoxes": [
        {"name": "Zeno_Paradoxes_Analysis", "url": "https://export.arxiv.org/api/query?search_query=Zeno+paradox+philosophy&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Paradoxes_Logic", "url": "https://export.arxiv.org/api/query?search_query=logical+paradox+self+reference&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Fermi_Paradox", "url": "https://export.arxiv.org/api/query?search_query=Fermi+paradox+extraterrestrial&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "quantum_technology": [
        {"name": "ArXiv_QuantumComputing", "url": "https://export.arxiv.org/api/query?search_query=cat:quant-ph+quantum+computing&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_QuantumCrypto", "url": "https://export.arxiv.org/api/query?search_query=quantum+cryptography+QKD&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_QuantumNetworks", "url": "https://export.arxiv.org/api/query?search_query=quantum+network+entanglement+communication&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_PostQuantumCrypto", "url": "https://export.arxiv.org/api/query?search_query=post+quantum+cryptography+NIST&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "finances": [
        {"name": "ArXiv_Bitcoin", "url": "https://export.arxiv.org/api/query?search_query=Bitcoin+blockchain+cryptocurrency&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Investment", "url": "https://export.arxiv.org/api/query?search_query=investment+strategy+portfolio+optimization&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_FinancialMath", "url": "https://export.arxiv.org/api/query?search_query=cat:q-fin.PM&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "certifications": [
        {"name": "ArXiv_SecurityCerts", "url": "https://export.arxiv.org/api/query?search_query=cybersecurity+certification+security&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_NetworkFundamentals", "url": "https://export.arxiv.org/api/query?search_query=network+security+fundamentals+TCP+IP&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_CloudSecurity", "url": "https://export.arxiv.org/api/query?search_query=cloud+security+architecture+compliance&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_PenTesting", "url": "https://export.arxiv.org/api/query?search_query=penetration+testing+methodology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "gardening": [
        {"name": "Henderson_Gardening", "url": "https://www.gutenberg.org/cache/epub/43500/pg43500.txt", "type": "text"},
        {"name": "ArXiv_Soil_Science", "url": "https://export.arxiv.org/api/query?search_query=soil+science+composition+organic+matter&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Companion_Planting", "url": "https://export.arxiv.org/api/query?search_query=companion+planting+intercropping+vegetable&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Permaculture", "url": "https://export.arxiv.org/api/query?search_query=permaculture+sustainable+food+systems&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Container_Gardening", "url": "https://export.arxiv.org/api/query?search_query=container+gardening+urban+agriculture&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Composting", "url": "https://export.arxiv.org/api/query?search_query=composting+soil+amendment+organic&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Pest_Management", "url": "https://export.arxiv.org/api/query?search_query=integrated+pest+management+organic+garden&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Medicinal_Herbs", "url": "https://export.arxiv.org/api/query?search_query=medicinal+herbs+phytochemistry+therapeutic&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Native_Plants", "url": "https://export.arxiv.org/api/query?search_query=native+plants+southeastern+United+States+ecology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Food_Forest", "url": "https://export.arxiv.org/api/query?search_query=food+forest+agroforestry+edible+landscape&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Raised_Bed_Science", "url": "https://export.arxiv.org/api/query?search_query=raised+bed+gardening+soil+yield+vegetable&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Water_Management", "url": "https://export.arxiv.org/api/query?search_query=irrigation+water+management+garden+drip&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Season_Extension", "url": "https://export.arxiv.org/api/query?search_query=season+extension+cold+frame+greenhouse+temperate&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Seed_Saving", "url": "https://export.arxiv.org/api/query?search_query=seed+saving+heirloom+varieties+preservation&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "creative_writing": [
        {"name": "Poe_Tales", "url": "https://www.gutenberg.org/cache/epub/2147/pg2147.txt", "type": "text"},
        {"name": "Lovecraft_Call_Cthulhu", "url": "https://www.gutenberg.org/cache/epub/68595/pg68595.txt", "type": "text"},
        {"name": "Stoker_Dracula", "url": "https://www.gutenberg.org/cache/epub/345/pg345.txt", "type": "text"},
        {"name": "Shelley_Frankenstein", "url": "https://www.gutenberg.org/cache/epub/84/pg84.txt", "type": "text"},
        {"name": "Doyle_Sherlock_Holmes", "url": "https://www.gutenberg.org/cache/epub/1661/pg1661.txt", "type": "text"},
        {"name": "ArXiv_Narrative_Structure", "url": "https://export.arxiv.org/api/query?search_query=narrative+structure+fiction+storytelling&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Screenwriting", "url": "https://export.arxiv.org/api/query?search_query=screenwriting+screenplay+story+structure&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Supernatural_Fiction", "url": "https://export.arxiv.org/api/query?search_query=supernatural+horror+fiction+gothic+narrative&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Character_Development", "url": "https://export.arxiv.org/api/query?search_query=character+development+fiction+protagonist+arc&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Mystery_Thriller", "url": "https://export.arxiv.org/api/query?search_query=mystery+thriller+genre+fiction+suspense&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Romance_Fiction", "url": "https://export.arxiv.org/api/query?search_query=romance+fiction+narrative+emotional+arc&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_World_Building", "url": "https://export.arxiv.org/api/query?search_query=world+building+speculative+fiction+mythology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Mythology_Narrative", "url": "https://export.arxiv.org/api/query?search_query=mythology+archetype+hero+journey+Campbell&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Dialogue_Writing", "url": "https://export.arxiv.org/api/query?search_query=dialogue+writing+fiction+voice+character&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Pacing_Tension", "url": "https://export.arxiv.org/api/query?search_query=narrative+pacing+tension+suspense+fiction&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Prose_Style", "url": "https://export.arxiv.org/api/query?search_query=prose+style+literary+fiction+technique&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "social_dynamics": [
        {"name": "ArXiv_Persuasion_Influence", "url": "https://export.arxiv.org/api/query?search_query=persuasion+influence+psychology+Cialdini&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Negotiation", "url": "https://export.arxiv.org/api/query?search_query=negotiation+strategy+psychology+conflict&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rapport_Building", "url": "https://export.arxiv.org/api/query?search_query=rapport+building+trust+interpersonal+communication&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Emotional_Intelligence", "url": "https://export.arxiv.org/api/query?search_query=emotional+intelligence+social+awareness+empathy&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rhetoric", "url": "https://export.arxiv.org/api/query?search_query=rhetoric+argumentation+persuasive+communication&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Conflict_Resolution", "url": "https://export.arxiv.org/api/query?search_query=conflict+resolution+mediation+communication&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Social_Influence", "url": "https://export.arxiv.org/api/query?search_query=social+influence+group+dynamics+behavior&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Nonverbal_Communication", "url": "https://export.arxiv.org/api/query?search_query=nonverbal+communication+body+language+social&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Professional_Communication", "url": "https://export.arxiv.org/api/query?search_query=professional+communication+workplace+networking&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Power_Dynamics", "url": "https://export.arxiv.org/api/query?search_query=power+dynamics+social+hierarchy+influence&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cultural_Intelligence", "url": "https://export.arxiv.org/api/query?search_query=cultural+intelligence+cross+cultural+communication&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Interpersonal_Dynamics", "url": "https://export.arxiv.org/api/query?search_query=interpersonal+dynamics+relationship+psychology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "health": [
        {"name": "Gray_Anatomy", "url": "https://www.gutenberg.org/cache/epub/39722/pg39722.txt", "type": "text"},
        {"name": "ArXiv_Anatomy_Physiology", "url": "https://export.arxiv.org/api/query?search_query=human+anatomy+physiology+systems&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Trauma_Medicine", "url": "https://export.arxiv.org/api/query?search_query=trauma+medicine+emergency+treatment+field&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Mental_Health", "url": "https://export.arxiv.org/api/query?search_query=mental+health+PTSD+treatment+veterans&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Nutrition_Science", "url": "https://export.arxiv.org/api/query?search_query=nutrition+science+macronutrients+micronutrients&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Exercise_Science", "url": "https://export.arxiv.org/api/query?search_query=exercise+science+strength+training+physiology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Sleep_Science", "url": "https://export.arxiv.org/api/query?search_query=sleep+science+circadian+rhythm+recovery&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Stress_Physiology", "url": "https://export.arxiv.org/api/query?search_query=stress+physiology+cortisol+nervous+system&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Longevity", "url": "https://export.arxiv.org/api/query?search_query=longevity+aging+healthspan+lifestyle&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Gut_Health", "url": "https://export.arxiv.org/api/query?search_query=gut+microbiome+health+nutrition+brain&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cardiovascular", "url": "https://export.arxiv.org/api/query?search_query=cardiovascular+health+heart+fitness&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_General_Wellness", "url": "https://export.arxiv.org/api/query?search_query=holistic+wellness+preventive+medicine+lifestyle&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "music": [
        {"name": "ArXiv_HipHop_Lyricism", "url": "https://export.arxiv.org/api/query?search_query=hip+hop+lyricism+flow+rhyme+scheme&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Music_Theory", "url": "https://export.arxiv.org/api/query?search_query=music+theory+harmony+composition&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Beat_Production", "url": "https://export.arxiv.org/api/query?search_query=music+production+beat+making+sampling&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rhythm_Meter", "url": "https://export.arxiv.org/api/query?search_query=rhythm+meter+timing+music+performance&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rap_Culture", "url": "https://export.arxiv.org/api/query?search_query=hip+hop+culture+history+African+American&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Vocal_Delivery", "url": "https://export.arxiv.org/api/query?search_query=vocal+delivery+performance+music+style&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Sound_Design", "url": "https://export.arxiv.org/api/query?search_query=sound+design+audio+engineering+mixing&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Music_Psychology", "url": "https://export.arxiv.org/api/query?search_query=music+psychology+emotion+cognition&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Songwriting", "url": "https://export.arxiv.org/api/query?search_query=songwriting+composition+lyrics+melody&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Music_History", "url": "https://export.arxiv.org/api/query?search_query=music+history+African+American+blues+jazz+rap&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "resume_career": [
        {"name": "ArXiv_AI_Security_Careers", "url": "https://export.arxiv.org/api/query?search_query=AI+security+career+workforce+skills&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cybersecurity_Workforce", "url": "https://export.arxiv.org/api/query?search_query=cybersecurity+workforce+skills+gap+hiring&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Defense_Contractor", "url": "https://export.arxiv.org/api/query?search_query=defense+contractor+technology+workforce+security+clearance&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Technical_Interview", "url": "https://export.arxiv.org/api/query?search_query=technical+interview+software+engineering+hiring&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Professional_Development", "url": "https://export.arxiv.org/api/query?search_query=professional+development+IT+career+growth&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Veterans_Tech", "url": "https://export.arxiv.org/api/query?search_query=veterans+technology+careers+transition+military&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Portfolio_Building", "url": "https://export.arxiv.org/api/query?search_query=technical+portfolio+github+projects+hiring&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Networking_Career", "url": "https://export.arxiv.org/api/query?search_query=professional+networking+career+advancement+strategy&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "research": [
        {"name": "ArXiv_Research_Methodology", "url": "https://export.arxiv.org/api/query?search_query=research+methodology+scientific+method&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Technical_Writing", "url": "https://export.arxiv.org/api/query?search_query=technical+writing+scientific+paper+documentation&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Data_Analysis", "url": "https://export.arxiv.org/api/query?search_query=data+analysis+statistical+methods+research&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Literature_Review", "url": "https://export.arxiv.org/api/query?search_query=systematic+literature+review+methodology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Experimental_Design", "url": "https://export.arxiv.org/api/query?search_query=experimental+design+hypothesis+testing+method&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Signal_Research", "url": "https://export.arxiv.org/api/query?search_query=signal+processing+research+methods+DSP&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "mathematics_advanced": [
        {"name": "ArXiv_Real_Analysis", "url": "https://export.arxiv.org/api/query?search_query=real+analysis+measure+theory+Lebesgue&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Algebraic_Geometry", "url": "https://export.arxiv.org/api/query?search_query=cat:math.AG&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Topology", "url": "https://export.arxiv.org/api/query?search_query=cat:math.GN&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Discrete_Mathematics", "url": "https://export.arxiv.org/api/query?search_query=cat:math.CO&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Functional_Analysis", "url": "https://export.arxiv.org/api/query?search_query=cat:math.FA&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Algebraic_Topology", "url": "https://export.arxiv.org/api/query?search_query=cat:math.AT&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Differential_Geometry", "url": "https://export.arxiv.org/api/query?search_query=cat:math.DG&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Combinatorics", "url": "https://export.arxiv.org/api/query?search_query=combinatorics+graph+theory+enumeration&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Applied_Math_Signal", "url": "https://export.arxiv.org/api/query?search_query=applied+mathematics+signal+processing+Fourier&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Applied_Math_AI", "url": "https://export.arxiv.org/api/query?search_query=applied+mathematics+machine+learning+optimization&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Linear_Algebra", "url": "https://export.arxiv.org/api/query?search_query=linear+algebra+matrix+decomposition+applications&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Statistics", "url": "https://export.arxiv.org/api/query?search_query=cat:math.ST&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Abstract_Algebra", "url": "https://export.arxiv.org/api/query?search_query=cat:math.RA&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Numerical_Analysis", "url": "https://export.arxiv.org/api/query?search_query=cat:math.NA&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "physics_advanced": [
        {"name": "ArXiv_Applied_Physics", "url": "https://export.arxiv.org/api/query?search_query=cat:physics.app-ph&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Gravity", "url": "https://export.arxiv.org/api/query?search_query=gravity+gravitational+waves+general+relativity&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Propulsion", "url": "https://export.arxiv.org/api/query?search_query=propulsion+advanced+aerospace+plasma+ion&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Electromagnetics", "url": "https://export.arxiv.org/api/query?search_query=electromagnetics+Maxwell+equations+wave+propagation&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Wave_Propagation", "url": "https://export.arxiv.org/api/query?search_query=wave+propagation+scattering+diffraction+medium&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Mechanics", "url": "https://export.arxiv.org/api/query?search_query=quantum+mechanics+wavefunction+Schrodinger+measurement&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_String_Theory", "url": "https://export.arxiv.org/api/query?search_query=string+theory+M+theory+extra+dimensions&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Field_Theory", "url": "https://export.arxiv.org/api/query?search_query=quantum+field+theory+QFT+standard+model&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Statistical_Mechanics", "url": "https://export.arxiv.org/api/query?search_query=statistical+mechanics+thermodynamics+entropy&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Classical_Mechanics", "url": "https://export.arxiv.org/api/query?search_query=classical+mechanics+Lagrangian+Hamiltonian+dynamics&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Relativity", "url": "https://export.arxiv.org/api/query?search_query=special+relativity+relative+velocity+spacetime+Lorentz&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cosmology", "url": "https://export.arxiv.org/api/query?search_query=cat:astro-ph.CO&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Plasma_Physics", "url": "https://export.arxiv.org/api/query?search_query=cat:physics.plasm-ph&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Condensed_Matter", "url": "https://export.arxiv.org/api/query?search_query=cat:cond-mat&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "quantum_advanced": [
        {"name": "ArXiv_Quantum_Sensing", "url": "https://export.arxiv.org/api/query?search_query=quantum+sensing+quantum+metrology+precision&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Radar", "url": "https://export.arxiv.org/api/query?search_query=quantum+radar+quantum+illumination+target+detection&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Lidar", "url": "https://export.arxiv.org/api/query?search_query=quantum+lidar+quantum+imaging+photon&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Communication", "url": "https://export.arxiv.org/api/query?search_query=quantum+communication+entanglement+teleportation&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Computing_Algorithms", "url": "https://export.arxiv.org/api/query?search_query=quantum+algorithm+Grover+Shor+speedup&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Error_Correction", "url": "https://export.arxiv.org/api/query?search_query=quantum+error+correction+fault+tolerant&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Defense", "url": "https://export.arxiv.org/api/query?search_query=quantum+technology+defense+military+sensing&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_Entanglement", "url": "https://export.arxiv.org/api/query?search_query=quantum+entanglement+Bell+inequality+nonlocality&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Photonic_Quantum", "url": "https://export.arxiv.org/api/query?search_query=photonic+quantum+computing+optical+qubit&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Quantum_AI", "url": "https://export.arxiv.org/api/query?search_query=quantum+machine+learning+quantum+neural+network&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "writing_craft": [
        {"name": "Strunk_White_Style", "url": "https://www.gutenberg.org/cache/epub/37134/pg37134.txt", "type": "text"},
        {"name": "ArXiv_Writing_Craft", "url": "https://export.arxiv.org/api/query?search_query=writing+craft+style+prose+composition&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Grammar_Linguistics", "url": "https://export.arxiv.org/api/query?search_query=grammar+linguistics+syntax+English+composition&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Rhetoric_Writing", "url": "https://export.arxiv.org/api/query?search_query=rhetoric+persuasive+writing+composition+argument&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Technical_Documentation", "url": "https://export.arxiv.org/api/query?search_query=technical+documentation+writing+software+engineering&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Narrative_Voice", "url": "https://export.arxiv.org/api/query?search_query=narrative+voice+style+author+fiction+prose&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Editing_Revision", "url": "https://export.arxiv.org/api/query?search_query=editing+revision+writing+process+manuscript&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Publishing_Industry", "url": "https://export.arxiv.org/api/query?search_query=publishing+industry+book+manuscript+literary+agent&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Aristotle_Poetics", "url": "https://www.gutenberg.org/cache/epub/1974/pg1974.txt", "type": "text"},
        {"name": "ArXiv_Metaphor_Language", "url": "https://export.arxiv.org/api/query?search_query=metaphor+figurative+language+cognitive+linguistics&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
    "spiritual_advanced": [
        {"name": "ArXiv_Consciousness_Science", "url": "https://export.arxiv.org/api/query?search_query=consciousness+science+neural+correlates+awareness&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Gateway_Experience", "url": "https://export.arxiv.org/api/query?search_query=Monroe+Institute+Gateway+Experience+consciousness+hemi-sync&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Remote_Viewing", "url": "https://export.arxiv.org/api/query?search_query=remote+viewing+parapsychology+consciousness+CIA&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Astral_Projection", "url": "https://export.arxiv.org/api/query?search_query=astral+projection+out+of+body+experience+sleep+paralysis&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Transcendental_Meditation", "url": "https://export.arxiv.org/api/query?search_query=transcendental+meditation+brainwave+alpha+theta&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Breathwork", "url": "https://export.arxiv.org/api/query?search_query=breathwork+pranayama+Wim+Hof+holotropic+breathing&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Lucid_Dreaming_Advanced", "url": "https://export.arxiv.org/api/query?search_query=lucid+dreaming+WILD+MILD+induction+technique+REM&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_UAP_Research", "url": "https://export.arxiv.org/api/query?search_query=unidentified+aerial+phenomena+UAP+UFO+scientific&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Cryptozoology", "url": "https://export.arxiv.org/api/query?search_query=cryptozoology+unknown+species+folklore+zoology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_World_Religions", "url": "https://export.arxiv.org/api/query?search_query=comparative+religion+world+religions+theology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Islam", "url": "https://export.arxiv.org/api/query?search_query=Islam+Quran+Sufi+mysticism+Islamic+theology&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Christianity", "url": "https://export.arxiv.org/api/query?search_query=Christianity+theology+mysticism+contemplative+prayer&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Buddhism_Advanced", "url": "https://export.arxiv.org/api/query?search_query=Buddhism+Zen+Tibetan+meditation+dharma&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Hinduism", "url": "https://export.arxiv.org/api/query?search_query=Hinduism+Vedanta+yoga+Advaita+Brahman&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Indigenous_Spirituality", "url": "https://export.arxiv.org/api/query?search_query=indigenous+spirituality+shamanism+animism+ceremony&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Near_Death_Experience", "url": "https://export.arxiv.org/api/query?search_query=near+death+experience+NDE+consciousness+afterlife&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Guided_Meditation", "url": "https://export.arxiv.org/api/query?search_query=guided+meditation+visualization+relaxation+script&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Psychedelics_Consciousness", "url": "https://export.arxiv.org/api/query?search_query=psychedelics+psilocybin+DMT+consciousness+mystical+experience&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "Quran_English", "url": "https://www.gutenberg.org/cache/epub/2800/pg2800.txt", "type": "text"},
        {"name": "Bible_KJV", "url": "https://www.gutenberg.org/cache/epub/10/pg10.txt", "type": "text"},
    ],
    "spiritual": [
        {"name": "ArXiv_Meditation_Neuroscience", "url": "https://export.arxiv.org/api/query?search_query=meditation+neuroscience+consciousness&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_OBE_Research", "url": "https://export.arxiv.org/api/query?search_query=out+of+body+experience+consciousness&max_results=50&sortBy=submittedDate", "type": "arxiv"},
        {"name": "ArXiv_Altered_States", "url": "https://export.arxiv.org/api/query?search_query=altered+states+consciousness+meditation&max_results=50&sortBy=submittedDate", "type": "arxiv"},
    ],
}

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
    print(f"  Saved: {filename} ({len(content):,} chars)")
    return filepath

def scrape_text(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"  Skip: {source['name']} (done)")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Scraper/1.0"}, timeout=30)
        r.raise_for_status()
        save_document(domain, source["name"], r.text[:50000], url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
    except Exception as e:
        print(f"  Error: {e}")

def scrape_arxiv(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"  Skip: {source['name']} (done)")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Scraper/1.0"}, timeout=30)
        r.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        content = f"ArXiv Papers - {source['name']}\n\n"
        for entry in entries:
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            if title is not None and summary is not None:
                content += f"Title: {title.text.strip()}\n"
                content += f"Abstract: {summary.text.strip()[:600]}\n\n"
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
        print(f"  Scraped {len(entries)} papers")
    except Exception as e:
        print(f"  Error: {e}")

def scrape_nvd(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"  Skip: {source['name']} (done)")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Scraper/1.0"}, timeout=30)
        r.raise_for_status()
        data = r.json()
        vulns = data.get("vulnerabilities", [])
        content = "NIST NVD - Critical CVEs\n\n"
        for v in vulns:
            cve = v.get("cve", {})
            cid = cve.get("id", "")
            desc = next((d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"), "")
            metrics = cve.get("metrics", {})
            cvss = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
            content += f"CVE: {cid}\nSeverity: {cvss.get('baseSeverity','N/A')} ({cvss.get('baseScore','N/A')})\n{desc}\n\n"
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
        print(f"  Scraped {len(vulns)} CVEs")
    except Exception as e:
        print(f"  Error: {e}")

def scrape_mitre(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"  Skip: {source['name']} (done)")
        return
    try:
        r = requests.get(url, headers={"User-Agent": "NISA-Scraper/1.0"}, timeout=60)
        r.raise_for_status()
        data = r.json()
        techniques = [o for o in data.get("objects", []) if o.get("type") == "attack-pattern"][:50]
        content = "MITRE ATT&CK Enterprise Techniques\n\n"
        for t in techniques:
            phases = [k.get("phase_name") for k in t.get("kill_chain_phases", [])]
            content += f"Technique: {t.get('name','')}\nPhases: {', '.join(phases)}\n{t.get('description','')[:500]}\n\n"
        save_document(domain, source["name"], content, url)
        state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
        print(f"  Scraped {len(techniques)} techniques")
    except Exception as e:
        print(f"  Error: {e}")

def scrape_pdf(source, domain, state):
    url = source["url"]
    uid = url_hash(url)
    if uid in state["scraped"]:
        print(f"  Skip: {source['name']} (done)")
        return
    try:
        import tempfile
        r = requests.get(url, headers={"User-Agent": "NISA-Scraper/1.0"}, timeout=60)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(r.content)
            tmp = f.name
        import subprocess
        result = subprocess.run(["pdftotext", tmp, "-"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            save_document(domain, source["name"], result.stdout[:50000], url)
            state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
        else:
            print(f"  PDF extraction failed - saving as binary note")
            save_document(domain, source["name"], f"PDF document from {url} - requires manual extraction", url)
            state["scraped"][uid] = {"name": source["name"], "ts": datetime.now().isoformat()}
        os.unlink(tmp)
    except Exception as e:
        print(f"  Error: {e}")

def run_scraper(domains=None, force=False):
    print("=" * 60)
    print("  NISA Knowledge Web Scraper")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    state = load_state()
    if force:
        state["scraped"] = {}
        print("Force mode: clearing state")
    
    dispatch = {
        "text": scrape_text,
        "arxiv": scrape_arxiv,
        "nvd": scrape_nvd,
        "mitre": scrape_mitre,
        "pdf": scrape_pdf,
        "dtic": scrape_text,
        "nasa": scrape_text,
        "pubmed_search": scrape_text,
    }
    
    target_domains = domains or list(SOURCES.keys())
    for domain in target_domains:
        if domain not in SOURCES:
            continue
        print(f"\nDomain: {domain}")
        for source in SOURCES[domain]:
            print(f"  {source['name']}")
            fn = dispatch.get(source["type"], scrape_text)
            fn(source, domain, state)
            time.sleep(DELAY)
    
    save_state(state)
    print(f"\nComplete. {len(state['scraped'])} sources scraped total.")

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    domains = [a for a in sys.argv[1:] if not a.startswith("--")] or None
    run_scraper(domains=domains, force=force)
