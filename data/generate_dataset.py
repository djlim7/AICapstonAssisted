"""
Generate 214 synthetic postgraduate data-science project proposals.

Output: data/proposals_214.json
  - 107 High Performers (HD/D), scores 10.5–15
  - 107 Low Performers  (C/P/N), scores 5.0–10.0

Run:
    python data/generate_dataset.py
"""

import json
import random
from pathlib import Path

random.seed(42)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(idx: int, group: str, score: float, title: str, desc: str, biz: str) -> dict:
    return {
        "id": f"p_{group.lower()}_{idx:03d}",
        "performance_group": group,
        "human_score": round(score, 1),
        "text": f"Title: {title}\n\nProject Description:\n{desc}\n\nBusiness Model:\n{biz}",
    }


def _uniform(n: int, lo: float, hi: float) -> list[float]:
    step = (hi - lo) / n
    return [lo + step * i + step * random.random() for i in range(n)]


def _high_scores(n: int) -> list[float]:
    """
    Scores for High performers matching the paper's original grade distribution
    (Fig. 1): HD=45.8%, D=26.9% → within High group: HD≈63%, D≈37%.

    Grade-to-raw-score mapping (raw = scaled/100 * 15):
      HD (80–100 scaled) → 12.0–15.0 raw
      D  (70–79  scaled) → 10.5–11.85 raw
    """
    n_hd = round(n * 0.63)
    n_d  = n - n_hd
    scores = _uniform(n_hd, 12.0, 15.0) + _uniform(n_d, 10.5, 11.85)
    random.shuffle(scores)
    return scores


def _low_scores(n: int) -> list[float]:
    """
    Scores for Low performers matching the paper's original grade distribution
    (Fig. 1): C=16.9%, P=7.7%, N=2.7% → within Low group: C≈62%, P≈28%, N≈10%.

    Grade-to-raw-score mapping:
      C (60–69 scaled) → 9.0–10.35 raw
      P (50–59 scaled) → 7.5–8.85  raw
      N (0–49  scaled) → 4.0–7.35  raw  (floor at 4.0 for realism; real fails rarely score 0)
    """
    n_c = round(n * 0.62)
    n_p = round(n * 0.28)
    n_n = n - n_c - n_p
    scores = _uniform(n_c, 9.0, 10.35) + _uniform(n_p, 7.5, 8.85) + _uniform(n_n, 4.0, 7.35)
    random.shuffle(scores)
    return scores


# ---------------------------------------------------------------------------
# HIGH-PERFORMER PROPOSALS  (107 total, scores 10.5–15)
# ---------------------------------------------------------------------------

def _high_proposals() -> list[dict]:
    records = []
    scores = _high_scores(107)
    si = iter(scores)

    # ── 1. Healthcare prediction (8 proposals) ──────────────────────────────
    hc_variants = [
        ("Predicting 30-Day Hospital Readmissions for Cardiac Patients",
         "Using CMS Medicare claims data (2018–2023) we build an ensemble of XGBoost and LSTM networks to predict 30-day readmissions for heart-failure patients. Features span ICD-10 codes, lab trends, medication adherence, and social determinants of health. A data engineer owns the ETL pipeline from CMS APIs; an ML engineer maintains model versioning on AWS SageMaker; a clinical informatician validates clinical plausibility of features.",
         "Target beneficiaries are hospital administrators subject to CMS's Hospital Readmissions Reduction Program (HRRP). A 15% reduction in readmission rate for a 600-bed hospital translates to approximately $1.8 M in avoided CMS penalties annually. Challenges include class imbalance (~12% positive), HIPAA compliance, and clinician distrust of black-box predictions. Mitigations: SMOTE oversampling, de-identified federated learning, and SHAP-based explanation dashboards co-designed with clinical staff."),
        ("Early Sepsis Detection in ICU Patients via Multivariate Time-Series",
         "This project applies a Temporal Convolutional Network (TCN) to MIMIC-IV ICU time-series — heart rate, MAP, SpO2, lactate — to issue a 6-hour early warning for sepsis onset. Roles: data engineer (MIMIC extraction pipeline), ML engineer (TCN training and ONNX export for latency-critical inference), intensivist (clinical validation). We use Rolling-window cross-validation to respect temporal ordering.",
         "ICU sepsis carries a 20–30% mortality rate; 6-hour early intervention reduces mortality by ~25%. For a 30-bed ICU with ~400 sepsis cases per year, projected lives saved exceed 20 annually. Deployment challenges include real-time data pipeline latency (<2 min end-to-end), alert fatigue (mitigated via a precision-tuned threshold of >0.85), and EHR vendor lock-in (addressed through FHIR-compliant APIs)."),
        ("Breast Cancer Malignancy Classification from Digital Mammograms",
         "We fine-tune an EfficientNet-B4 convolutional model on the CBIS-DDSM mammography dataset (2,620 cases) augmented with synthetic minority-class images from a conditional GAN. Grad-CAM heatmaps surface lesion localisation for radiologist review. Team: a medical imaging data scientist, a deep learning engineer, and a senior radiologist as domain expert.",
         "Radiologists mis-classify ~12% of cases on initial read; AI-assisted screening is projected to reduce false negatives by 30% at Australian breast-screening clinics processing ~400,000 screens per year. Deployment via a CE-marked Software as Medical Device (SaMD) integration with existing PACS. Challenges: distribution shift across different mammography devices; mitigated via device-stratified normalisation and prospective multi-site validation."),
        ("Drug Repurposing for Rare Diseases Using Knowledge Graph Embeddings",
         "We construct a biomedical knowledge graph from DrugBank, DisGeNET, and STRING protein interaction databases, then train RotatE embeddings to score candidate drug–disease links for 50 rare diseases lacking approved therapies. A bioinformatician handles graph construction; a data scientist trains and evaluates embeddings; a pharmacologist curates positive training links.",
         "Drug repurposing reduces development cost from ~$2.6 B to ~$300 M per candidate and cuts timeline by 30%. The system surfaces the top-10 candidates per disease for wet-lab validation, with an expected 5–10 novel repurposing hypotheses per rare disease. Challenges: data incompleteness across ontologies (addressed by graph alignment via BioPortal), and negative sampling bias (addressed by a curriculum-learning schedule)."),
        ("Alzheimer's Progression Forecasting from Longitudinal MRI and Biomarkers",
         "Leveraging ADNI longitudinal data (over 1,800 participants, 5-year follow-up), we train a variational autoencoder on 3D T1-weighted MRI slices and concatenate latent representations with CSF biomarkers (Aβ42, p-tau) in a survival analysis model (DeepSurv). A neuroimaging engineer manages FreeSurfer preprocessing; an ML engineer maintains the VAE pipeline; a neurologist validates clinically relevant hippocampal atrophy trajectories.",
         "Early Alzheimer's identification 3–5 years before symptom onset enables clinical trial eligibility screening, valued at ~$50,000 per qualified participant for pharmaceutical sponsors. Patient benefit includes access to preventive interventions. Challenges: high missing-data rate in longitudinal imaging (addressed via multiple imputation), and heterogeneity across MRI scanners (addressed via ComBat harmonisation)."),
        ("Predicting ICU Length-of-Stay to Optimise Bed Allocation",
         "We model ICU length-of-stay as a regression task using a LightGBM model on admission features from the eICU Collaborative Research Database (200K+ ICU stays). Features include APACHE IV severity score, diagnosis category, and initial lab values. Team: data engineer (eICU API integration), ML engineer (LightGBM pipeline), hospital operations analyst (bed-planning simulation).",
         "A 10% improvement in ICU bed utilisation in a 500-bed hospital generates ~$2.4 M additional revenue annually by reducing unnecessary day-of-surgery cancellations. Challenges include dynamic updates as patient condition changes (addressed by hourly model re-inference), and distribution shift across hospital types in eICU (addressed by hospital-stratified calibration)."),
        ("Mental Health Crisis Prediction from Electronic Health Records",
         "Using longitudinal GP visit records and prescription data from the CPRD UK database, we train a gradient-boosted model with temporal features (visit frequency trends, antidepressant dose escalations) to predict emergency mental-health presentations within 30 days. A health data scientist leads feature engineering; a GP provides clinical labelling guidelines; a data engineer builds the CPRD extraction pipeline.",
         "Mental health emergency presentations cost the NHS ~£1,800 per episode. Predicting 40% of at-risk patients 30 days in advance enables proactive outreach, projected to prevent 600 presentations per 100,000 enrolled patients annually. Challenges: stigma-driven under-recording of diagnoses (addressed via proxy features such as sleep-aid prescriptions), and class imbalance (addressed via focal loss)."),
        ("Protein-Ligand Binding Affinity Prediction for Drug Discovery",
         "We implement an SE(3)-equivariant graph neural network (SE3-Transformer) trained on the PDBbind 2020 dataset (19,443 protein–ligand complexes) to predict binding affinity (Ki/IC50). A computational chemist curates input featurisation (atom types, bond orders, partial charges); an ML engineer manages distributed training on A100 GPUs; a medicinal chemist validates top-ranked candidates.",
         "Virtual screening with accurate affinity prediction reduces wet-lab assay cost by 70%, enabling a 10× increase in candidate throughput at comparable budget. For a mid-size biotech screening 5,000 compounds per campaign, accurate ML-based filtering to the top 200 candidates saves ~$400,000 per screen. Challenges: generalisation to novel protein families (addressed via meta-learning on held-out protein families) and data licencing for PDBbind (institutional access secured)."),
    ]
    for title, desc, biz in hc_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 2. Financial ML (8 proposals) ───────────────────────────────────────
    fin_variants = [
        ("Real-Time Credit Card Fraud Detection with Graph Neural Networks",
         "We model transaction networks as heterogeneous graphs where nodes are cards, merchants, and terminals, and apply GraphSAGE with temporal edge features to detect fraudulent transactions in real time. Training data spans 5 years of anonymised transaction logs (50 M records) from a partner bank. Roles: data engineer (Kafka streaming pipeline), graph ML engineer (GraphSAGE training), risk analyst (labelling schema and threshold policy).",
         "False-negative fraud costs our partner bank ~$120 M annually. A 20% improvement in recall at fixed precision 0.90 recovers ~$24 M/year. Deployment via a sub-50 ms decision engine integrated with the bank's existing fraud scoring layer. Challenges: highly imbalanced labels (~0.1% fraud), concept drift as fraudsters adapt, and graph scalability; addressed via focal loss, CUSUM drift detection, and GraphSAGE's inductive neighbourhood sampling."),
        ("Algorithmic Trading Strategy Optimisation Using Reinforcement Learning",
         "We formulate intraday equity trading as a Markov Decision Process and train a Proximal Policy Optimisation (PPO) agent on 10 years of tick-level S&P 500 data from Refinitiv. State space includes LOB imbalance, VWAP deviation, and sentiment embeddings from FinBERT. Roles: quant researcher (strategy framing), RL engineer (PPO training on GPU cluster), risk officer (drawdown constraints).",
         "Target is a proprietary trading desk managing $200 M AUM. Backtested Sharpe ratio improvement of 0.35 over a momentum baseline translates to ~$3.5 M additional annual risk-adjusted return. Challenges include look-ahead bias (addressed via strict point-in-time data joins), transaction cost modelling (addressed via an AMM-realistic market impact model), and overfitting (addressed via walk-forward validation)."),
        ("SME Credit Risk Scoring Using Alternative Data Sources",
         "We build a gradient-boosted credit risk model for small-business loan applicants using alternative data: bank transaction metadata (cash-flow volatility, payroll regularity), web scraping of business reviews, and accounting software API feeds. A data engineer builds the multi-source ingestion layer; a credit data scientist engineers features and calibrates the model; a compliance officer ensures APRA adherence.",
         "Traditional SME lending relies on tax returns with 12-month lag. Our real-time model enables same-day loan decisions for 80% of applicants at a projected default rate reduction of 18%, translating to ~$6 M in reduced write-offs per $500 M loan book. Challenges: privacy compliance under the Consumer Data Right (CDR) framework, and sparse credit history for new businesses (addressed via cold-start Bayesian priors)."),
        ("Explainable Portfolio Optimisation with Regime-Switching Models",
         "We combine a Hidden Markov Model (HMM) for macro regime detection (risk-on/off/crisis) with a mean-CVaR portfolio optimiser that adjusts asset weights dynamically per regime. Factor signals come from MSCI ESG scores, Fama-French factors, and VIX term structure. Team: quantitative analyst, data engineer (Bloomberg API pipeline), ESG specialist.",
         "A $1 B institutional fund using static mean-variance optimisation has left ~0.4% annual alpha on the table versus a regime-aware strategy in backtests (2003–2023). This translates to ~$4 M additional return per year. APRA's SPS 530 requires explainability of investment decisions; HMM-based regime signals provide a transparent and auditable rationale. Challenges: HMM parameter instability across regimes (addressed via Bayesian HMM with informative priors)."),
        ("Anti-Money-Laundering Transaction Monitoring via Federated Learning",
         "We train a federated GNN across five participating banks without sharing raw customer data, using the LexisNexis federated learning framework. Local models learn transaction graph patterns; a central server aggregates gradients with differential privacy (ε=1.0). Roles: federated ML engineer, compliance data scientist, legal officer (inter-bank data-sharing agreement).",
         "Regulatory fines for AML failures in Australia reached $1.3 B in 2023. A federated cross-bank detection model is expected to surface 25% more shell-company networks than single-bank models. Participation is incentivised through shared AML intelligence. Challenges: heterogeneous graph schemas across banks (addressed via a common ontology negotiated with AUSTRAC), and free-rider model poisoning (addressed via Byzantine-robust aggregation)."),
        ("Insurance Claim Severity Modelling with Attention-Based Neural Networks",
         "We predict claim settlement amounts for motor vehicle insurance using a TabTransformer model on structured claim metadata combined with damage photograph embeddings from a fine-tuned CLIP model. Training data: 800,000 settled claims from IAG's internal systems. Roles: data scientist (model design), computer vision engineer (CLIP fine-tuning), actuary (severity band calibration).",
         "Over-reserving costs IAG ~$40 M annually in tied-up capital; under-reserving creates solvency risk. A 12% reduction in mean absolute prediction error of claim severity releases ~$4.8 M in reserve capital per year. Challenges: rare high-severity claims (addressed via a two-stage model: frequency × severity), and image quality variation across claim submission channels (addressed via adaptive image normalisation)."),
        ("Real-Time FX Spread Prediction Using Order Book Microstructure",
         "We predict EUR/USD bid-ask spread at a 1-second horizon using a Temporal Fusion Transformer trained on Level-2 order book snapshots (top 10 bid/ask levels) from LMAX Digital. Features include LOB slope, trade imbalance, and macro announcement indicators. Team: quant engineer (data pipeline from LMAX API), TFT ML engineer, head of FX trading (business validation).",
         "A 5 bp improvement in spread prediction accuracy enables our FX desk to reduce hedging costs by $800,000 per quarter on a $4 B quarterly notional volume. Challenges: non-stationarity of microstructure at market open/close (addressed by session-aware feature normalisation) and regulatory constraints on co-location infrastructure (addressed by edge-inference at IEX-certified data centres)."),
        ("Mortgage Default Prediction with Fairness Constraints",
         "We train a logistic regression model augmented with adversarial debiasing (Zhang et al., 2018) on Freddie Mac's Single Family Loan-Level Dataset (22 M loans, 1999–2022) to predict 90-day mortgage default while minimising demographic parity gap across racial groups. Roles: ML fairness researcher, data engineer, compliance analyst.",
         "Default prediction improves loan loss provisioning accuracy by ~15%, saving a mid-size lender ~$8 M per year in IFRS 9 Expected Credit Loss reserves. The fairness constraint is legally required under Australia's Equal Credit Opportunity Act equivalent and reduces litigation exposure. Challenges: proxy discrimination via ZIP-code features (addressed via redlining-aware feature exclusion) and calibration across credit score deciles."),
    ]
    for title, desc, biz in fin_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 3. NLP / Text (7 proposals) ─────────────────────────────────────────
    nlp_variants = [
        ("Automated Legal Contract Review Using Large Language Models",
         "We fine-tune LLaMA-3-70B with LoRA adapters on a corpus of 18,000 annotated Australian commercial contracts (NDA, SaaS, employment) to identify non-standard clauses, risky obligations, and regulatory compliance gaps. A legal data engineer curates the annotation schema; an NLP engineer manages LoRA training on 4× A100 GPUs; a solicitor validates extracted clause labels against LexisNexis standards.",
         "Large law firms spend ~$400/hour on junior associate contract review; our system reduces review time by 60%, saving ~$2.4 M annually for a 50-partner firm. Deployment as a Microsoft Word add-in allows seamless adoption. Challenges: hallucination in clause interpretation (addressed via retrieval-augmented generation citing the source clause), jurisdictional variation across states (addressed by a jurisdiction-aware routing layer), and confidentiality (addressed via on-premise deployment)."),
        ("Cross-Lingual Misinformation Detection on Social Media",
         "We build a multilingual claim verification pipeline using mBERT and XLM-RoBERTa fine-tuned on the XFACT dataset (25 languages). A retrieval component fetches relevant Wikipedia passages; a stance detector determines claim support/refute/neutral. Team: NLP data scientist, multilingual data engineer (API connectors to Twitter/Meta CrowdTangle), fact-check partnership manager.",
         "Platform fines under Australia's Online Safety Act for hosting mis/disinformation can reach $550,000/day. Our system flags 78% of cross-lingual misinformation narratives within 15 minutes of posting, enabling timely human review. Challenges: low-resource languages with sparse training data (addressed via cross-lingual transfer learning and data augmentation via back-translation) and adversarial paraphrasing (addressed via semantic similarity-based deduplication)."),
        ("Scientific Literature Summarisation and Trend Discovery",
         "We apply a hierarchical BART model (fine-tuned on the S2ORC corpus) to generate structured summaries of biomedical papers, and use UMAP + HDBSCAN to cluster paper embeddings from BioSentVec into research trend clusters. A data engineer manages the Semantic Scholar API pipeline (500K new papers/month); an NLP engineer fine-tunes BART; a bibliometrics analyst validates cluster quality.",
         "Pharmaceutical R&D teams spend ~20% of researcher time on literature monitoring; our system reduces this to 5%, saving a 100-researcher team ~$2 M/year. A SaaS subscription model at $500/user/month targets 400 enterprise users in Year 1. Challenges: paper access restrictions under journal paywalls (addressed via Unpaywall open-access metadata), and temporal drift in research vocabulary (addressed via monthly BART fine-tuning updates)."),
        ("Customer Support Ticket Routing and Resolution Time Prediction",
         "We train a dual-task transformer (RoBERTa-large) to simultaneously classify support tickets into 48 product categories and predict resolution time (regression). Training data: 2.3 M historical tickets from Salesforce CRM. Features include ticket text, customer tier, and product version metadata. Roles: data engineer (Salesforce API pipeline), NLP engineer, customer operations analyst.",
         "Misrouted tickets increase resolution time by 3× on average. Correct first-pass routing for 85% of tickets saves a 500-agent support centre ~$1.8 M/year in re-routing and re-read overhead. Resolution time predictions enable SLA compliance monitoring and dynamic queue prioritisation. Challenges: distribution shift as new product features introduce novel ticket categories (addressed via online few-shot fine-tuning on labelled tickets within 48 hours of new category detection)."),
        ("Automated Medical Discharge Summary Generation",
         "Using the MIMIC-IV clinical notes corpus, we fine-tune a Longformer-Encoder-Decoder on (admission notes, discharge summary) pairs to generate discharge summaries conditioned on structured EHR fields (diagnoses, procedures, medications). A clinical NLP engineer manages the pipeline; a data scientist evaluates ROUGE-L and BERTScore; a hospitalist evaluates factual accuracy.",
         "Physicians spend 45 minutes per patient writing discharge summaries; our system generates an 80%-complete draft in under 30 seconds for physician review, saving ~$3,600/physician/month. Deployment as an Epic SmartPhrase plugin. Challenges: hallucination of clinical facts (mitigated via constrained decoding that prohibits drug names not in the structured medication list) and de-identification of training data (addressed via PhysioNet data use agreement and i2b2 de-ID pipeline)."),
        ("Automated Scoring of Open-Ended Student Responses in MOOCs",
         "We fine-tune DeBERTa-v3-large on the SemEval 2013 Student Response Analysis dataset augmented with 4,000 human-scored Coursera responses to predict rubric-aligned scores for open-ended questions. A data engineer builds the Coursera LTI grade passback pipeline; an NLP engineer manages training; an instructional designer validates rubric alignment.",
         "Manual grading of 10,000 MOOC student responses costs $8/response; automated scoring at 95% human agreement reduces cost to $0.02/response, saving $79,800 per course offering. Feedback generation from model rationales is expected to improve student pass rates by 8%. Challenges: rubric specificity across question types (addressed via question-conditioned encoding) and domain shift across MOOC subjects (addressed via domain-adaptive pre-training on course transcripts)."),
        ("Real-Time Earnings Call Transcript Analysis for Equity Research",
         "We build a pipeline that ingests live Refinitiv earnings call transcripts, applies FinBERT sentiment scoring at sentence level, extracts forward guidance signals using a custom NER model (trained on 12,000 annotated earnings calls), and generates a structured analyst brief within 5 minutes of call completion. Roles: financial NLP engineer, data engineer (Refinitiv Elektron API), equity analyst (validation).",
         "Equity analysts spend 4 hours post-call synthesising transcripts; our system reduces this to 30 minutes, enabling coverage of 3× more stocks per analyst. For a 20-analyst research team, this creates capacity equivalent to hiring 7 additional analysts (~$1.8 M in salary savings). A Bloomberg Terminal plug-in distribution model targets 5,000 buy-side subscribers at $2,400/year. Challenges: speaker diarisation errors in noisy call recordings (addressed via WhisperX re-alignment) and forward-guidance ambiguity (addressed via calibrated confidence scores)."),
    ]
    for title, desc, biz in nlp_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 4. Computer Vision (6 proposals) ────────────────────────────────────
    cv_variants = [
        ("Automated Defect Inspection on PCB Assembly Lines Using YOLOv9",
         "We deploy a YOLOv9 model trained on 120,000 annotated PCB images (soldering defects, missing components, solder bridges) with a real-time inference pipeline running at 120 FPS on NVIDIA Jetson AGX Orin edge hardware. A computer vision engineer handles data collection via structured-light 3D scanner; an ML engineer manages model training and edge deployment; a quality engineer defines defect taxonomy.",
         "Manual AOI (Automated Optical Inspection) misses ~3% of defects at high throughput; our model reduces escape rate to 0.4%, preventing ~$1.2 M/year in field returns for a mid-size electronics manufacturer processing 500 boards/hour. ROI breakeven at 8 months. Challenges: class imbalance for rare defect types (addressed via targeted synthetic defect augmentation using Stable Diffusion inpainting), and lighting variation across production shifts (addressed via luminance-adaptive normalisation)."),
        ("Satellite Image Change Detection for Urban Growth Monitoring",
         "We apply a Siamese EfficientNet architecture to bi-temporal Sentinel-2 10m imagery pairs to detect urban expansion, deforestation, and illegal construction in peri-urban areas. Training uses the LEVIR-CD dataset augmented with Australian state government aerial imagery. Team: remote sensing engineer, geospatial data scientist, urban planner (domain expert).",
         "Australian state planning departments spend ~$8 M/year on manual satellite image auditing for development control. Our system automates 80% of routine change-flagging, reducing cost to ~$1.6 M/year. Detected unauthorised developments generate fine revenue exceeding $2 M/year. Challenges: cloud-cover gaps in time series (addressed via SAR-optical fusion with Sentinel-1), and geographic domain shift across states (addressed via state-specific calibration layers)."),
        ("Real-Time Crowd Density Estimation for Event Safety Management",
         "We adapt CSRNet (congested scene recognition network) with a multi-scale attention module, trained on UCF_CC_50 and ShanghaiTech Part A datasets augmented with Australian stadium footage from MCG venue managers. Inference runs at 60 FPS on NVIDIA RTX 4090 GPUs installed at 32 stadium camera nodes. Team: computer vision engineer, embedded systems engineer, venue safety officer.",
         "The 2023 MCG stadium tragedy highlight report cited inadequate crowd density monitoring as a contributing factor. Real-time density alerts enable proactive crowd management, reducing injury liability exposure estimated at $5 M/incident. Deployment via a venue management SaaS platform at $80,000/year per stadium; targeting 15 major Australian venues in Year 1. Challenges: occlusion in packed crowds (addressed via depth-aware density estimation using stereo cameras), and privacy (addressed via on-premise inference with no frame storage)."),
        ("Medical Image Segmentation of Tumour Margins for Surgical Planning",
         "We train a nnU-Net (no-new-U-Net) framework on 1,200 contrast-enhanced MRI volumes from The Cancer Imaging Archive (TCIA) to segment glioblastoma tumour margins with sub-centimetre accuracy. A medical image engineer manages DICOM preprocessing; a deep learning engineer conducts nnU-Net hyperparameter search; a neurosurgeon provides tumour boundary annotations and clinical validation.",
         "Accurate tumour margin delineation reduces positive-margin resection rates by 22%, lowering re-operation costs (~$18,000/procedure) and improving 5-year survival by 12%. For 500 glioblastoma surgeries per year across Australian neurosurgical centres, avoided re-operations save ~$2 M. Deployment as a DICOM-integrated second-read tool with TGA SaMD class IIb certification pathway. Challenges: inter-annotator variability (addressed via STAPLE consensus annotation) and tumour heterogeneity across grades (addressed via grade-conditional segmentation heads)."),
        ("Autonomous Inspection Drone Path Planning with Obstacle Detection",
         "We combine a SLAM-based occupancy map built from LiDAR point clouds with a YOLOv8 obstacle detector (trained on 30,000 annotated aerial images) and a PPO-based path planner to enable autonomous infrastructure inspection of high-voltage power towers. An embedded systems engineer handles ROS2 integration; a computer vision engineer trains the object detector; a power utility domain expert defines inspection coverage requirements.",
         "Manual power-tower inspection costs ~$500/tower/year; drone-automated inspection reduces this to $120/tower. For a utility managing 18,000 towers, annual savings are $6.8 M. Safety improvements from removing human workers from high-voltage proximity environments reduce liability by an estimated $1.2 M/year. Challenges: GPS denial near transmission lines (mitigated via visual-inertial odometry), and adverse weather operation (mitigated via wind-gust-resilient PID controller tuning)."),
        ("Retail Shelf Out-of-Stock Detection via In-Store Camera Network",
         "We deploy a multi-view EfficientDet model trained on 200,000 annotated shelf images (including 45 SKU categories) to detect out-of-stock events at 10-minute intervals across a 2,400-camera store network. A data engineer manages edge inference pipeline (NVIDIA Jetson Nano per camera cluster); an ML engineer retrains on new product releases quarterly; a retail operations analyst integrates alerts into the replenishment WMS.",
         "Out-of-stock events cost Australian grocery retailers ~2.4% of potential sales (~$240 M across a 100-store chain). Reducing out-of-stock duration by 55% via proactive replenishment recovers ~$132 M in annual revenue. Challenges: shelf appearance variation across store formats (addressed via store-specific fine-tuning), and SKU visual similarity for private-label products (addressed via triplet loss metric learning on visually similar pairs)."),
    ]
    for title, desc, biz in cv_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 5. Recommendation & Personalisation (5 proposals) ───────────────────
    rec_variants = [
        ("Sequential Session-Based Recommendation for E-Commerce",
         "We implement a GRU4Rec+ model on 3 years of Olist Brazilian e-commerce clickstream logs (4.7 M sessions) to predict the next product a user will view within a session. Session features include dwell time, scroll depth, and add-to-cart signals. Roles: data engineer (Kafka session assembly pipeline), recommender systems engineer (GRU4Rec+ training), A/B testing analyst.",
         "A 12% improvement in next-item prediction CTR on Olist's homepage is projected to generate $3.6 M additional GMV annually. Deployment via a low-latency (<20 ms) Redis-backed feature store and TensorRT-optimised inference service. Challenges: cold-start for new users (addressed via a content-based initialisation using product text embeddings), and popularity bias (addressed via inverse propensity score re-weighting)."),
        ("Knowledge-Graph-Enhanced News Recommendation for Digital Publishers",
         "We enrich user reading histories with Wikidata entity embeddings (extracted via named-entity linking) and train a KGCN (knowledge graph convolutional network) on Microsoft News (MIND dataset, 1 M users) augmented with The Guardian and SMH article graphs. Team: NLP engineer (entity linking), graph ML engineer (KGCN training), editorial strategy analyst.",
         "Personalised news recommendation increases session length by 22% and subscription conversion by 8% in publisher A/B tests. For a digital news publisher with 2 M subscribers at $15/month, an 8% conversion lift on free-tier users (500,000) generates $600,000/month in new subscription revenue. Challenges: filter-bubble effects (mitigated via diversity-aware re-ranking with a 15% exploration rate), and news freshness decay (addressed by exponential time-decay weighting)."),
        ("Music Playlist Continuation Using Transformer-Based Session Models",
         "We train a BERT4Rec-style self-attention model on 6 months of Spotify skip-log data (licensed via the Spotify Academic dataset) to predict the next track given a partial playlist, conditioning on audio features (MFCCs, tempo, key) alongside listening context (time-of-day, device type). Roles: audio ML engineer (feature extraction pipeline using librosa), recommender engineer, UX researcher.",
         "Reducing skip rate by 10% on a 50 M-user platform retains users on-app 8 minutes longer per session, generating 12% additional streaming ad revenue (~$24 M annually for a mid-tier platform). Integration via Spotify Web API partner programme. Challenges: licensing restrictions on audio feature extraction at scale (addressed via Spotify's official audio features endpoint), and cold-start for new releases (addressed via audio-content embedding as a prior)."),
        ("Adaptive Learning Path Recommendation for Corporate Training",
         "We model employee learning as a knowledge tracing problem using DKVMN (Deep Key-Value Memory Networks) on 18 months of LMS interaction logs from a 10,000-employee enterprise. Skill mastery states are updated after each module completion, and a contextual bandit explores optimal next-module recommendations. Team: edtech data scientist, LMS integration engineer, L&D director.",
         "Employees in non-personalised training programmes waste ~35% of learning time on content below their current competency level. Adaptive learning reduces time-to-competency by 28%, equivalent to $4,200/employee/year in recovered productivity for a 10,000-person workforce ($42 M total). SaaS licensing at $180/employee/year. Challenges: sparse interaction logs for infrequent learners (addressed via collaborative filtering with skill-graph priors) and cold-start for new employees (addressed via onboarding assessment-based initialisation)."),
        ("Location-Aware Restaurant Recommendation with Contextual Bandits",
         "We implement a LinUCB contextual bandit on the Yelp Open Dataset (6.9 M reviews, 150,000 businesses) augmented with real-time contextual features: weather, time-of-day, user's current GPS coordinates, and dietary restriction flags. A geospatial data engineer builds the feature store; a bandit-systems engineer implements LinUCB with warm-start from matrix factorisation; a UX designer conducts A/B tests.",
         "Irrelevant restaurant recommendations result in a 40% abandonment rate in food discovery apps. Contextual bandits are projected to reduce abandonment to 22%, increasing order conversion by 18% and GMV per MAU by $4.20. For an app with 3 M MAU, annual GMV lift is $151 M. Challenges: exploration-exploitation trade-off in sparse geographic regions (addressed via cluster-level Thompson sampling), and privacy of location data (addressed via on-device feature computation with only aggregate signals sent to server)."),
    ]
    for title, desc, biz in rec_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 6. Environmental & Climate (5 proposals) ────────────────────────────
    env_variants = [
        ("Sub-Seasonal Rainfall Forecasting Using Ensemble Deep Learning",
         "We ensemble a ConvLSTM model trained on ERA5 reanalysis fields (1940–2023, 0.25° resolution) with a gradient-boosted model on teleconnection indices (SOI, DMI, Niño-3.4) to forecast Australian regional rainfall at 2–6 week lead times. A climate data engineer manages ERA5 bulk download and preprocessing; an ML engineer maintains the ensemble; a Bureau of Meteorology hydrologist validates skill scores.",
         "Accurate 2–6 week rainfall forecasts reduce Australian agricultural losses by an estimated $800 M/year by enabling optimal irrigation scheduling, harvest timing, and livestock management decisions. Commercial licensing to 40,000 farm subscribers at $2,000/year generates $80 M ARR. Challenges: chaotic atmospheric dynamics limiting predictability beyond 2 weeks (addressed via probabilistic ensemble outputs with calibrated uncertainty), and distribution shift under climate change (addressed via transfer learning from CMIP6 climate projections)."),
        ("Air Quality Index Forecasting for Smart City Pollution Alerts",
         "We train a Spatio-Temporal Graph Convolutional Network (ST-GCN) on 5 years of hourly PM2.5, NO2, and O3 sensor readings from 200 stations across Melbourne (EPA Victoria dataset), enriched with traffic volume and meteorological features. Roles: IoT data engineer (real-time sensor API ingestion), geospatial ML engineer (ST-GCN training), EPA policy analyst.",
         "Accurate 24-hour AQI forecasts enable health advisories that reduce outdoor exposure for at-risk populations (estimated 120,000 Melburnians), preventing ~$45 M in healthcare costs annually. The model powers Melbourne City Council's real-time air quality dashboard (SLA: 99.9% uptime, <5-min forecast latency). Challenges: sensor malfunctions causing data gaps (addressed via kriging-based spatial imputation) and non-linear meteorological interactions (addressed via attention-based graph convolution)."),
        ("Wildfire Risk Mapping Using Remote Sensing and Weather Models",
         "We fuse Sentinel-2 vegetation indices (NDVI, NBR), fuel moisture estimates from MODIS, and NWP wind/temperature forecasts in a Random Forest ensemble to produce 48-hour dynamic fire risk maps at 100m resolution across south-east Australia. Team: remote sensing engineer, fire behaviour scientist (CSIRO), data engineer (AWS Lambda-based daily ingestion).",
         "The 2019–20 Black Summer fires caused $103 B in economic damage. Providing rural fire services with 48-hour high-resolution risk maps enables pre-positioning of aerial tankers, projected to reduce suppression costs by 15% (~$120 M nationally). Licensing to state emergency services at $500,000/year per state. Challenges: data latency during smoke-obscured Sentinel-2 overpass periods (addressed via SAR-based vegetation moisture retrieval from Sentinel-1) and model degradation during unprecedented fire conditions (addressed via continual learning with post-fire satellite surveys)."),
        ("Carbon Footprint Estimation from Corporate Supply Chain Data",
         "We develop a multi-tier supply chain emissions model using a Graph Attention Network trained on Exiobase 3.8 global input-output tables and company-specific procurement data to estimate Scope 3 emissions at SKU level. A supply chain data engineer builds ERP integration connectors; a sustainability data scientist trains the GAT; an ESG analyst validates against CDP-reported benchmarks.",
         "Under the TCFD framework, ASX200 companies face mandatory Scope 3 disclosures from FY2025. Our platform reduces emissions estimation cost from $250,000/year (consulting) to $40,000/year SaaS subscription, targeting 200 ASX200 subscribers for $8 M ARR. Challenges: confidential supplier data access (addressed via a secure data enclave architecture with aggregation guarantees), and multi-tier attribution (addressed via probabilistic supply chain Monte Carlo sampling)."),
        ("Optimising Renewable Energy Dispatch with Reinforcement Learning",
         "We train a Twin Delayed Deep Deterministic (TD3) policy gradient agent on the IEEE 118-bus test network augmented with real South Australian AEMO wind/solar trace data to optimise real-time battery dispatch and wind curtailment decisions under price uncertainty. Team: power systems engineer, RL engineer, AEMO market analyst.",
         "Suboptimal battery dispatch in South Australia's 150 MW Hornsdale Power Reserve costs ~$4 M/year in foregone arbitrage revenue and excessive curtailment. Our RL policy recovers an estimated 18% additional arbitrage value ($720,000/year) and reduces curtailment by 12%. Licensing to Australian battery operators at $150,000/installation/year. Challenges: non-stationarity of electricity prices (addressed via opponent modelling of bidding strategies), and safety constraints on battery State of Charge (addressed via constrained RL with Lagrangian multipliers)."),
    ]
    for title, desc, biz in env_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 7. Education Technology (5 proposals) ───────────────────────────────
    edu_variants = [
        ("Early Identification of At-Risk Students Using Clickstream Analytics",
         "We apply a bidirectional LSTM trained on LMS clickstream logs (page views, forum activity, assignment submission timing) from Monash's Moodle platform (50,000 enrolments, 3 academic years) to predict student failure risk 4 weeks before census date. A data engineer builds the Moodle SQL extraction pipeline; an ML engineer trains the biLSTM; a student success advisor co-designs the intervention dashboard.",
         "One student failure costs the institution ~$12,000 in lost tuition and administrative overhead. Identifying 65% of at-risk students 4 weeks before census enables targeted outreach (tutoring, welfare check), projected to retain 30% of identified students — saving ~$2.4 M annually across a 10,000-student faculty. Challenges: data sparsity in early weeks (addressed via a self-supervised pre-training on late-semester data projected backward), and privacy under FERPA equivalents (addressed via differential privacy on individual event logs)."),
        ("Automated Rubric-Aligned Marking for Engineering Design Reports",
         "We fine-tune a DeBERTa-v3 model on 6,000 human-marked engineering design reports from UNSW (annotated at rubric criterion level) to produce criterion-wise scores and justification sentences. An NLP engineer handles the multi-label fine-tuning; a data engineer builds the Canvas LMS integration; a senior lecturer validates marking consistency against historical grade distributions.",
         "Marking 300 engineering design reports per cohort costs $8,000 in tutor time. Automated first-pass marking (human review of flagged cases) reduces cost by 65% to $2,800 per cohort. Student feedback is available within 24 hours instead of 3 weeks, improving satisfaction scores by a projected 0.4 points (5-point scale). Challenges: discipline-specific terminology requiring domain-adapted pre-training (addressed via PubMed + IEEE corpus continued pre-training) and partial credit at sub-criterion level (addressed via span-level regression heads)."),
        ("Detecting Ghostwriting and AI-Generated Submissions in Higher Education",
         "We build a hybrid classifier combining a RoBERTa-based stylometric model (trained on the PAN-2024 authorship verification dataset) and a DetectGPT-style log-probability perturbation test to classify submissions as human-authored, AI-generated, or ghostwritten. Team: NLP security researcher, data engineer (Canvas API), academic integrity officer.",
         "Academic integrity breaches cost universities $50,000–$500,000 per tribunal process. Providing a probabilistic integrity risk score for each submission (rather than binary accusation) enables proportionate follow-up, reducing tribunal caseload by 40% (~$2 M/year for a G8 university) while deterring AI-assisted cheating. Challenges: rapid evolution of LLM outputs making static detectors obsolete (addressed via weekly DetectGPT recalibration against current GPT-4o/Claude outputs), and false-positive risk for non-native English writers (addressed via writer-specific stylometric calibration)."),
        ("Personalised Hint Generation for Mathematics Learning Systems",
         "We fine-tune GPT-4o-mini with supervised RLHF on 12,000 human-authored hints (rated by 50 tutors on helpfulness and correctness) from Khan Academy mathematics to generate step-specific hints. A data scientist manages the RLHF pipeline (PPO with a reward model trained on hint quality ratings); an instructional designer writes the hint rubric; a middle-school maths teacher validates hint educational value.",
         "Irrelevant hints in adaptive learning systems cause 34% of students to disengage from hint sequences. Personalised hints are projected to increase hint acceptance rate by 40% and reduce time-to-correct-answer by 18%, measurable via Khan Academy API A/B testing. Licenced as an API add-on at $0.02/hint to existing adaptive learning platforms (target: 10 M hints/month at Year 2). Challenges: mathematical notation rendering in text-based hint generation (addressed via LaTeX-to-text pipeline) and hallucinated incorrect solution steps (addressed via symbolic verification against CAS-computed step solutions)."),
        ("Predicting Academic Dishonesty from Exam Metadata Patterns",
         "Using anonymised exam metadata (submission timestamps, question-order variability, answer change frequency, keylogger pause patterns) from 40,000 remote online exams on Inspera, we train a Random Forest model to flag anomalous behaviour consistent with collusion or exam material leakage. Roles: data scientist, Inspera integration engineer, academic integrity director.",
         "Post-hoc plagiarism investigation costs $3,000 per case; our model prioritises the top 5% highest-risk submissions for review, concentrating investigation effort and reducing the cost per confirmed breach from $3,000 to $750. For 2,000 suspected cases annually, savings are $4.5 M. Challenges: behavioural variation among test-anxious honest students (addressed via multi-threshold calibration with institution-specific false-positive budgets), and adversarial students who mimic normal patterns (addressed via distributional outlier scoring rather than rule-based flags)."),
    ]
    for title, desc, biz in edu_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 8. Supply Chain & Logistics (5 proposals) ────────────────────────────
    sc_variants = [
        ("Demand Forecasting for FMCG Distribution Using Temporal Fusion Transformers",
         "We train a Temporal Fusion Transformer (TFT) on 4 years of weekly SKU-level sales data (8,000 SKUs × 200 distribution centres) from Woolworths augmented with promotional calendar, public holiday, and weather features. A data engineer builds the Snowflake data warehouse pipeline; an ML forecasting engineer trains TFT on a distributed Ray cluster; a supply chain analyst defines business KPIs.",
         "A 15% reduction in forecast MAPE across 8,000 SKUs reduces Woolworths' inventory holding cost by ~$18 M/year and out-of-stock events by 22%. Deployment as an API service replacing the existing SAS-based system. Challenges: promotional lift estimation for novel promotions (addressed via a separate promotion-response XGBoost model whose output is an additional TFT covariate), and inter-SKU substitution effects (addressed via cross-SKU graph features derived from co-purchase patterns)."),
        ("Dynamic Vehicle Routing Optimisation for Last-Mile Delivery",
         "We frame last-mile delivery as a time-windows Vehicle Routing Problem (VRPTW) and solve it with a Pointer Network (Ptr-Net) trained via REINFORCE on synthetically generated instances, then fine-tuned on historical delivery records from an Australian courier network (1.2 M deliveries/year). A combinatorial optimisation engineer trains the Ptr-Net; a routing data scientist evaluates on historical instances; a logistics operations director validates route feasibility.",
         "A 12% reduction in total route distance for 200 delivery vans reduces fuel costs by ~$1.4 M and CO2 emissions by 480 tonnes/year. The system replaces a legacy hand-crafted heuristic and re-optimises in real time as new orders arrive. Challenges: traffic-conditional travel time estimation (addressed via Google Distance Matrix API with time-of-day lookups), and driver preference constraints (addressed via soft penalties in the reward function)."),
        ("Supplier Risk Scoring Using News Sentiment and Financial Signals",
         "We build a real-time supplier risk dashboard combining: (1) daily sentiment scores from a FinBERT model applied to ~2,000 supplier-name-mention news articles, (2) financial health metrics from Dun & Bradstreet, and (3) geopolitical risk indices for supplier country exposures. Team: NLP data engineer, financial data scientist, procurement director.",
         "A single tier-1 supplier disruption costs a mid-size Australian manufacturer ~$5 M in lost production. Early risk signals enable pre-emptive dual-sourcing; for a portfolio of 300 suppliers, preventing one major disruption per year pays for the system 10×. SaaS pricing: $120,000/year targeting 50 enterprise procurement teams. Challenges: news coverage gaps for private SME suppliers (addressed via graph-based risk propagation from known public suppliers), and entity disambiguation in news (addressed via GATOR entity linking fine-tuned on supplier names)."),
        ("Port Container Dwell Time Prediction to Reduce Terminal Congestion",
         "Using gate-in/gate-out timestamps, vessel schedule data, and customs clearance event logs from Port of Melbourne (5-year dataset, 2.8 M container events), we train a Gradient Boosting model to predict container dwell time 48 hours in advance, enabling proactive slot allocation. Team: maritime data engineer, logistics ML scientist, terminal operations manager.",
         "Average container dwell time at Port of Melbourne is 4.2 days versus a global benchmark of 2.8 days, costing importers ~$80/container/day. Reducing average dwell by 0.8 days saves importers $56/container; at 1.4 M TEU/year, aggregate savings are $78 M. The port authority monetises the prediction service via priority-slot reservation fees. Challenges: vessel schedule unreliability (addressed via real-time AIS vessel tracking as a dynamic feature) and customs clearance time uncertainty (addressed via a probabilistic output with 80% prediction interval)."),
        ("Cold Chain Integrity Monitoring Using IoT Sensor Fusion",
         "We deploy an ensemble of Isolation Forest and LSTM Autoencoder models on temperature, humidity, and door-open event streams from 4,000 IoT sensors across a pharmaceutical cold-chain network (ColdChain Co., 38 distribution nodes). A data engineer builds the MQTT-to-InfluxDB ingestion pipeline; an ML engineer trains the anomaly detector; a regulatory affairs officer ensures TGA cold-chain compliance documentation.",
         "A single cold-chain breach in pharmaceutical distribution can result in batch spoilage costing $500,000 and TGA regulatory action. Real-time anomaly alerting (< 2-minute detection latency) enables intervention before product temperature exceeds limit. Projected annual batch-spoilage prevention: 12 events × $500,000 = $6 M. Monthly SaaS fee: $2,000/node × 38 nodes = $76,000/month. Challenges: sensor calibration drift (addressed via median-of-medians normalisation per sensor cohort) and intermittent MQTT connectivity in refrigerated trucks (addressed via edge buffering with store-and-forward)."),
    ]
    for title, desc, biz in sc_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 9. Smart City & Urban (5 proposals) ─────────────────────────────────
    sc2_variants = [
        ("Congestion-Aware Traffic Signal Control via Multi-Agent RL",
         "We train a MAPPO (Multi-Agent PPO) system where each signalised intersection in a 40-intersection network is an independent agent, sharing a centralised critic. Simulation environment: SUMO (Simulation of Urban Mobility) calibrated on Melbourne's inner-city loop using VicRoads SCATS detector data. Team: traffic simulation engineer, MARL engineer, VicRoads signal operations analyst.",
         "Inner-Melbourne traffic congestion costs the economy $1.9 B/year in lost productivity. A 15% reduction in average vehicle delay on the calibrated 40-intersection network reduces commuter time losses by $285 M/year citywide. VicRoads licences adaptive signal algorithms at $2 M/year; our system is expected to displace two legacy vendors. Challenges: sim-to-real transfer gap (addressed via domain randomisation and iterative real-world fine-tuning with shadow deployment), and safety constraints on signal phase timing (addressed via constrained MARL with phase duration hard limits)."),
        ("Crime Hotspot Prediction for Proactive Policing Resource Allocation",
         "Using Victoria Police CAD incident records (10 years, 2 M events) combined with environmental features (lighting levels from street lamp APIs, bar density, unemployment statistics from ABS), we train a Spatio-Temporal DBSCAN hotspot model for 7-day crime forecasting at 250m grid resolution. Team: crime data scientist, geospatial data engineer, Victoria Police intelligence analyst.",
         "Directed patrols to predicted hotspots reduce property crime by 12% in randomised controlled trials (Telep et al., 2014 meta-analysis). For Melbourne's ~40,000 property crimes/year, a 12% reduction saves victims $64 M in losses and reduces police investigation costs by $4.8 M. Fairness audit by an independent ethicist ensures no discriminatory targeting of ethnic neighbourhoods. Challenges: under-reporting bias in incident data (addressed via auxiliary predictors from crime survey data), and patrol displacement effect (addressed via a spatial equilibrium adjustment in model training)."),
        ("Public Transport Demand Forecasting for Dynamic Fleet Allocation",
         "We train a Graph WaveNet model on 3 years of Myki tap-on/tap-off data (Melbourne's smartcard system, 600 M annual trips) to forecast passenger loads at route-segment level at 15-minute granularity, enabling dynamic bus fleet reallocation. Roles: public transport data engineer (PTV API integration), spatial ML engineer, PTV network planning analyst.",
         "Under-utilised bus routes tie up ~15% of PTV's $1.8 B annual fleet budget. Dynamic reallocation based on real-time demand forecasts is projected to improve seat-km utilisation by 18%, releasing $270 M in fleet efficiency. Real-time passenger load predictions also feed PTV's planned app feature for live capacity visibility. Challenges: school-holiday and event-driven demand spikes (addressed via exogenous event features from a public events API) and GPS delays in real-time Myki feed (addressed via a 5-minute predictive forward-fill)."),
        ("Urban Heat Island Mitigation via Tree Canopy Optimisation",
         "We build a spatial optimisation model combining a CNN-based urban heat island (UHI) temperature predictor (trained on Landsat-8 surface temperature and LiDAR tree-canopy data across 6 Australian cities) with a set-cover optimisation algorithm to recommend tree-planting locations that maximally reduce peak summer temperatures. Team: geospatial data scientist, urban ecology expert, city council landscape architect.",
         "Urban heat islands increase mortality risk by 3.2× during heatwaves in Australian cities. Optimal tree placement for a $10 M tree-planting budget is projected to reduce peak UHI intensity by 1.8°C in targeted areas, preventing an estimated 45 heat-related deaths/year (statistical value: $180 M). Methodology is licensed to 12 Australian city councils at $80,000/year. Challenges: LiDAR data currency (resolved via annual AHN-style survey contracts), and tree species growth model uncertainty (addressed via probabilistic shade projection with 5-year growth curves)."),
        ("Flood Inundation Prediction for Stormwater Infrastructure Planning",
         "We combine a physics-informed neural network (PINN) with a U-Net trained on 20-year Brisbane River flood event records and LiDAR-derived DEM data to predict 24-hour flood inundation extent at 10m resolution. A hydrological engineer provides physics-based boundary conditions; a geospatial ML engineer trains the PINN + U-Net hybrid; a Brisbane City Council drainage planner validates against 2011 and 2022 historical flood extents.",
         "The 2022 Brisbane floods caused $2.5 B in insured losses. Accurate 24-hour predictions enable targeted sandbagging, property evacuation, and infrastructure protection, reducing insured losses by an estimated 20% ($500 M). Bureau of Meteorology licences the system at $1.5 M/year for national deployment across 12 major river basins. Challenges: uncertainty in rainfall input forecasts (addressed via ensemble NWP inputs with Monte Carlo inundation sampling) and computational cost of PINN training (addressed via transfer learning from pre-trained PINNs on synthetic flood scenarios)."),
    ]
    for title, desc, biz in sc2_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 10. Manufacturing / IoT (5 proposals) ────────────────────────────────
    mfg_variants = [
        ("Predictive Maintenance for CNC Machining Centres via Vibration Analysis",
         "We train a 1D-CNN on high-frequency (25 kHz) spindle vibration signals from 80 CNC machining centres (Siemens 840D controllers) to classify tool wear state (new/medium/worn/broken) with a lead time of 4–6 hours. A data engineer builds the OPC-UA real-time data bridge; an ML engineer handles model training and deployment on edge Raspberry Pi 4 clusters; a mechanical engineer provides tool wear ground truth from CMM measurements.",
         "Unplanned tool breakage causes $15,000 in downtime and scrap per incident; our model eliminates 80% of unplanned breakages, saving ~$1.2 M/year across an 80-machine floor. Planned tool replacement at the right time also reduces over-conservative early replacement by 30%, saving $400,000/year in tooling costs. Challenges: varying workpiece materials causing vibration signature shift (addressed via material-conditional normalisation), and sensor drift over 12-month deployments (addressed via a self-supervised sensor recalibration routine)."),
        ("Quality Control Defect Root-Cause Analysis in Steel Rolling Mills",
         "Using 5-second interval process parameter logs (roll force, tension, speed, coolant temperature) from a BlueScope Steel cold rolling mill (3-year dataset, 200 parameters), we train an LSTM encoder + attention mechanism to predict surface defect occurrence and attribute causality to upstream process variables via SHAP temporal explanations. Team: process data engineer, ML engineer, metallurgist.",
         "Surface defects in cold-rolled steel cause 2.5% scrap rate; reducing this by 0.8 percentage points saves BlueScope ~$8 M/year in scrap and customer penalties. Root-cause attribution enables targeted process setpoint adjustments, replacing 2 weeks of manual statistical process control investigation per incident with real-time diagnosis. Challenges: correlated high-dimensional process variables causing SHAP attribution instability (addressed via hierarchical feature grouping) and non-stationarity from roll wear (addressed via rolling-horizon retraining every 2 weeks)."),
        ("Energy Optimisation in Semiconductor Fab Using Digital Twin Simulation",
         "We build a digital twin of a 300mm semiconductor fab using the SimPy discrete-event simulation framework calibrated on 18-month tool utilisation and energy consumption logs from Samsung Austin Fab. A Bayesian optimisation loop (BoTorch) searches fab scheduling parameters to minimise kWh/wafer. Roles: semiconductor process engineer, simulation engineer, energy data scientist.",
         "Semiconductor fabs consume 100 MW continuously; a 5% energy reduction for a fab with $80 M/year energy costs saves $4 M annually. Carbon credit value adds another $600,000/year under Australia's ERF. Simulation-based optimisation avoids costly physical experiments on a $5 B production facility. Challenges: simulation fidelity for stochastic tool downtime (addressed via empirically calibrated failure rate distributions from SECS/GEM data) and optimisation in 500-dimensional parameter space (addressed via multi-fidelity BO with low-fidelity simulation warm-starts)."),
        ("Automated Visual Inspection of Pharmaceutical Tablet Coatings",
         "We train a DenseNet-201 model on 95,000 annotated tablet images (coating defects: chips, cracks, picking, twinning) captured under structured illumination in a GMP-compliant inspection station. A computer vision engineer designs the high-throughput imaging rig (180 tablets/min); an ML engineer trains DenseNet-201 with mixup augmentation; a QA officer validates against FDA 21 CFR Part 11 audit trail requirements.",
         "Manual visual inspection at 180 tablets/min misses 4% of defective tablets; automated inspection reduces escape rate to 0.3%, eliminating batch recall risk (one recall costs ~$8 M in direct costs plus brand damage). TGA GMP compliance requires 100% inspection for solid-dose pharmaceuticals; our system enables inline 100% inspection replacing end-of-line sampling. Challenges: subtle coating colour variation across production campaigns (addressed via campaign-adaptive histogram normalisation) and regulatory validation under USP <1> guidance (addressed via Installation Qualification / Operational Qualification documentation package)."),
        ("Predictive Scheduling for Semiconductor Etch Equipment Maintenance",
         "We model etch chamber degradation as a time-to-event problem using a DeepHit survival model trained on 4 years of in-situ optical emission spectroscopy (OES) sensor traces and RF match network impedance logs from 24 Applied Materials Centura systems. A fab data engineer builds the FTP-to-Parquet pipeline; an ML engineer trains DeepHit; a process integration engineer defines PM trigger criteria.",
         "Unscheduled etch chamber downtime causes $180,000/hour in lost wafer starts. Our model issues maintenance alerts 48–72 hours in advance for 75% of impending failures, reducing unscheduled downtime by 60% ($2.1 M/year per fab). Planned PM windows are shortened by 20% via targeted replacement of predicted-failed components only (avoiding full kit replacement), saving $1.2 M/year in spare parts. Challenges: OES signal drift requiring sensor health monitoring (addressed via univariate control charts on baseline OES peaks) and multi-chamber generalisation (addressed via transfer learning with chamber-specific fine-tuning)."),
    ]
    for title, desc, biz in mfg_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 11. Agriculture & Environment (4 proposals) ──────────────────────────
    agr_variants = [
        ("Precision Irrigation Scheduling via Soil Moisture Prediction",
         "We predict soil volumetric water content 24 hours in advance using a hybrid LSTM-Gaussian Process model trained on 3 years of FieldClimate soil moisture sensor data (20 farms, 5 soil depths) augmented with NWP rainfall forecasts and satellite-derived evapotranspiration estimates from MODIS ET products. Team: soil scientist, ML engineer, agronomy consultant.",
         "Over-irrigation wastes 35% of applied water in Australian cotton farming. Optimal irrigation scheduling is projected to reduce water application by 28% per hectare while maintaining yield parity, saving a 500-ha cotton farm $140,000/year in water entitlement costs. SaaS platform at $2,500/farm/season targets 1,000 farms for $2.5 M ARR. Challenges: sensor failure in remote paddocks (addressed via physics-based water balance model as a fallback), and soil heterogeneity within paddock (addressed via spatial kriging interpolation from multi-depth sensors)."),
        ("Crop Disease Early Detection from UAV Multispectral Imagery",
         "We train a lightweight MobileNetV3 model on 45,000 UAV multispectral images (RGB + NIR + RedEdge) annotated for 12 crop disease classes across wheat, canola, and chickpea, optimised for deployment on DJI Mavic 3 Multispectral onboard compute. A UAV data engineer manages image collection protocols; a plant pathologist annotates disease severity; an ML engineer trains the edge-deployable model.",
         "Crop diseases cause 10–40% yield losses when undetected; early aerial detection enables targeted fungicide application, reducing chemical use by 60% and yield losses by 25%. For a 2,000-ha wheat farm with $1.2 M revenue at risk, projected savings are $300,000/year. Service model: $8/ha survey fee via certified agronomist-drone operators. Challenges: class imbalance for rare diseases (addressed via generative data augmentation using a domain-adapted DCGAN), and lighting variation across flight times (addressed via empirical line radiometric calibration)."),
        ("Automated Livestock Body Condition Scoring via 3D Point Cloud Analysis",
         "We process LiDAR point clouds captured by overhead scanners in cattle laneways to extract body condition score (BCS, 1–9 scale) using a PointNet++ model trained on 12,000 manually scored 3D scans from JBS Australia feedlots. Roles: computer vision engineer (point cloud preprocessing), ML engineer (PointNet++ training), veterinary scientist (BCS validation).",
         "Manual BCS assessments cost $15/head/year across a 10,000-head feedlot; automated scoring reduces cost to $2/head/year ($130,000 saving) while enabling weekly instead of monthly assessments, improving feed conversion efficiency by 8% (valued at $640,000/year per feedlot). Challenges: animal movement causing incomplete point clouds (addressed via multi-frame fusion from 3 consecutive laneway passes), and breed-specific body morphology variation (addressed via breed-conditional scoring heads)."),
        ("Satellite-Based Crop Type Mapping for Agricultural Policy Planning",
         "We train a multi-temporal Random Forest classifier on 3-year Sentinel-2 time-series (monthly composites) and SRTM DEM data, using the AusCover ground-truth vegetation survey as training labels, to produce annual 10m-resolution crop type maps across Australia's grain belt. A remote sensing engineer manages data pre-processing; a GIS data scientist trains and evaluates the classifier; an ABARES analyst validates against NPI data.",
         "ABARES spends $4 M annually on crop area estimation surveys with 6-month lag. Our satellite-based system produces estimates within 3 weeks of season end at $600,000/year, saving $3.4 M annually while improving spatial resolution from LGA-level to 10m. Export as GeoTIFF to ABARES DSS. Challenges: cloud contamination in northern Australian wet season (addressed via phenology-based gap filling), and mixed-pixel confusion in small-field regions (addressed via sub-pixel soft classification using Dirichlet outputs)."),
    ]
    for title, desc, biz in agr_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 12. Retail & E-Commerce (5 proposals) ────────────────────────────────
    retail_variants = [
        ("Dynamic Pricing Optimisation for Hotel Revenue Management",
         "We train a Thompson Sampling contextual bandit on 4 years of Expedia hotel booking logs augmented with competitor pricing scraped from OTA APIs (Booking.com, Agoda) to set room rates that maximise RevPAR. Features include occupancy rate, days-to-arrival, competitor prices, and local event calendar. Team: revenue management data scientist, pricing engineer, hotel operations director.",
         "A 6% RevPAR improvement for a 250-room 4-star hotel generates ~$900,000 additional annual revenue. Deployment as an API integration with Opera PMS (property management system). Challenges: competitor price scraping legality (addressed by terms-of-service-compliant scraping via SerpAPI), and demand elasticity estimation from observational pricing data (addressed via instrumental variable regression using competitor prices as instruments)."),
        ("Return Rate Reduction via Customer Purchase Intention Modelling",
         "We model e-commerce return risk at the product-customer-interaction level using a gradient-boosted classifier on 2 years of Zalando EU transaction data (15 M transactions, 8% return rate). Features: product category, image-to-reality gap score from review images, customer historical return rate, and size-fit score from brand size tables. Team: data scientist, computer vision engineer, returns logistics analyst.",
         "Each return costs Zalando ~€12 in logistics; reducing the return rate by 2 percentage points on 15 M transactions saves ~€3.6 M/year. Proactive pre-purchase alerts ('Customers with your purchase history often return this size; consider sizing up') reduce returns without suppressing sales. Challenges: selection bias in the training data since high-risk products are already deprioritised by the recommendation system (addressed via inverse propensity score weighting)."),
        ("Personalised Email Campaign Timing Optimisation",
         "We estimate the optimal send-time for individual subscribers using a survival model (CoxPH) trained on 18 months of Mailchimp campaign log data (500 M send-open pairs across 10,000 brands). Features include subscriber historical open-hour distribution, device type, and email category. Team: data engineer (Mailchimp API), ML engineer, email marketing strategist.",
         "Send-time personalisation increases open rates by 22% over batch send (Mailchimp internal benchmark). For a retailer with 1 M subscribers generating $0.15 revenue per opened email, a 22% open-rate lift generates $330,000 additional revenue per campaign. Licenced as a Mailchimp premium add-on at $2,000/month. Challenges: privacy under GDPR's right-to-deletion (addressed via subscriber-level model weight sharding enabling targeted deletion) and cold-start for new subscribers (addressed via cohort-based priors from demographic similar subscribers)."),
        ("Real-Time Inventory Replenishment with Reinforcement Learning",
         "We train a PPO agent in a discrete-event simulation of a 5-echelon FMCG supply chain (calibrated on 3 years of Coles distribution centre data) to decide order quantities and timing, directly optimising a composite reward of service level, holding cost, and stockout penalty. A supply chain simulation engineer uses AnyLogic for environment calibration; a reinforcement learning engineer trains PPO; a category manager defines reward weights.",
         "Reducing average inventory holding by 12% while maintaining 98.5% service level releases $4.8 M in working capital for Coles' dry grocery category. Comparison against SAP's standard min-max replenishment policy shows a 9% reduction in total cost of inventory. Challenges: sim-to-real transfer due to demand seasonality not fully captured in simulation (addressed via simulation recalibration every quarter from recent actuals) and multi-echelon state space explosion (addressed via hierarchical RL with level-specific sub-policies)."),
        ("Product Bundling Recommendation via Association Rule Mining and RL",
         "We first mine high-confidence association rules from 5 years of Bunnings hardware transaction logs (4 M transactions) to build a product affinity graph, then train a DQN agent to select bundles dynamically based on cart composition, customer segment, and margin targets. Team: data engineer (POS transaction ETL), ML engineer, category management analyst.",
         "Cross-selling via intelligent bundling increases average basket size by 8% in A/B tests. For Bunnings' $17 B revenue base, an 8% basket-size lift on 30% of transactions adds ~$408 M in annual revenue. Challenges: sparsity of product pairs in long-tail SKUs (addressed via graph embedding imputation of affinity scores) and bundle margin constraints (addressed via constrained DQN with a hard margin floor in the reward shaping)."),
    ]
    for title, desc, biz in retail_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 13. Bioinformatics & Genomics (4 proposals) ──────────────────────────
    bio_variants = [
        ("Variant Pathogenicity Prediction Using Transformer Language Models",
         "We fine-tune ESM-2 (Meta's 650 M-parameter protein language model) on ClinVar's curated variant-to-pathogenicity labels (240,000 variants) to predict the clinical significance of novel missense variants without structural or functional assays. A bioinformatics data engineer manages VCF parsing and UniProt sequence retrieval; an ML engineer runs ESM-2 fine-tuning on 8× A100 GPUs; a clinical geneticist validates predictions against literature-curated gold standard variants.",
         "Clinical genome sequencing produces ~3 M candidate variants per patient; manual review by clinical geneticists costs ~$2,000/case. Automated pre-filtering to the top 50 candidates reduces review time by 80%, saving ~$1,600/case. For a genomics lab processing 5,000 cases/year, savings are $8 M. Challenges: class imbalance (clinically significant variants are rare), addressed via focal loss; and distribution shift across ethnic populations, addressed via population-stratified fine-tuning."),
        ("Single-Cell RNA-Seq Cell Type Annotation via Graph Neural Networks",
         "We build a graph where nodes are single cells (features: gene expression PCA embeddings) and edges connect cells with high kNN-similarity, then train a GraphSAGE node classifier on annotated reference atlases (Human Cell Atlas, 1.2 M cells) to auto-annotate novel scRNA-seq datasets. A computational biologist manages Scanpy preprocessing; an ML engineer trains GraphSAGE; a cell biologist validates annotations against known marker gene expression.",
         "Manual cell type annotation by domain experts costs ~$8,000 per dataset (4–6 expert-hours); automated annotation reduces this to $50/dataset (compute cost), enabling annotation of 10× more datasets per research budget. For a genomics CRO processing 200 datasets/year, savings are $1.6 M. Deployment as a Seurat/Scanpy plugin. Challenges: batch effects across sequencing platforms (addressed via Harmony integration before graph construction) and novel cell type discovery (addressed via out-of-distribution detection triggering a human-review flag)."),
        ("Microbiome Composition Prediction from Dietary Survey Data",
         "Using the American Gut Project dataset (11,000 participants, 16S rRNA microbiome profiles linked to dietary surveys), we train a multi-label regression model (XGBoost with SHAP feature attribution) to predict microbiome compositional features from dietary patterns. A bioinformatics data scientist handles OTU table preprocessing with QIIME2; an ML engineer trains and interprets the XGBoost model; a nutritional scientist validates dietary-microbiome relationships against published literature.",
         "Personalised nutrition advice grounded in individual microbiome composition is a $4.7 B market (2023). Our model enables dietary recommendation apps to provide microbiome-informed meal suggestions without costly microbiome sequencing ($250/test vs $0 inference cost). B2B licencing to 3 nutrition app companies at $500,000/year. Challenges: compositional nature of microbiome data requiring log-ratio transformation (addressed via isometric log-ratio encoding), and confounding by antibiotics and probiotics (addressed via feature-based covariate adjustment)."),
        ("Gene Expression Signature Discovery for Cancer Subtype Classification",
         "We apply a variational autoencoder to TCGA bulk RNA-seq data (10,000 tumour samples, 33 cancer types) to learn a latent representation of transcriptomic states, then train a Random Forest on latent embeddings to classify cancer subtypes and identify gene expression signatures driving each subtype. A bioinformatics engineer manages TCGA download and DESeq2 normalisation; an ML engineer trains the VAE; an oncologist validates signatures against published subtype markers.",
         "Incorrect cancer subtype classification leads to suboptimal treatment selection; improving subtype accuracy by 8% (from 88% to 96%) is projected to improve treatment response rates by 12% for 2,000 misclassified patients/year in Australia. The gene signature panel can be commercialised as a companion diagnostic panel (FDA/TGA pathway). Challenges: batch effects across TCGA sequencing centres (addressed via ComBat-seq harmonisation) and interpretability of VAE latent dimensions (addressed via pathway enrichment analysis of top genes per latent dimension)."),
    ]
    for title, desc, biz in bio_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 14. Autonomous Systems & Robotics (4 proposals) ─────────────────────
    auto_variants = [
        ("LiDAR-Based 3D Object Detection for Autonomous Warehousing",
         "We train a PointPillars model on the Waymo Open Dataset augmented with synthetic LiDAR scans generated by CARLA simulator for warehouse environments to detect forklifts, pallets, and pedestrians in real time at 20 Hz. An embedded systems engineer deploys the model on NVIDIA Orin; a 3D perception ML engineer manages training; a warehouse safety officer defines detection confidence thresholds.",
         "Autonomous forklift collisions cost Australian warehouses ~$250,000/incident (equipment damage, injury liability, downtime). Deploying reliable 3D detection on 50 forklifts prevents an estimated 8 incidents/year ($2 M saved). System cost: $15,000/forklift hardware + $2,000/year software licence. Challenges: point cloud density variation at different forklift speeds (addressed via pillar voxel resolution adaptive to speed), and reflective pallet wrap causing false echoes (addressed via intensity-filtered outlier removal)."),
        ("Sim-to-Real Transfer for Robotic Arm Grasping via Domain Randomisation",
         "We train a SAC (Soft Actor-Critic) grasp policy in PyBullet simulation with domain randomisation over object geometry, surface reflectance, and camera noise, then transfer to a Universal Robots UR5 arm with an Intel RealSense D435 depth camera in a packaging line application. A robotics engineer designs the policy architecture; an ML engineer implements domain randomisation; a production engineer defines grasp success criteria.",
         "Manual packing of irregularly shaped items (cosmetics, fresh produce) costs ~$15/hour/worker; robotic packing at $3/hour after amortisation saves $12/hour. For a 20-packer line running 2 shifts, annual savings are $876,000. Sim-to-real transfer eliminates the $200,000 cost of collecting real-world training data. Challenges: object pose estimation errors from depth noise (addressed via RGB-D fusion with uncertainty-aware grasping) and safety interlocking with the production conveyor (addressed via a hardware emergency stop triggered by anomaly detection in the force-torque sensor)."),
        ("Multi-UAV Coordination for Search and Rescue via MARL",
         "We train a QMIX multi-agent reinforcement learning system where each UAV is an agent coordinating search patterns across a disaster zone. Simulation: StarCraft II Multi-Agent Challenge environment modified for aerial search with occlusion-aware target detection. Team: MARL engineer, UAV embedded systems engineer, emergency management specialist.",
         "A coordinated 4-UAV search of a 10 km² flood zone takes 45 minutes versus 3 hours for uncoordinated single-UAV sweeps. For Australia's 24-hour national search and rescue operations (1,200 incidents/year involving aerial search), a 60% reduction in search time saves an estimated 15 lives/year (statistical value $90 M) and reduces fuel costs by $1.2 M/year. Challenges: communication bandwidth limits between UAVs in remote areas (addressed via bandwidth-constrained QMIX with local observation windows), and GPS denial in canyon environments (addressed via visual odometry via ORB-SLAM3)."),
        ("Autonomous Weed Detection and Spot-Spraying via Agricultural UGV",
         "We deploy a fine-tuned RT-DETR transformer on an autonomous ground vehicle (Burro UGV) processing 4K RGB images at 30 FPS to detect 12 weed species in row crops and trigger precision herbicide application from a 10-nozzle boom with cm-level targeting accuracy. A computer vision engineer trains RT-DETR on the DeepWeeds dataset augmented with farm-specific imagery; an embedded engineer deploys on Jetson Xavier NX; an agronomist defines weed density thresholds.",
         "Broadcast herbicide application costs $180/ha and treats the entire field; spot-spraying reduces herbicide volume by 70%, saving $126/ha in chemicals and reducing environmental run-off. For a 2,000-ha broadacre farm, annual savings are $252,000. Challenges: weed detection in dense canopy occlusion (addressed via multi-angle image fusion from 3 boom-mounted cameras), and herbicide resistance adaptation (addressed via CRISPR-aware weed taxonomy updates to the detection model)."),
    ]
    for title, desc, biz in auto_variants:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    # ── 15. Remaining high proposals (25 items) to reach exactly 107 ──────────
    remaining_high = [
        ("Satellite-Based Maritime Vessel Tracking for Illegal Fishing Detection",
         "We fuse AIS transponder data with Sentinel-1 SAR vessel detections (via a CNN trained on the xView3 maritime dataset) to identify 'dark vessels' — ships that disable their AIS to conceal illegal fishing activity. A maritime data engineer builds the AIS-SAR temporal fusion pipeline; an ML engineer trains the SAR vessel detector; a fisheries compliance officer defines alert thresholds. Analysis covers 10 M km² of Australian EEZ.",
         "Illegal, unreported, and unregulated (IUU) fishing costs Australian fisheries ~$260 M/year. Detecting 60% of dark vessel activity enables AFMA enforcement action expected to recover $156 M/year in fish stocks. Licencing to AFMA and Pacific island fisheries authorities at $2 M/year. Challenges: SAR resolution insufficient to distinguish vessel type at low incidence angles (addressed via multi-polarisation feature fusion) and AIS spoofing by sophisticated vessels (addressed via trajectory physics-consistency scoring)."),
        ("Predictive Policing Resource Optimisation via Hierarchical Forecasting",
         "We build a hierarchical forecasting system (top-down reconciliation using MinT shrinkage) for Queensland Police Service that decomposes state-level crime forecasts into district/patrol-area forecasts, enabling optimal shift scheduling and patrol allocation. A policing data scientist trains Prophet-based base forecasters; a hierarchical ML engineer applies MinT reconciliation; a police district commander validates patrol recommendations.",
         "Inefficient patrol scheduling wastes ~18% of officer shift time on low-risk periods. Demand-aligned scheduling recovers 850 officer-hours per week per district, worth $1.7 M/year. Fairer workload distribution across shifts also reduces officer overtime by 12% ($600,000/year). Independent fairness audit ensures no systematic over-policing of marginalised communities. Challenges: crime reporting lag (addressed via near-real-time CAD feed integration), and geopolitical events causing demand spikes (addressed via a manual override interface for district commanders)."),
        ("Knowledge Distillation for On-Device Sentiment Analysis in Wearables",
         "We distil a DistilBERT-base sentiment classifier into a 2 MB TinyBERT model quantised to INT8 for on-device inference on a Fitbit Sense 2, enabling passive sentiment monitoring from voice snippet transcriptions without cloud transmission. An NLP engineer manages the distillation pipeline; an embedded ML engineer handles INT8 quantisation with TensorFlow Lite; a privacy legal officer validates the on-device-only data processing architecture.",
         "Mental health apps that require cloud processing face GDPR data transfer restrictions reducing market size by 60% in EU. On-device inference enables deployment to all EU markets, tripling addressable market to 45 M users. Subscription pricing at $8/month generates $432 M ARR potential. Challenges: INT8 accuracy drop vs FP32 (addressed via QAT — quantisation-aware training — recovering 99.2% of FP32 accuracy) and limited device memory for vocabulary embedding tables (addressed via vocabulary pruning to the 10,000 most common sentiment-bearing tokens)."),
        ("Cybersecurity Intrusion Detection via Federated Anomaly Detection",
         "We train a federated LSTM autoencoder across 12 enterprise networks (each contributing local network flow features from Zeek/Bro logs) with SecureAgg gradient aggregation to detect novel intrusion patterns without centralising sensitive traffic data. A security data engineer manages the Flower federated learning framework; a threat intelligence analyst curates attack signatures; a CISO validates detection policy thresholds.",
         "A single data breach costs Australian enterprises an average of $4.3 M (IBM 2023 report). Our federated model, sharing threat intelligence without sharing raw traffic, reduces mean time to detect novel intrusions from 197 days (industry average) to 12 hours. SaaS pricing: $180,000/year per enterprise network. Challenges: heterogeneous network topologies across participants (addressed via personalised federation), and Byzantine-robust aggregation against a compromised participant (addressed via Krum aggregation)."),
        ("Real-Time Sports Performance Analytics for Cricket Batting Optimisation",
         "Using ball-tracking data (Hawk-Eye system) and wearable IMU sensor streams from a professional T20 cricket academy (2 seasons, 180 players), we train a transformer-based sequence model to predict dismissal probability per ball and recommend optimal stroke selection for a given field placement. A sports data engineer manages Hawk-Eye XML extraction; an ML engineer trains the stroke recommendation model; a batting coach validates tactical outputs.",
         "Top-order batsmen who improve their shot selection by acting on ML recommendations show a 12% increase in average runs per dismissal in simulation. For a $5 M-salary top-order batsman, a 12% improvement in average translates to significant team value. Licenced to Cricket Australia at $250,000/year covering the national squad and state academies. Challenges: sparse data for rare ball deliveries (addressed via Bayesian hierarchical modelling across bowling types) and contextual factors not captured in Hawk-Eye (addressed via match situation features from CricInfo live feeds)."),
        ("Legal Judgment Prediction for Australian Civil Cases",
         "We fine-tune LegalBERT on 22,000 annotated Federal Court of Australia civil judgments (AustLII corpus) to predict case outcomes (plaintiff win/lose/partial) and extract key reasoning factors. An NLP engineer manages document parsing from PDF court decisions; a data scientist trains LegalBERT with outcome labels; a barrister validates prediction confidence alignment with legal reasoning complexity.",
         "Legal risk assessment by solicitors costs $500–$2,000/case; automated risk scoring reduces this to $20/case, enabling affordable access to litigation risk intelligence for SMEs and self-represented litigants. Licenced to law firms at $50,000/year for unlimited queries. Challenges: legal language evolution over time causing concept drift (addressed via annual fine-tuning on recent judgments), and data imbalance across case types (addressed via stratified sampling in fine-tuning batches)."),
        ("Autonomous Road Condition Monitoring Using Smartphone Accelerometers",
         "We train a Temporal Convolutional Network on crowdsourced smartphone accelerometer and GPS data (10 M km of road segments from the OpenPotholes dataset and VicRoads partner data) to classify road surface condition (excellent/good/fair/poor/very poor) at 10m resolution. A mobile data engineer manages the SDK for Android/iOS data collection; an ML engineer trains the TCN; a VicRoads infrastructure planner validates classification against manual surveys.",
         "Manual road condition surveys cost VicRoads $12 M/year; crowdsourced ML monitoring reduces this to $2.4 M/year ($9.6 M saving). Prioritised maintenance of 'poor' and 'very poor' segments (5% of road network) prevents $28 M in vehicle damage claims annually. SaaS platform licenced to 8 Australian state road authorities at $1.2 M/year each. Challenges: smartphone heterogeneity causing sensor noise variation (addressed via phone model–specific calibration layers) and privacy of GPS trajectories (addressed via on-device inference with only segment-level aggregates uploaded)."),
        ("Graph-Based Anti-Phishing URL Classification",
         "We represent URLs as directed graphs (nodes: URL tokens, DNS resolution chain, HTML DOM structure; edges: structural relationships) and apply a Graph Isomorphism Network (GIN) trained on the PhishTank + OpenPhish dataset (2 M labelled URLs) to classify phishing URLs with <5 ms inference latency per URL. A security data engineer builds the real-time URL feature extraction microservice; an ML engineer trains GIN; a threat intelligence analyst curates adversarial phishing examples for adversarial training.",
         "Phishing is the initial attack vector in 36% of data breaches; a single breach costs $4.3 M average (IBM 2023). Deploying phishing detection at the DNS resolver level for a 50,000-employee enterprise reduces phishing success rate from 3% to 0.4% of delivered emails, preventing ~1 breach/3 years ($1.4 M annualised). SaaS licensing at $12/user/year; target 500 enterprise customers for $300 M ARR. Challenges: adversarial URL obfuscation using Unicode homoglyphs (addressed via punycode normalisation before graph construction) and zero-day phishing domains (addressed via domain registration recency as an additional node feature)."),
        ("Automated Research Grant Matching for University Commercialisation",
         "We embed 18 years of ARC and NHMRC grant abstracts (280,000 grants) using SciBERT and build a bi-encoder retrieval system to match researcher profiles to relevant open funding calls, recommending the top-5 most suitable grants per researcher. An NLP data engineer manages ARC/NHMRC API ingestion; a research information scientist curates researcher profile data from Pure CRIS; a research office administrator evaluates recommendation quality via expert judgment.",
         "Researchers spend an average of 40 hours identifying and preparing grant applications; missed opportunities represent $800,000 in foregone grant income per 100 researchers annually. Our system reduces identification time to 2 hours, freeing 38 hours/researcher for research. Licenced to G8 universities at $80,000/year. Challenges: researcher profile sparsity for early-career academics (addressed via citation network–based profile augmentation using Semantic Scholar), and grant deadline sensitivity (addressed via real-time grant deadline monitoring via a web scraping pipeline)."),
        ("Real-Time Hand Gesture Recognition for AR/VR Interaction",
         "We train a MediaPipe Hands-augmented TCN model on the SHREC'21 dynamic hand gesture dataset augmented with 30,000 self-collected Apple Vision Pro interaction sequences to recognise 32 gesture classes at 60 Hz with <8 ms latency for natural AR/VR navigation. A computer vision engineer handles MediaPipe landmark preprocessing; an ML engineer trains the TCN on temporal keypoint sequences; a UX researcher conducts user studies on gesture learnability.",
         "Apple Vision Pro requires novel hands-free interaction paradigms; our gesture SDK would be the first real-time 32-class gesture recogniser publicly available for visionOS development. B2B licencing to 50 visionOS app developers at $5,000/year generates $250,000 ARR in Year 1, scaling to $5 M ARR with 1,000 developers. Enterprise spatial computing applications (surgical navigation, industrial inspection) provide a $2 B total addressable market. Challenges: gesture confusion between similar-looking gestures (addressed via contrastive learning with hard-negative gesture pairs) and hand occlusion in cluttered environments (addressed via keypoint dropout augmentation during training)."),
        ("Counterfeit Product Detection in Luxury E-Commerce Using Multi-Modal AI",
         "We train a two-stream network combining a fine-grained visual recognition model (trained on 800,000 authentic product images from Cartier and Louis Vuitton brand partnerships) with a text authentication model (detecting fake seller descriptions using stylometric anomaly detection) to flag counterfeit listings on marketplace platforms. Team: computer vision engineer, NLP engineer, IP legal analyst.",
         "Global counterfeit luxury goods cause $500 B in annual brand damage. Our system flags 91% of counterfeit listings before live publication (precision 0.87 in pilot tests), protecting brand equity and generating $1.2 M/year in licence fees per brand partner (target: 20 luxury brands). Platform API integration with Shopify and Amazon Seller Central. Challenges: adversarial sellers who rotate product images (addressed via hash-based deduplication and image perturbation detection) and evolving counterfeit quality (addressed via monthly retraining on newly confirmed fakes)."),
        ("Predictive Maintenance for Wind Turbine Gearboxes via Acoustic Emission",
         "We apply a 1D-CNN on 40 kHz acoustic emission signals sampled from piezoelectric sensors mounted on 80 wind turbine gearboxes (Vestas V90-2MW, 5-year dataset) to classify fault types (bearing spalling, gear tooth crack, lubricant contamination) with a 72-hour prognostic horizon. A mechanical engineer curates fault labels from maintenance logs; an embedded DSP engineer manages sensor firmware and edge preprocessing; an ML engineer trains the 1D-CNN.",
         "A single wind turbine gearbox replacement costs $350,000 including crane hire and lost generation. Detecting 80% of gearbox faults 72 hours in advance enables planned maintenance with 3-day lead time, reducing replacement cost to $180,000 (no emergency crane premium). For an 80-turbine wind farm, preventing 4 unplanned replacements/year saves $680,000. Challenges: impulsive noise from blade passage contaminating acoustic signals (addressed via synchronous average subtraction at blade pass frequency) and sensor-to-sensor variability (addressed via transfer learning with turbine-specific fine-tuning layers)."),
        ("Personalised Risk Assessment for Elderly Fall Prevention",
         "We train a gradient-boosted model on 3 years of wearable IMU and GPS data from 2,400 community-dwelling elderly participants (TILDA study) to predict 90-day fall risk, and integrate it with a clinician-facing dashboard that recommends balance training programmes tailored to specific detected gait impairments. A geriatric data scientist leads feature engineering (gait cadence, step variability, turning dynamics); an ML engineer trains and calibrates the model; a physiotherapist designs the intervention recommendation logic.",
         "Falls in Australian adults 65+ cost the healthcare system $2.3 B/year. Identifying the 25% of elderly adults at high fall risk and enrolling them in targeted balance training programs reduces falls by 35% in that group (~$200 M nationally). Programme delivery through existing physiotherapy networks at $400/enrolled person. Challenges: wearable adherence rates (~60% of participants wear sensors consistently) addressed via imputation from clinic visit gait assessments, and covariate shift between TILDA (Irish) population and Australian cohort addressed via importance weighting fine-tuning."),
        ("Hyper-Personalised Insurance Pricing via Telematics and ML",
         "We build a usage-based insurance (UBI) pricing model using telematics data from 150,000 policyholders (IAG DriveScore programme): GPS trajectories, accelerometer-derived harsh-braking events, and nighttime driving percentage. A GLM baseline is augmented with a gradient-boosted residual corrector. An actuarial data scientist ensures Solvency II–equivalent APRA reserve adequacy; a data engineer manages telematics ingestion from TomTom API; a pricing analyst defines model governance.",
         "UBI customers who consent to telematics receive average premium reductions of 18% (low-risk drivers), improving retention by 22%. For IAG's 500,000 auto policyholders, UBI adoption by 30% of low-risk customers reduces adverse selection loss ratio by 3 percentage points, saving ~$45 M/year in claims. Challenges: data quality of GPS signals in urban canyons (addressed via map-matching with OpenStreetMap snapping), and differential privacy for sensitive location data (addressed via trajectory-level k-anonymity before storage)."),
        ("Occupancy Prediction for Smart Building Energy Management",
         "We predict room-level occupancy in a 50,000 m² office building 30 minutes ahead using a fusion of CO2 sensor readings, Wi-Fi probe request counts, badge access logs, and calendar meeting data in a LightGBM model. A building IoT engineer manages MQTT sensor integration; an ML engineer trains LightGBM with time-series cross-validation; a facilities manager uses predictions to pre-condition HVAC.",
         "HVAC accounts for 40% of commercial building energy use; occupancy-driven pre-conditioning reduces HVAC energy by 22%, saving ~$180,000/year for a 50,000 m² A-grade office. NABERS energy rating improvement from 4.5 to 5.5 stars increases property valuation by ~$2.5 M. SaaS at $0.20/m²/year targets 500 commercial buildings for $5 M ARR. Challenges: privacy of badge access data (addressed via aggregated-only storage at room level), and sensor drift over time (addressed via online recalibration from HVAC fan-coil return temperature as a proxy occupancy signal)."),
        ("Dynamic Pricing for Ride-Sharing Surge Management",
         "We train a DQN agent to set surge multipliers for 200 hexagonal demand zones in Sydney, directly optimising the platform's gross merchandise value minus driver supply shortfall penalty, using a Lyft open-source ride-sharing simulator calibrated on 18 months of Ola Australia trip data. Roles: ride-sharing operations data scientist, RL engineer, pricing strategy manager.",
         "Manual surge pricing rules capture only 70% of the optimum welfare surplus during demand spikes; RL-based pricing recovers the remaining 30% ($4.5 M/year on $15 M annual Sydney GMV). Real-time zone-level pricing decisions are made in <10 ms via a Redis-backed state cache. Challenges: multi-zone coupling where surge in one zone displaces drivers to adjacent zones (addressed via spatial value function decomposition), and gaming by drivers who learn to position in high-surge zones (addressed via supply-aware state representation)."),
        ("Automated Radiology Report Generation from Chest X-Rays",
         "We train a CheXpert-pretrained DenseNet-121 visual encoder + GPT-2 text decoder end-to-end on the MIMIC-CXR dataset (227,000 chest X-ray/report pairs) to generate preliminary radiology reports, flagging 14 pathology findings. An ML engineer manages end-to-end training with cross-attention between image patches and report tokens; a radiologist provides ground-truth annotation corrections; a data engineer builds the DICOM-to-report pipeline.",
         "Radiologist report turnaround at many hospitals exceeds 48 hours; our system generates a draft report in 8 seconds, reducing turnaround to 2 hours with radiologist review. For a radiology group reading 150,000 chest X-rays/year, a 40% reduction in report time frees 0.8 FTE radiologist ($280,000 value), enabling the same headcount to cover 40% more imaging volume. Challenges: hallucination of absent findings (addressed via constrained decoding that prohibits findings not activated in the visual classification head) and regulatory pathway as a SaMD class IIb device (TGA submission with prospective clinical trial)."),
        ("Multi-Task Learning for Simultaneous Entity and Relation Extraction",
         "We implement a span-based multi-task BERT model that jointly predicts named entities and their relationships in scientific biomedical text (CRAFT corpus + BC5CDR dataset), sharing the BERT encoder across tasks and using task-specific span classification heads. A data engineer manages corpus preprocessing; an NLP engineer trains the multi-task model; a computational pharmacologist evaluates relation extraction quality for drug-gene interactions.",
         "Manual curation of drug-gene interaction databases (e.g., DrugBank) costs $500/relation extracted by a domain expert; automated extraction reduces this to $0.50/relation. For a pharmacogenomics lab curating 10,000 relations/year, savings are $4.95 M. Relations are ingested into a Neo4j knowledge graph powering drug repurposing queries. Challenges: overlapping entity spans (addressed via boundary detection as a separate auxiliary task) and relation directionality ambiguity (addressed via a direction-aware span pair encoding module)."),
        ("Explainable Credit Limit Decisions via Counterfactual Generation",
         "We build an XGBoost credit limit model for CommBank's credit card portfolio and implement DiCE (Diverse Counterfactual Explanations) to automatically generate the minimal set of actionable changes a customer must make to qualify for a higher limit, complying with Australia's upcoming EU AI Act–aligned explainability regulations. Team: credit risk data scientist, ML interpretability engineer, compliance officer.",
         "CommBank receives 2,000 credit limit increase complaints/year at $400/complaint resolution cost ($800,000). Automated counterfactual explanations resolve 60% of complaints without agent involvement ($480,000 saving). APRA's CPS 230 operational risk requirement for explainable AI decisions is also satisfied. Challenges: counterfactual feasibility (ensuring recommended changes are financially realistic) addressed via actionability constraints in DiCE, and high-dimensional feature space (addressed via PCA-based dimensionality reduction before DiCE optimisation)."),
        ("Semi-Supervised Defect Segmentation for Solar Panel Inspection",
         "Using a small labelled set (500 manually annotated EL images of solar panel defects: microcracks, broken busbars, delamination) and 20,000 unlabelled EL images from a solar farm in South Australia, we train a semi-supervised U-Net with mean-teacher consistency regularisation to segment defect regions at pixel level. A solar energy data engineer manages camera system integration; a computer vision engineer trains the semi-supervised model; a solar farm operator validates defect severity thresholds.",
         "Manual EL inspection of a 100 MW solar farm (400,000 panels) costs $200,000/inspection; automated drone-based EL capture + ML segmentation reduces this to $40,000/inspection. Identifying and replacing the 3% of panels with severe defects recovers $420,000/year in lost generation at current electricity prices. Challenges: annotation scarcity for rare defect types (addressed via mean-teacher pseudo-labelling with confidence thresholding), and EL image quality degradation from ageing cameras (addressed via image quality assessment pre-filtering)."),
        ("Conversational AI Agent for Mental Health First Aid Triage",
         "We fine-tune LLaMA-3-8B-Instruct via RLHF (using Beyond Blue clinical guidelines as reward model training signal) to conduct structured mental health first aid conversations that screen for depression/anxiety severity (PHQ-9/GAD-7) and route users to appropriate support resources. An NLP engineer manages RLHF pipeline; a clinical psychologist designs the conversation flow and validates responses against MHFA standards; a data scientist evaluates PHQ-9 scoring accuracy.",
         "Mental health help-seeking in Australia is constrained by stigma and wait times (6-8 weeks for a GP referral). Our agent provides an accessible first contact point, with 60% of users redirected to appropriate services within 24 hours. Deployment via Beyond Blue's app at $0 cost to users, funded by NHMRC research grant and government digital health investment. Challenges: suicide crisis protocols requiring immediate human handoff (addressed via a hard-coded emergency escalation trigger at specific keyword combinations with human counsellor on-call), and hallucination of clinical advice (addressed via retrieval-augmented generation from validated clinical guidelines only)."),
        ("Demand Forecasting for Blood Product Inventory in Hospital Networks",
         "We train a Temporal Fusion Transformer on 7 years of Red Cross Blood Service daily transfusion records (18 hospitals, 6 blood product types) to forecast 7-day demand per hospital-product combination, enabling optimised distribution of perishable blood products (42-day shelf life for RBCs). A blood bank data engineer manages HL7 FHIR integration; an ML engineer trains TFT; a transfusion medicine specialist validates clinical relevance.",
         "Blood product wastage due to expiry costs Australian hospitals $12 M/year. A 30% reduction in wastage via demand-driven distribution saves $3.6 M annually. Emergency shortage prevention (forecasting demand spikes before elective surgery surges) avoids surgical cancellations valued at $800,000/year. Challenges: rare event demand spikes from mass casualty incidents (addressed via exogenous event features from hospital ED admission forecasts) and inter-hospital sharing logistics (addressed via joint optimisation of forecast + redistribution routing)."),
        ("Multimodal Fake Review Detection for E-Commerce Platforms",
         "We fuse text (RoBERTa embeddings of review content), metadata (reviewer posting velocity, account age, product return history), and image features (CLIP embeddings of uploaded review photos) in a cross-attention multimodal classifier trained on the YelpZip fake review dataset augmented with 50,000 manually labelled Amazon reviews. Team: NLP engineer (text and image encoders), data engineer (metadata feature pipeline), trust and safety analyst.",
         "Fake reviews influence 4% of Australian consumer spending (~$4 B/year); platforms face ACCC penalties up to $50 M for failing to address fake reviews under the new deceptive practices regime. Our classifier flags 88% of coordinated fake review campaigns for human review at 0.7% false positive rate. Licenced to Kogan, Catch, and Amazon AU at $200,000/year per platform. Challenges: adversarial review farms that adapt writing style to avoid detection (addressed via adversarial training with GAN-generated fake reviews) and cold-start for new product categories (addressed via zero-shot classification using CLIP image similarity to known fake-review patterns)."),
        ("Reinforcement Learning for Optimal Chemotherapy Dosing",
         "We train a model-based RL agent (MBRL with Gaussian process dynamics model) on retrospective chemotherapy dosing records (3,200 breast cancer patients, Peter MacCallum Cancer Centre, 2015–2022) to learn individualised dosing policies that maximise tumour response while minimising haematological toxicity, using neutrophil count trajectory as the state space. An oncology data scientist models drug pharmacokinetics; an RL engineer implements MBRL with safety constraints; a medical oncologist validates policy outputs against NCCN guidelines.",
         "Suboptimal chemotherapy dosing leads to 28% of patients receiving doses too low for full efficacy and 15% experiencing Grade 3–4 toxicity from over-dosing. RL-optimised dosing is projected to improve complete response rates by 8% (40 additional responses per 500 patients/year at Peter Mac) and reduce Grade 3–4 toxicity by 30%, avoiding $1.6 M in toxicity management costs. Deployment as a clinical decision support tool (not autonomous prescription) with TGA approval pathway as a SaMD class III device. Challenges: patient heterogeneity across cancer subtypes (addressed via patient-stratified Gaussian process dynamics models) and prospective validation requirement (addressed via a planned RCT with Peter Mac ethics approval)."),
        ("Automated Slide Presentation Generation from Research Papers",
         "We implement a two-stage pipeline: (1) a summarisation model (PEGASUS fine-tuned on the SciSummNet dataset) extracts key contributions, methods, and results from research paper PDFs, and (2) a layout planning model (trained via supervised learning on 8,000 matching paper-slide pairs from SlideShare) generates structured slide outlines with speaker notes. An NLP engineer manages PDF parsing and model fine-tuning; a front-end engineer builds the Google Slides API integration; an academic researcher validates scientific accuracy.",
         "Researchers spend 6–8 hours creating conference presentation slides from a paper; our system generates a 90%-complete draft in 3 minutes. For a 200-researcher institute presenting at 4 conferences/year, the tool saves 1,600 hours/year ($320,000 in researcher time). B2C SaaS at $15/month targets 50,000 academic users for $9 M ARR. Challenges: hallucination of figures and tables not in the paper (addressed via figure reference grounding — slides are permitted to display only figures extracted from the PDF), and layout aesthetics (addressed via a CLIP-guided aesthetic scoring model that rejects low-quality slide images during generation)."),
        ("Federated Learning for Cross-Hospital Sepsis Prediction",
         "We implement a federated learning system using the Flower framework across 6 Australian hospitals, where each hospital trains a local LSTM on its own MIMIC-format ICU data and aggregates model weights using FedAvg with differential privacy (ε=2.0). A federated ML engineer manages orchestration; a data engineer builds each hospital's local pipeline; an intensivist validates the global model performance against each site's local baseline.",
         "Federated training across 6 hospitals produces a model with 15% higher AUROC than single-hospital models (more diverse training data) while never centralising patient data. Avoiding data centralisation eliminates $500,000 in data governance overhead per participating hospital. The global model is licenced back to participants at $200,000/year, generating $1.2 M ARR. Challenges: heterogeneous EHR schemas across hospitals (addressed via a shared OMOP CDM mapping layer), and Byzantine-robust aggregation against a potential compromised site (addressed via Krum aggregation as an alternative to FedAvg)."),
        ("Automated Invoice Processing and Approval Workflow via OCR and NLP",
         "We build an end-to-end invoice processing pipeline combining a PaddleOCR layout-aware text extractor with a LayoutLM-v3 classifier trained on 80,000 annotated Australian tax invoices to extract vendor name, ABN, GST amount, and line items, then route to the appropriate approver via a rule-based workflow engine integrated with Microsoft Dynamics 365. A data engineer manages the SharePoint document ingestion pipeline; an NLP engineer fine-tunes LayoutLM-v3; an AP operations manager defines workflow rules.",
         "A mid-size company processes 5,000 invoices/month at $12/invoice (data entry, verification, approval routing); automated processing reduces cost to $1.50/invoice, saving $525,000/year. ATO compliance (GST reconciliation accuracy >99.5%) is validated quarterly. Challenges: variable invoice layouts across 800+ suppliers (addressed via layout-agnostic LayoutLM-v3 attention over document tokens and spatial positions), and handwritten invoice fields from small suppliers (addressed via a HTR fallback using TrOCR for handwritten regions)."),
        ("Dynamic Tariff Optimisation for Water Distribution Networks",
         "Using 10 years of Sydney Water consumption records (2 M meter reads/day) and infrastructure cost models, we train a causal inference model (double ML) to estimate price elasticity per customer segment and geography, then implement a dynamic tariff recommendation engine that maximises revenue adequacy while promoting conservation in drought-stressed catchments. A utility data scientist leads causal modelling; a pricing engineer builds the optimisation solver; a water policy analyst ensures IPART regulatory compliance.",
         "Sydney Water's current flat tariff underprices peak-demand consumption by 30%, costing $60 M/year in deferred infrastructure investment. Marginal-cost-aligned tariffs recover this while reducing peak demand by 8% (380 ML/day), deferring $120 M in dam infrastructure expansion by 5 years ($24 M NPV saving). Challenges: regressivity of higher tariffs for low-income households (addressed via a 'lifeline tariff' exemption block for the first 20 kL/quarter), and smart meter penetration at only 40% (addressed via synthetic consumption profile imputation for non-smart meters)."),
        ("Graph Attention Networks for Academic Citation Recommendation",
         "We build a citation recommendation system using a Graph Attention Network (GAT) over the Microsoft Academic Graph (250 M papers, 1.5 B citations), where nodes are papers (features: SciBERT title+abstract embeddings) and edges are citation links. Given a draft paper, the system retrieves the top-20 most relevant uncited works via approximate nearest-neighbour search on GAT node embeddings. An ML engineer trains GAT on a 4-GPU cluster; a data engineer manages MAG graph updates; a library scientist evaluates recall@20 against reference gold standards.",
         "Researchers miss an average of 8 relevant papers in each publication, leading to knowledge gaps and duplicated work. Automated citation recommendation integrated into Overleaf and Microsoft Word reduces missed citations by 60%, improving research quality. Licenced to academic publishers (Elsevier, Springer Nature) at $300,000/year. Challenges: graph scale requiring GraphSAGE-style mini-batch training (addressed via the PyG scalable graph sampling library), and cold-start for preprint papers not yet indexed in MAG (addressed via abstract-only SciBERT embedding retrieval as a fallback)."),
        ("Privacy-Preserving Synthetic Data Generation for Healthcare Research",
         "We train a conditional GAN (CTGAN) on de-identified patient records from the APDC (Australian Patient Data Collection, 3 M hospitalisations) to generate synthetic patient datasets that preserve statistical properties for research use while provably preventing re-identification (ε-differential privacy guarantee with ε=1.0). A privacy-ML engineer implements DPCTGAN; a biostatistician validates synthetic data utility via propensity score matching tests; a legal officer reviews under the Privacy Act 1988.",
         "Sharing real patient data with external researchers requires IRB approval processes taking 6–18 months; synthetic data can be released in 2 weeks under a self-serve portal. AIHW currently spends $2 M/year managing data access requests; synthetic data automation reduces this to $200,000/year. External researchers pay $5,000/dataset access, generating $1.5 M/year revenue for AIHW. Challenges: mode collapse in GAN training causing underrepresentation of rare clinical events (addressed via minority oversampling before GAN training), and synthetic data utility degradation for subgroup analyses (addressed via conditional generation with explicit subgroup conditioning)."),
        ("Churn Prediction and Intervention Optimisation for Telecom Subscribers",
         "We build a two-stage pipeline: (1) a gradient-boosted churn model on Telstra's 3-year subscriber feature set (usage patterns, ARPU trends, contract end dates, service quality metrics), and (2) a causal uplift model (T-learner with XGBoost base) to estimate incremental retention probability per intervention type (discount, plan upgrade, tech support outreach). Team: data scientist, causal ML engineer, retention marketing manager.",
         "Telco subscriber acquisition costs ~$400; reducing quarterly churn by 1% retains 50,000 subscribers worth $20 M in annual recurring revenue. Uplift-model-guided targeting focuses retention spend on persuadable churners, improving ROI by 35% compared to untargeted intervention. Challenges: counterfactual inference from observational data (addressed via DML double-debiased ML to remove confounding), and ARPU distribution shift during economic downturns (addressed via rolling 90-day training window retraining)."),
    ]
    for title, desc, biz in remaining_high:
        records.append(_entry(len(records)+1, "High", next(si), title, desc, biz))

    return records[:107]


# ---------------------------------------------------------------------------
# LOW-PERFORMER PROPOSALS  (107 total, scores 5.0–10.0)
# ---------------------------------------------------------------------------

def _low_proposals() -> list[dict]:
    records = []
    scores = _low_scores(107)
    si = iter(scores)

    low_items = [
        # Social media / internet data (vague)
        ("Analysing Social Media Trends with Machine Learning",
         "This project will analyse trends on social media platforms. I plan to collect data from Twitter and Instagram using their APIs. The data will include posts, likes, and comments. I will then apply machine learning techniques to find patterns in the data. Python will be used for the analysis.",
         "Social media analysis is useful for many businesses. Companies can understand what customers are saying about them. The results could help businesses improve their marketing strategies. There might be some challenges with getting access to the data and making sure the analysis is accurate."),
        ("Predicting Social Media Post Virality",
         "I will look at social media posts and try to predict which ones will go viral. I will collect data from popular platforms. Features might include the number of likes, shares, and the time of posting. I will try different machine learning models to see which works best.",
         "Viral social media posts are valuable for brands and influencers. If we can predict virality, companies can plan their content better. The main challenge is collecting enough data. I will use whatever public datasets are available online."),
        ("Sentiment Analysis of Twitter Data",
         "My project is about sentiment analysis on Twitter. I will collect tweets about a specific topic and classify them as positive, negative, or neutral. I will use a pre-trained sentiment analysis model and apply it to the tweets. The results will show how people feel about the topic.",
         "Many companies want to know public opinion about their products. This system would help them understand social sentiment quickly. The challenge is dealing with informal language and slang on Twitter. I will try to handle this with some preprocessing steps."),
        ("Analysing Reddit Comments to Understand Public Opinion",
         "I want to analyse comments on Reddit to understand what people think about various topics. I will use the Reddit API to collect comments and apply text analysis techniques. I hope to find interesting patterns in how people discuss different subjects online.",
         "Understanding public opinion is valuable for many stakeholders. Governments and companies could use this information to make better decisions. Collecting data at scale might be challenging. The project would use open-source tools and free data from Reddit."),
        ("Facebook User Behaviour Analysis",
         "This project analyses Facebook user behaviour using publicly available data. I will look at things like posting frequency and engagement patterns. Machine learning will help identify different types of users. The results could be useful for social media platform designers.",
         "Understanding user behaviour helps platforms improve their design. Advertisers would also benefit from knowing more about how people use Facebook. Privacy could be a concern, but I will only use publicly visible data. The main technical challenge is handling large amounts of data."),

        # Simple prediction tasks (vague)
        ("Predicting House Prices Using Machine Learning",
         "I want to predict house prices in Melbourne using a machine learning model. I will collect data about houses including size, location, number of bedrooms, and age. Then I will train a regression model to predict the price. I will compare different algorithms to see which is most accurate.",
         "Real estate agents and buyers would benefit from accurate price predictions. Knowing the expected price helps people make better decisions. The main challenge is getting good quality data. I will try to use data from publicly available real estate websites."),
        ("Stock Market Prediction Using Historical Data",
         "This project is about predicting stock prices using historical data. I will download stock price data from Yahoo Finance and use it to train a time series model. I might use LSTM because I have heard it works well for time series data. I will evaluate the model using common metrics.",
         "Investors want to make money from the stock market. A good prediction model could help them make better investment decisions. The main challenge is that markets are very unpredictable. I will focus on predicting trends rather than exact prices."),
        ("Weather Prediction Using a Neural Network",
         "I will build a neural network to predict the weather. I will use historical weather data as input and try to predict temperature and rainfall for the next day. I will use Python and TensorFlow to build the model. The accuracy will be compared to simple baseline predictions.",
         "Weather prediction is important for many activities including farming and outdoor events. An accurate model would be commercially valuable. The challenge is that weather depends on many factors that are hard to capture. I will start with a simple model and add complexity if needed."),
        ("Predicting Customer Lifetime Value",
         "My project will predict how much value a customer will bring to a business over their lifetime. I will use past transaction data and machine learning to make predictions. The features will include purchase history and customer demographics. Various regression models will be compared.",
         "Knowing the lifetime value of customers helps businesses decide how much to spend on acquiring and retaining them. This is useful for marketing and strategy. The challenge is getting accurate data. I plan to use a publicly available e-commerce dataset from Kaggle."),
        ("Energy Consumption Forecasting for Households",
         "I will forecast household energy consumption using smart meter data. The model will predict energy use for the next 24 hours based on historical patterns. I will try several machine learning models and pick the best one. Time features like hour of day and day of week will be used.",
         "Energy companies need to forecast demand to manage the grid efficiently. Households could also benefit by planning their energy use better. The challenge is getting representative data. I will look for public smart meter datasets to use in this project."),
        ("Predicting Employee Attrition with Machine Learning",
         "This project predicts whether an employee will leave a company. I will use HR data including salary, job role, and satisfaction scores as features. Classification algorithms like logistic regression and decision trees will be applied and compared. The IBM HR Analytics dataset will be used for training.",
         "Employee turnover is expensive for companies. Predicting which employees are likely to leave lets HR departments intervene early. The challenge is getting real HR data, which is often private. I will use the publicly available IBM dataset as a proxy. The results might not generalise to other companies."),
        ("Predicting Traffic Accidents Using Historical Data",
         "My project looks at predicting traffic accidents using historical accident records. Features will include time of day, weather conditions, and road type. I will use a classification model to predict accident likelihood. This could help transport authorities plan better.",
         "Reducing traffic accidents would save lives and money. Transport authorities could use predictions to allocate safety resources. The challenge is that accident data might be incomplete or have missing values. I will handle this using basic imputation techniques."),
        ("Predicting Flight Delays Using Airline Data",
         "I will predict whether a flight will be delayed using features like airline, departure airport, time of day, and weather. A classification model will be trained on historical flight data from the BTS dataset. The goal is to help passengers plan better when there is a risk of delay.",
         "Flight delays are inconvenient for passengers and costly for airlines. A prediction tool could be embedded in flight booking websites. The main challenge is that delays depend on many unpredictable factors. My model will give probability estimates rather than exact predictions."),

        # Simple classification
        ("Email Spam Classifier Using Naive Bayes",
         "I will build a spam email classifier using the Naive Bayes algorithm. The model will classify emails as spam or not spam based on the words they contain. I will use the Enron email dataset for training. Common NLP preprocessing like tokenisation and stop word removal will be applied.",
         "Spam filtering is important for email users everywhere. A better spam classifier means fewer unwanted emails reach users' inboxes. The challenge is keeping up with new types of spam as spammers change their techniques. My model will provide a baseline that could be improved over time."),
        ("Classifying News Articles by Topic",
         "My project will classify news articles into categories such as politics, sport, and technology. I will use a dataset of labelled news articles and train a text classifier. TF-IDF features will be used with a logistic regression classifier. I will evaluate using accuracy and F1-score.",
         "News websites could use topic classification to automatically organise articles and improve user experience. Publishers could also use it to analyse trends in their content. The main challenge is dealing with articles that cover multiple topics at once. I will focus on single-label classification for simplicity."),
        ("Image Classification of Animals Using CNN",
         "I want to classify images of animals using a convolutional neural network. I will use a publicly available dataset of animal images. The model will learn to distinguish between different animal species. I will use transfer learning from a pre-trained model to speed up training.",
         "Animal image classification could be useful for wildlife monitoring applications. Conservation organisations could use it to track animal populations from camera trap images. The challenge is collecting enough diverse training images. I will use an existing dataset rather than collecting my own."),
        ("Classifying Skin Lesions as Benign or Malignant",
         "This project classifies skin lesion images as either benign or malignant. I will use the ISIC dataset which contains labelled dermoscopy images. A CNN model will be trained to detect malignant lesions. The model's accuracy will be compared to dermatologist performance where possible.",
         "Early detection of skin cancer could save lives. An AI tool could help people check suspicious lesions at home. The challenge is that medical AI systems need to be very accurate and reliable. I will try to make the model as accurate as possible and acknowledge its limitations."),
        ("Classifying Sentiment in Product Reviews",
         "I will classify Amazon product reviews as positive or negative based on the review text. I will use a pre-trained sentiment model or train my own on the Amazon review dataset. The model will be evaluated on a held-out test set. Results will be compared to simple baseline methods.",
         "Companies want to know what customers think of their products without reading every review. This system automates sentiment classification at scale. The challenge is that some reviews are mixed or sarcastic. I will note these cases as limitations of the model."),
        ("Classifying Fake News Articles",
         "My project detects fake news articles using text classification. I will use a dataset of labelled real and fake news articles. Features will include writing style and word frequency. A machine learning classifier will be trained to distinguish real from fake articles.",
         "Misinformation is a big problem on the internet. A fake news classifier could help platforms and users identify unreliable content. The challenge is that fake news can be sophisticated and hard to detect. My model will be a proof of concept rather than a production system."),

        # Recommendation systems (vague)
        ("Building a Movie Recommendation System",
         "I will build a movie recommendation system using collaborative filtering. Users will rate movies and the system will recommend new movies based on similar users' preferences. I will use the MovieLens dataset for this project. The system will be evaluated using RMSE on held-out ratings.",
         "Streaming platforms like Netflix need recommendation systems to keep users engaged. A good recommendation system increases user satisfaction and subscription retention. The challenge is dealing with the cold-start problem when new users have no history. I will use a simple popularity-based fallback for new users."),
        ("Recommending Books to Users Based on Past Reads",
         "This project builds a book recommendation system using the Goodreads dataset. I will apply collaborative filtering to recommend books users have not yet read. The recommendations will be based on the reading history and ratings of similar users.",
         "People often struggle to find new books they will enjoy. A recommendation system would make it easier to discover new reads. The main challenge is the sparsity of ratings since most users have only rated a small fraction of books. Matrix factorisation will be used to handle this."),
        ("Restaurant Recommendation Using Location and Reviews",
         "I will build a restaurant recommendation system using Yelp review data. The system will recommend restaurants based on user location, past ratings, and review sentiment. A content-based filtering approach will be combined with location proximity.",
         "Finding a good restaurant in an unfamiliar city is difficult. A personalised recommendation system would make this easier for travellers and locals. The challenge is handling the dynamic nature of restaurant quality which changes over time. I will use recent reviews to weight recommendations towards currently relevant options."),
        ("Music Playlist Generator Using Audio Features",
         "My project generates music playlists based on audio features. I will use the Spotify dataset from Kaggle which includes features like tempo, energy, and valence. A K-means clustering algorithm will group similar songs, and playlists will be generated from the same cluster.",
         "People enjoy listening to music that matches their mood. An automated playlist generator saves users time selecting songs manually. The challenge is that audio features do not fully capture what makes a song enjoyable to a specific person. I will use a simple content-based approach as a starting point."),

        # Agriculture vague
        ("Predicting Crop Yields Using Weather Data",
         "I will predict crop yields using historical weather data and planting records. Regression models will be trained on temperature and rainfall data to predict wheat yield. The data will come from publicly available government agricultural statistics and weather records.",
         "Farmers need to plan for how much crop they will produce each season. Better yield predictions help with storage and market planning. The challenge is that crop yields depend on many factors beyond weather. I will acknowledge the model's limitations and suggest future improvements."),
        ("Plant Disease Detection from Leaf Images",
         "This project detects plant diseases from images of leaves. I will use a CNN trained on the PlantVillage dataset. The model will classify leaves as healthy or diseased and identify the type of disease. This could help farmers catch problems early.",
         "Plant diseases can destroy crops and cause significant losses for farmers. Early detection allows farmers to treat crops before the disease spreads. The challenge is that the PlantVillage dataset was collected under controlled conditions and might not work well in real farm settings. I will test the model on some real farm images if possible."),
        ("Precision Farming Using Satellite Imagery",
         "I want to use satellite imagery for precision farming. I will download satellite images of agricultural land and apply image analysis to identify crop health. NDVI index calculations will be used to assess vegetation health. The results could help farmers make decisions about irrigation and fertilisation.",
         "Precision farming helps farmers use resources more efficiently. Satellite imagery provides broad coverage without requiring expensive on-ground sensors. The challenge is accessing high-resolution imagery, which can be expensive. I will use freely available Sentinel-2 imagery for this project."),

        # Healthcare vague
        ("Analysing Hospital Patient Data to Improve Care",
         "My project analyses patient data from hospitals to find patterns that could improve care. I will use a publicly available healthcare dataset. Machine learning will identify factors associated with longer hospital stays. The results could help hospital administrators make better decisions.",
         "Hospitals want to improve patient outcomes while reducing costs. Data analytics can reveal insights that would otherwise be hidden. The challenge is getting access to real patient data due to privacy rules. I will use a publicly available dataset that has been de-identified."),
        ("Predicting Diabetes Using Patient Health Records",
         "I will predict whether a patient has diabetes using health record data. Features include BMI, glucose levels, and age. A classification model such as logistic regression or a decision tree will be trained and evaluated on the Pima Indians Diabetes dataset. Accuracy and AUC will be reported.",
         "Diabetes is a growing health problem worldwide. Early detection allows for better management of the condition. The challenge is that the dataset I am using is relatively small and may not represent all populations. I will discuss the generalisability of the results in my analysis."),
        ("Analysing Mental Health Survey Data",
         "This project analyses mental health survey data to understand what factors are associated with mental health conditions. I will use the OSMI mental health in tech survey dataset. Statistical analysis and machine learning will be used to identify important predictors.",
         "Mental health is an important issue especially in the workplace. Understanding the factors associated with mental health problems could help organisations create better support systems. The challenge is that survey data is self-reported and may not be fully accurate. I will acknowledge this limitation in my analysis."),
        ("COVID-19 Data Analysis and Trend Prediction",
         "I will analyse COVID-19 data to understand trends in case numbers and predict future case counts. I will use publicly available data from WHO or Our World in Data. Time series models like ARIMA or exponential smoothing will be applied to forecast cases.",
         "Understanding COVID-19 trends is important for public health planning. Accurate forecasts help governments decide on public health measures. The challenge is that COVID-19 case numbers depend on testing rates and reporting, which vary across countries. I will try to account for these factors in my analysis."),

        # Retail / e-commerce vague
        ("Customer Segmentation for a Retail Business",
         "This project segments retail customers using their purchase history. K-means clustering will be applied to group customers with similar buying behaviour. The resulting segments will be described and their business value discussed. Data from a public retail dataset will be used.",
         "Understanding different customer groups helps retailers target their marketing more effectively. Customer segmentation allows businesses to personalise their offers. The main challenge is choosing the right number of segments. I will use the elbow method to determine the optimal K value."),
        ("Predicting Customer Purchase Intent on E-Commerce Sites",
         "I will predict whether an e-commerce website visitor will make a purchase during their session. The dataset includes clickstream data from an online shopping site. A classification model will be trained to predict purchase intent. The UCI Online Shoppers Intention dataset will be used.",
         "Knowing which visitors are likely to buy allows e-commerce sites to show targeted promotions at the right time. This can increase conversion rates and revenue. The challenge is dealing with highly imbalanced data since most sessions do not end in a purchase. I will use oversampling to address this."),
        ("Retail Sales Forecasting for Inventory Planning",
         "My project forecasts retail sales at the product category level to help with inventory planning. Historical sales data will be used to train a time series forecasting model. ARIMA and exponential smoothing will be compared. The results will show which model works better for different product categories.",
         "Accurate sales forecasting reduces the risk of overstocking or running out of products. Both outcomes are costly for retailers. The challenge is that sales can be affected by promotions and external events which are hard to model. I will try to include promotional information as an additional feature."),
        ("Price Optimisation for Online Retailers",
         "I will build a price optimisation model for an online retailer. The model will analyse how price changes affect demand and recommend optimal prices to maximise revenue. I will use publicly available data from an online retail transaction dataset.",
         "Pricing is a key lever for retailers to increase revenue. Automated price optimisation can react to market conditions faster than manual adjustments. The challenge is that price elasticity varies greatly across products and customer segments. I will start with a simple linear demand model and improve from there."),

        # Sports vague
        ("Predicting Football Match Outcomes",
         "My project predicts the outcome of football matches using historical data. Features include team statistics, home or away status, and recent form. A classification model will be trained to predict win, draw, or loss. The results will be compared against bookmaker odds as a baseline.",
         "Sports prediction is interesting for fans and betting markets. A good model could help fans make informed predictions about upcoming matches. The challenge is that football matches can be unpredictable due to random events. I will focus on identifying which features are most important for prediction."),
        ("Basketball Player Performance Analytics",
         "This project analyses basketball player performance using statistics data. I will use publicly available NBA statistics to analyse player contributions to team success. Regression analysis will identify which player attributes are most associated with winning. The results could be useful for team management decisions.",
         "Sports analytics is increasingly important in professional basketball. Teams use data to make better decisions about player recruitment and game strategy. The challenge is attributing team success to individual players since basketball is a team sport. I will use adjusted metrics that attempt to account for team context."),
        ("Predicting Rugby Player Injuries",
         "I will try to predict rugby player injuries using training load data. Features will include training hours, distance covered, and previous injury history. A machine learning model will be trained to classify players as high or low injury risk.",
         "Injuries are costly for rugby teams both in terms of player welfare and team performance. Early identification of injury risk allows for preventive intervention. The challenge is getting access to real training data which is often proprietary. I will try to find or simulate representative data for this project."),

        # Energy vague
        ("Smart Home Energy Management System",
         "I will build a system that manages energy usage in a smart home. Sensors will monitor when appliances are in use and a machine learning model will suggest optimal times to run high-energy appliances. The goal is to reduce energy bills by shifting usage to off-peak times.",
         "Smart home energy management can reduce household electricity bills. It can also help reduce strain on the electricity grid during peak hours. The challenge is integrating with different smart home devices which have different APIs. I will focus on a simulated environment for this project."),
        ("Predicting Solar Panel Output Using Weather Data",
         "My project predicts the power output of solar panels using weather data. Features include solar radiation, temperature, and cloud cover. A regression model will be trained on historical solar output data linked to weather observations. The results could help solar energy planners schedule grid operations.",
         "Solar energy is growing rapidly in Australia and predicting output is important for grid stability. More accurate forecasts help energy operators balance supply and demand. The challenge is that solar output is highly variable and depends on localised weather conditions. I will use data from a single solar installation as a case study."),
        ("Electric Vehicle Charging Demand Forecasting",
         "I will forecast electricity demand from electric vehicle charging stations. Time series data from a network of charging stations will be used to train a forecasting model. The model will predict demand at hourly intervals to help grid operators plan capacity.",
         "As more people adopt electric vehicles, managing charging demand becomes increasingly important for grid stability. Accurate forecasting helps operators avoid grid stress during peak charging periods. The challenge is that EV adoption patterns are changing rapidly, making historical data less relevant for future forecasting. I will acknowledge this as a key limitation."),

        # Logistics vague
        ("Route Optimisation for Delivery Trucks",
         "My project optimises delivery routes for a small courier company. I will use the travelling salesman problem as the basis and apply a heuristic algorithm to find good routes. Google Maps API will be used to estimate travel times between delivery locations.",
         "Efficient delivery routes reduce fuel costs and allow more deliveries per day. This is directly valuable for courier companies. The challenge is that the number of possible routes grows exponentially with the number of deliveries. I will use a greedy algorithm as an approximation since exact solutions are too slow to compute."),
        ("Warehouse Layout Optimisation Using Simulation",
         "I will simulate a warehouse and optimise its layout to minimise the distance workers travel to pick orders. A discrete event simulation model will be built using Python. Different layout configurations will be tested to find the most efficient arrangement.",
         "Warehouse efficiency directly affects order fulfilment costs. Optimising the layout can significantly reduce picking time and labour costs. The challenge is accurately modelling complex warehouse operations including variable demand patterns. I will make simplifying assumptions in my initial model and note where real-world complexity is not captured."),
        ("Predicting Package Delivery Failures",
         "This project predicts whether a parcel delivery will fail on the first attempt. Features include time of delivery, recipient location type, and package weight. A machine learning classifier will be trained on historical delivery records. Reducing failed deliveries saves courier companies money.",
         "Failed first-attempt deliveries are costly for courier companies. Predicting failure allows proactive actions such as scheduling an alternative delivery window. The challenge is getting access to real delivery data which companies consider commercially sensitive. I will look for a public logistics dataset or contact a local courier company about a data partnership."),

        # Cybersecurity vague
        ("Detecting Network Intrusions Using Machine Learning",
         "I will build a network intrusion detection system using machine learning. The KDD Cup 1999 dataset will be used for training. A classifier will be trained to distinguish normal network traffic from various types of attacks. The model will be evaluated on accuracy and detection rate.",
         "Network security is critically important for organisations. An automated intrusion detection system can identify threats faster than manual monitoring. The challenge is that the KDD Cup dataset is quite old and may not reflect modern attack patterns. I will acknowledge this limitation and suggest using more modern datasets in future work."),
        ("Password Strength Prediction Using ML",
         "I will train a machine learning model to predict the strength of passwords. The model will use features like length, character diversity, and common word inclusion. A classifier will rate passwords as weak, medium, or strong. This could be useful for password policy enforcement.",
         "Weak passwords are a major security vulnerability. An automated strength predictor could help systems enforce better password policies. The challenge is defining what makes a password strong since attackers continuously update their cracking strategies. I will base my strength definitions on well-known password guidelines like NIST recommendations."),

        # Education vague
        ("Analysing Student Performance Using School Data",
         "My project analyses student academic performance using school records. Features like attendance, previous grades, and family background will be used to predict final exam scores. A regression model will be trained and evaluated. The UCI Student Performance dataset will be used.",
         "Understanding factors affecting student performance helps schools provide targeted support. Early identification of struggling students allows for timely intervention. The challenge is that many important factors affecting student performance are not captured in school records. I will discuss these limitations in my analysis."),
        ("Predicting University Student Dropout",
         "I will predict which university students are at risk of dropping out using data from their first semester. Features include grades, attendance, and engagement with learning management systems. A classification model will be trained and evaluated on a publicly available dataset.",
         "Student dropout is costly for universities and detrimental to students' futures. Early identification allows universities to provide support before the problem becomes critical. The challenge is accessing real student data which is confidential. I will use a publicly available dataset as a proxy for real student data."),

        # Miscellaneous vague
        ("Predicting Real Estate Rental Prices",
         "I will predict rental prices for apartments in Sydney using listing data scraped from property websites. Features include location, number of bedrooms, and distance from transport. A regression model will be trained and its performance evaluated against actual rental prices.",
         "Renters and landlords both benefit from knowing fair market rental prices. A prediction model can help renters check if they are paying a reasonable price. The challenge is keeping the data up to date as the rental market changes quickly. I will collect data at a single point in time and acknowledge this as a limitation."),
        ("Classifying Medical Imaging Data for Disease Detection",
         "My project applies machine learning to medical imaging data to detect diseases. I will use a publicly available dataset of medical images. A convolutional neural network will be trained to classify images as normal or abnormal. The model's performance will be compared to published benchmarks.",
         "Automated medical image analysis could assist doctors in diagnosing diseases more quickly. This is especially valuable in areas with limited access to specialist doctors. The challenge is that medical AI systems require careful validation before clinical deployment. My project will be a proof of concept and not intended for clinical use."),
        ("Chatbot Development for Customer Service Automation",
         "I will build a customer service chatbot using natural language processing. The chatbot will answer common customer questions using a retrieval-based approach. I will use a pre-trained language model to understand customer queries and match them to predefined answers.",
         "Customer service chatbots can reduce the workload on human agents and provide 24/7 support. This can improve customer satisfaction while reducing operational costs. The challenge is handling queries outside the chatbot's knowledge base. I will implement a fallback to human agents for queries the bot cannot answer."),
        ("Analysing and Visualising Crime Data",
         "This project analyses crime data from an Australian city to identify patterns and hotspots. I will download publicly available crime statistics and create visualisations showing crime distribution by area and time. Machine learning will be used to identify factors associated with higher crime rates.",
         "Understanding crime patterns helps law enforcement allocate resources more effectively. Citizens could also use crime maps to make safer decisions about where they live or travel. The challenge is that crime data reflects reported crime, not actual crime, which may differ. I will acknowledge this bias in my analysis."),
        ("Predicting Taxi Demand in Urban Areas",
         "I will predict taxi demand in different areas of a city using historical trip data. Features include time of day, day of week, and location. A regression model will be trained to predict the number of trip requests per area per hour. The NYC Taxi dataset will be used.",
         "Accurate demand prediction helps taxi companies position their vehicles to meet demand efficiently. This reduces passenger wait times and increases driver earnings. The challenge is that taxi demand is affected by many unpredictable events. My model will focus on regular patterns and will not capture unexpected events."),
        ("Recommending Jobs to Users Based on Their Profile",
         "My project recommends job listings to users based on their profile and past applications. I will use content-based filtering to match job descriptions with user skills listed in their profiles. The system will be evaluated using a publicly available recruitment dataset.",
         "Job seekers often struggle to find relevant opportunities in large job boards. A personalised recommendation system would make job searching more efficient. The challenge is that job descriptions and user profiles use different vocabularies which makes matching difficult. I will use text embedding techniques to address this semantic mismatch."),
        ("Analysing Customer Feedback with NLP",
         "I will analyse customer feedback text using natural language processing. The goal is to extract common themes and sentiments from product reviews. Topic modelling using LDA will identify the main topics that customers discuss. The results will be presented as word clouds and charts.",
         "Customer feedback contains valuable insights that can help businesses improve their products and services. Automated analysis makes it possible to process large volumes of feedback quickly. The challenge is that LDA topics can be difficult to interpret and may not perfectly align with business categories. Human review of the topics will be required."),
        ("Predicting Air Quality from Industrial Sensor Data",
         "My project predicts air quality measurements using data from industrial pollution sensors. I will use a regression model to predict PM2.5 levels based on wind direction, temperature, and industrial output indicators. The data will come from a publicly available air quality monitoring dataset.",
         "Air pollution is a serious health issue in many cities. Accurate prediction helps authorities issue timely health advisories. The challenge is that air quality is affected by many local factors that may not be captured in the data. I will focus on major predictors and acknowledge the model's limitations."),
        ("Detecting Credit Card Fraud Using Transaction Data",
         "I will build a fraud detection model using credit card transaction data. The Kaggle credit card fraud dataset will be used for training. The model will classify transactions as fraudulent or legitimate. Since the dataset is highly imbalanced, I will try oversampling techniques to improve detection.",
         "Credit card fraud is a major problem for banks and their customers. An automated detection system can flag suspicious transactions for review before they are processed. The main challenge is the severe class imbalance in fraud detection datasets. I will compare different sampling strategies to find the best approach."),
        ("Predicting Bicycle Sharing Demand",
         "This project predicts the demand for shared bicycles in a city. Features include weather conditions, time of day, and day of week. A regression model will be trained on the Capital Bikeshare dataset. The model will predict the number of rentals per hour.",
         "Bike sharing companies need to know where to position bikes to meet demand. Accurate forecasting reduces the cost of repositioning bikes and improves user satisfaction. The challenge is that demand is affected by many unpredictable factors including special events. I will build a baseline model and note where accuracy could be improved."),
        ("Automated Essay Scoring Using NLP",
         "I will build an automated essay scoring system using NLP features. I will use the ASAP dataset from Kaggle to train a regression model that predicts essay scores. Features will include sentence length, vocabulary richness, and grammatical correctness measured by a grammar checker.",
         "Automated essay scoring can reduce the workload on teachers and provide faster feedback to students. This is especially useful in large online courses with many submissions. The challenge is that essay quality involves complex judgments that are difficult to capture with simple NLP features. I will acknowledge the model's limitations and suggest it be used as a support tool rather than a replacement for human marking."),
        # --- additional low-performer proposals ---
        ("Building a Chatbot Using Python",
         "I want to build a chatbot that can answer questions. I will use Python and maybe a pre-trained language model. The chatbot will be trained on some FAQ data. Users can type questions and the bot will try to answer them.",
         "Chatbots are useful for businesses because they can handle customer queries automatically. This reduces the need for human staff to answer repetitive questions. The challenge is making the chatbot understand different ways of asking the same question. I will test the chatbot with sample questions and improve it over time."),
        ("Traffic Sign Recognition Using Deep Learning",
         "I will train a deep learning model to recognise traffic signs from images. I will use the German Traffic Sign Recognition Benchmark dataset. A CNN model will be trained to classify signs into different categories. The model will be evaluated on accuracy.",
         "Traffic sign recognition is important for autonomous driving systems. A reliable classifier could be used in driver assistance systems. The challenge is making the model robust to different weather and lighting conditions. I will test the model on a variety of images but acknowledge that real-world performance could be lower."),
        ("Fake News Detection Using Text Analysis",
         "My project detects fake news articles using machine learning. I will collect labelled fake and real news articles from a public dataset. Text features like word frequency and article length will be used. A classifier will be trained to distinguish fake from real news.",
         "Fake news spreads quickly on social media and can cause harm. A detector could help platforms filter misleading content. The challenge is that fake news can be very convincing and hard to detect. I will evaluate my model carefully and acknowledge cases where it fails."),
        ("Predicting Box Office Revenue for Movies",
         "I will predict how much money a movie will earn at the box office. Features will include budget, genre, release date, and cast popularity. I will train a regression model on historical movie data from IMDB or a similar source.",
         "Studios want to know whether a movie will be profitable before releasing it. A prediction model could help with investment decisions. The challenge is that box office performance depends on many unpredictable factors like reviews and word-of-mouth. My model will provide estimates with significant uncertainty."),
        ("Handwritten Digit Recognition with MNIST",
         "I will train a neural network to recognise handwritten digits using the MNIST dataset. This is a classic computer vision problem. I will compare a simple feedforward network with a convolutional neural network and report the accuracy of each.",
         "Handwritten digit recognition has applications in postal mail sorting and cheque processing. A high-accuracy recogniser reduces the need for manual reading. The challenge is that handwritten digits vary greatly between people. My model should perform well on the MNIST test set."),
        ("Sentiment Analysis for Restaurant Reviews",
         "I will classify restaurant reviews as positive or negative using sentiment analysis. A dataset of labelled restaurant reviews from Yelp will be used. I will apply a pre-trained sentiment model and also train my own classifier for comparison.",
         "Restaurants want to know if customers are satisfied with their food and service. Automated sentiment analysis helps process large volumes of reviews quickly. The challenge is that some reviews are mixed or ironic. I will try to handle these edge cases but expect some classification errors."),
        ("Object Detection in Street Images",
         "I will detect objects like cars, pedestrians, and cyclists in street images. I will use the COCO dataset and a pre-trained YOLO model. The model will be fine-tuned on a subset of street images. Detection performance will be measured using mAP.",
         "Object detection is important for autonomous vehicles and smart city applications. Accurate detection of pedestrians and vehicles improves road safety. The challenge is detecting objects in challenging conditions like night or rain. My model will be evaluated under normal conditions and limitations will be noted."),
        ("Customer Review Summarisation Using NLP",
         "I will build a system that summarises customer reviews for products. I will use an extractive summarisation approach to identify the most important sentences. The system will produce a short summary of what customers liked and disliked about a product.",
         "Reading hundreds of reviews is time-consuming for both businesses and customers. Automated summarisation provides a quick overview of customer opinions. The challenge is that important information can be spread across many reviews. My system will try to capture the most common themes."),
        ("Predicting Insurance Premium Amounts",
         "I will predict the insurance premium a customer should pay based on their profile. Features include age, medical history, and lifestyle factors. A regression model will be trained on a public insurance dataset. The model will be evaluated on prediction error.",
         "Insurance companies need to set fair premiums that reflect the actual risk of insuring a customer. A data-driven model could be more accurate than manual underwriting rules. The challenge is getting access to real insurance data. I will use a publicly available dataset as a substitute."),
        ("Classifying Toxic Comments Online",
         "My project classifies online comments as toxic or non-toxic. I will use the Jigsaw Toxic Comment Classification dataset from Kaggle. A text classifier will be trained using TF-IDF features and machine learning. Different classifiers will be compared.",
         "Toxic comments harm online communities and discourage participation. Automated toxicity detection can help platform moderators focus their efforts. The challenge is that toxicity is subjective and context-dependent. My model will focus on clearly toxic language and may struggle with subtle cases."),
        ("Predicting Electricity Demand Using Time Series",
         "I will predict electricity demand using historical consumption data. A time series forecasting model will be applied to hourly electricity usage data. I will compare ARIMA and a simple neural network. The forecasts will cover a 24-hour horizon.",
         "Electricity providers need accurate demand forecasts to plan generation capacity and avoid outages. Better forecasts reduce the cost of backup generation capacity. The challenge is that demand is affected by many unpredictable factors. My model will work best under normal conditions and may not handle unusual events well."),
        ("Face Detection in Photos Using OpenCV",
         "I will build a face detection system using OpenCV's Haar cascade classifier. The system will detect faces in photos and draw bounding boxes around them. I will test it on a variety of images and measure detection rate.",
         "Face detection is used in many applications including security cameras and photo organisation apps. An accurate detector makes these applications more reliable. The challenge is detecting faces at different angles and under poor lighting. I will use pre-trained models from OpenCV rather than training my own."),
        ("Predicting Heart Disease Using Medical Data",
         "I will predict heart disease using the UCI Heart Disease dataset. Features include age, blood pressure, cholesterol, and exercise-induced angina. Multiple classification algorithms will be compared and the best one selected based on accuracy and ROC AUC.",
         "Heart disease is a leading cause of death and early detection can save lives. A machine learning model could help doctors screen patients more efficiently. The challenge is that the dataset is relatively small and may not generalise well to all populations. I will discuss the limitations of the model and suggest it be used only as a screening tool."),
        ("E-Mail Classification into Categories",
         "I will classify emails into categories such as work, personal, promotional, and spam. I will use a text classification approach with TF-IDF features. The system will be trained on a labelled email dataset. Accuracy across categories will be reported.",
         "Automatically sorting emails saves users time and helps them focus on important messages. Many email clients already do this but my project will explore how well a custom model can do it. The challenge is building a representative labelled dataset. I will try to collect my own emails or use a publicly available email dataset."),
        ("Predicting Water Quality from Sensor Data",
         "My project predicts water quality using readings from water quality sensors. Features include pH, turbidity, and dissolved oxygen levels. A regression model will be trained to predict a water quality index score. The data will come from a public water quality monitoring dataset.",
         "Safe drinking water is essential for public health. Automated prediction of water quality problems allows authorities to respond quickly. The challenge is getting high-quality sensor data since sensors can malfunction and produce erroneous readings. I will include data cleaning steps to handle outliers before training the model."),
        ("Book Genre Classification Using Text Features",
         "I will classify books into genres based on their plot summaries. A text classification model will be trained on the CMU Movie Summary Corpus. TF-IDF or word embeddings will be used as features. Performance will be evaluated using precision, recall, and F1-score.",
         "Genre classification helps readers find books they like and helps bookstores organise their inventory. An automated classifier can process many books quickly. The challenge is that books can belong to multiple genres and genre boundaries are not always clear. My model will use single-label classification for simplicity."),
        ("Predicting Loan Default Risk",
         "I will predict the likelihood of a borrower defaulting on a loan. Features include credit history, income, and debt-to-income ratio. A logistic regression model and a decision tree will be compared. The model will be trained on the LendingClub loan dataset.",
         "Lenders need to assess the risk of lending money before approving a loan. A data-driven model can help make more objective and consistent decisions. The challenge is that the relationship between borrower features and default risk can be complex and non-linear. I will start with simple models and consider more complex ones if the results are unsatisfactory."),
        ("Detecting Abnormal Driving Behaviour from GPS Data",
         "I will detect abnormal driving behaviour such as speeding and sudden braking from GPS traces. I will use GPS data collected from vehicles and define abnormal behaviour based on acceleration and speed thresholds. A classification model will flag dangerous trips.",
         "Insurance companies and fleet managers want to identify risky driving behaviour. Automated detection allows for targeted feedback and training for at-risk drivers. The challenge is distinguishing genuine dangerous behaviour from normal driving in different road conditions. I will test the model in various scenarios and calibrate the thresholds carefully."),
        ("Building a Simple Fraud Detection System",
         "I will build a fraud detection system for online transactions. The dataset will be from Kaggle and contains credit card transactions labelled as fraudulent or legitimate. I will train a random forest classifier and evaluate its performance using precision and recall.",
         "Online fraud causes significant financial losses every year. An automated detection system can flag suspicious transactions for review. The main challenge is the severe class imbalance in the dataset since most transactions are legitimate. I will apply oversampling techniques and adjust the decision threshold to improve detection of the minority class."),
        ("Predicting Spotify Song Popularity",
         "I will predict the popularity of songs on Spotify using audio features like tempo, energy, danceability, and valence. A regression model will be trained on the Spotify dataset available on Kaggle. I will test different models and report the best results.",
         "Music producers and record labels want to know if a song will be popular before releasing it. A prediction model could help them make data-driven decisions about which songs to invest in. The challenge is that song popularity depends on many factors beyond audio features including marketing and cultural trends. My model will only use audio features as a starting point."),
        ("Classifying Diabetic Retinopathy from Fundus Images",
         "I will classify fundus eye images for signs of diabetic retinopathy. A pre-trained CNN will be fine-tuned on the Kaggle Diabetic Retinopathy dataset. The model will classify images into severity levels. Performance will be measured using a weighted kappa score.",
         "Diabetic retinopathy is a leading cause of blindness and early detection can prevent vision loss. An automated screening tool could help screen more patients in areas with limited access to ophthalmologists. The challenge is that the dataset contains many mislabelled images which could affect model quality. I will do my best to handle this but acknowledge it as a limitation."),
        ("Natural Language Processing for Legal Document Analysis",
         "I will apply NLP techniques to analyse legal documents. I will extract key information such as party names, dates, and contract terms from contract documents. Named entity recognition will be used to identify these elements automatically.",
         "Lawyers spend a lot of time reading and analysing documents. Automated extraction of key information could save significant time. The challenge is that legal language is complex and varies between jurisdictions. My model will be trained on a specific type of contract and may not generalise to all document types."),
        ("Predicting Air Passenger Numbers",
         "My project forecasts the number of airline passengers for a route using historical booking data. Time features like seasonality and public holidays will be included in the model. ARIMA and a neural network will be compared.",
         "Airlines need accurate passenger forecasts to plan staffing and fuel requirements. Better forecasts reduce operational costs and improve customer service. The challenge is that travel demand is affected by many external factors like fuel prices and geopolitical events. My model will focus on historical patterns and may not account for these external shocks."),
        ("Image Captioning Using a Pre-Trained Model",
         "I will build an image captioning system that generates text descriptions of images. I will use a pre-trained model from the HuggingFace library as the starting point. The system will take an image as input and generate a sentence describing its content.",
         "Automated image captioning is useful for accessibility applications and content management. It can help visually impaired users understand image content. The challenge is generating accurate and natural-sounding captions for diverse images. I will use existing pre-trained models rather than training from scratch due to computational constraints."),
        ("Predicting Crop Irrigation Needs",
         "This project predicts when crops need irrigation using weather and soil data. I will use temperature, humidity, and soil moisture readings as features. A machine learning model will predict whether irrigation is needed on a given day.",
         "Efficient irrigation reduces water waste and improves crop yields. An automated prediction system could help farmers manage water use more sustainably. The challenge is getting accurate soil moisture readings from sensors which can be unreliable in the field. I will use simulated data to test my model before testing with real sensor data."),
        ("Building a Recommendation System for Movies Using Matrix Factorisation",
         "I will implement a collaborative filtering recommendation system using matrix factorisation. The MovieLens 100K dataset will be used to train the model. The system will learn user and item latent factors and use them to predict ratings for unseen movies.",
         "Movie recommendations help users discover content they enjoy. Matrix factorisation is a well-established approach that has been used successfully in practice. The challenge is dealing with the cold-start problem for new users who have no rating history. I will use the most popular movies as a fallback recommendation for new users."),
        ("Analysing Public Health Data During COVID-19",
         "I will analyse COVID-19 epidemiological data to understand the spread of the virus. I will use publicly available data on cases, deaths, and vaccinations. Statistical analysis and visualisation will be used to identify trends and patterns over time.",
         "Understanding COVID-19 data helps public health officials make better policy decisions. Accurate analysis of trends can inform decisions about public health measures. The challenge is that data quality varies across countries and may not be fully comparable. I will focus on high-quality datasets and acknowledge data quality issues in my analysis."),
        ("Voice Assistant Using Speech Recognition",
         "I will build a simple voice assistant that can respond to voice commands. I will use a speech recognition library to convert speech to text and then process the text to determine what action to take. The assistant will handle basic commands like setting timers or answering simple questions.",
         "Voice assistants are increasingly popular as a hands-free interface for smart devices. Building one from scratch is a good way to learn about speech recognition and NLP. The challenge is achieving reliable speech recognition across different accents and in noisy environments. I will use a pre-built speech recognition service rather than training my own acoustic model."),
        ("Predicting Student Test Scores",
         "My project predicts student test scores based on demographic information and study habits. Features include study time, attendance, parental education level, and prior grades. A regression model will be trained and evaluated on the UCI Student Performance dataset.",
         "Identifying students who are likely to perform poorly allows teachers to provide additional support. Data-driven predictions could help allocate educational resources more effectively. The challenge is that student performance is affected by many factors not captured in the dataset. I will discuss the limitations of the model and suggest how it could be improved with more data."),
        ("Comparing Machine Learning Algorithms for Classification Tasks",
         "I will compare the performance of different machine learning algorithms on several classification datasets. Algorithms to be compared include logistic regression, decision tree, random forest, and SVM. Performance metrics like accuracy, precision, and recall will be computed for each algorithm.",
         "Comparing algorithms helps data scientists choose the right tool for a given problem. This project will provide a practical comparison that could serve as a reference for future work. The challenge is ensuring a fair comparison by using the same train/test split and preprocessing steps for all algorithms. I will follow best practices to make the comparison as fair as possible."),
        ("Analyse and Predict Customer Spending",
         "I will analyse customer spending data from a retail store to identify patterns. Clustering algorithms will group customers by spending behaviour. I will also build a regression model to predict how much a customer will spend on their next visit.",
         "Understanding how customers spend money helps retailers plan inventory and marketing. Predicting future spending allows for personalised promotions. The main challenge is getting sufficient transaction history for each customer. I will use a minimum transaction threshold to filter customers with too little data."),
        ("Predicting Hotel Booking Cancellations",
         "I will predict whether a hotel booking will be cancelled using booking features like lead time, room type, and special requests. A classification model will be trained on the Hotel Booking Demand dataset from Kaggle. Different algorithms will be compared.",
         "Hotels lose revenue when bookings are cancelled at the last minute. Predicting likely cancellations allows hotels to overbook strategically. The challenge is that the cancellation policy affects when customers cancel, which means the model may not generalise across different hotels with different policies. I will note this as a limitation."),
        ("Classifying Handwritten Characters",
         "I will build a handwritten character recognition system using a dataset of handwritten letters. A CNN will be trained to classify characters. I will evaluate the model on accuracy and compare it to published benchmarks.",
         "Handwritten character recognition is needed for digitalising handwritten documents. An accurate system could speed up document scanning workflows in offices and archives. The challenge is dealing with handwriting variation between people. My model will be trained on a diverse dataset to improve generalisation."),
        ("Predicting Traffic Volume at Intersections",
         "I will predict traffic volume at road intersections using historical sensor data. Features include time of day, day of week, and weather conditions. A regression model will predict the number of vehicles passing through an intersection per hour.",
         "Traffic volume prediction helps traffic management systems control signal timing more efficiently. Better signal control reduces congestion and improves traffic flow. The challenge is that traffic patterns change over time due to construction, events, and other disruptions. I will acknowledge that my model may not perform well during unusual events."),
        ("Sentiment Analysis of News Headlines",
         "I will classify news headlines as positive, negative, or neutral. I will use a pre-trained sentiment model and apply it to a dataset of news headlines. The results will show how news sentiment varies across different topics and time periods.",
         "News sentiment analysis can be used to track public mood and market sentiment over time. Investors use sentiment data to inform trading decisions. The challenge is that news sentiment is often ambiguous and depends on context. I will use a simple sentiment classifier and acknowledge its limitations for nuanced headlines."),
        ("Building a Simple Intrusion Detection System",
         "I will build an intrusion detection system using the KDD Cup dataset. Network traffic features will be used to classify connections as normal or attack. I will train a decision tree or random forest and evaluate performance.",
         "Network intrusion detection is important for cybersecurity. Automated detection can identify attacks faster than manual monitoring. The challenge is that the KDD dataset is old and modern attacks look different. I will note this as a key limitation and suggest using more recent datasets in future work."),
        ("Predicting Churn in a Subscription Service",
         "I will predict which customers of a subscription service are likely to cancel their subscription. Features include usage frequency, payment history, and customer support interactions. A binary classification model will be trained and the best model selected based on AUC.",
         "Retaining existing customers is cheaper than acquiring new ones. A churn prediction model allows the company to intervene before customers leave. The challenge is getting access to real subscription data which is often proprietary. I will use a publicly available telecom churn dataset as a proxy."),
        ("Predicting Sales for a Small Business",
         "I will forecast sales for a small business using historical sales records. Time series methods will be used to predict future sales. I will compare simple moving average with exponential smoothing. The forecasts will be evaluated on a held-out test period.",
         "Small businesses need to manage inventory and staffing based on expected sales. A simple forecasting model can help them plan ahead. The challenge is that small businesses often have limited historical data. I will work with whatever data is available and acknowledge that longer history would improve forecast accuracy."),
        ("Predicting Loan Approval Decisions",
         "I will predict whether a bank will approve a loan application. Features include income, credit score, and employment status. A classification model will be trained on a publicly available loan dataset. Fairness metrics will also be computed.",
         "Loan approval decisions have a big impact on people's lives. A transparent and consistent model could be fairer than human judgment. The challenge is ensuring the model does not discriminate against protected groups. I will compute fairness metrics and discuss any biases found in the data."),
        ("Recommending E-Learning Courses to Students",
         "I will build a course recommendation system for an e-learning platform. Students will be recommended courses based on their past enrolments and ratings. Collaborative filtering will be used to find students with similar learning interests.",
         "Students often struggle to find the right courses to advance their skills. A recommendation system can guide them toward relevant learning opportunities. The challenge is the cold-start problem when a new student has no enrolment history. I will recommend popular courses from the student's self-declared interest areas as a fallback."),
        ("Analysing Sports Injury Data",
         "I will analyse sports injury data to identify patterns and risk factors. I will use a publicly available dataset of sports injuries. Statistical analysis and machine learning will be used to identify which athletes are at highest risk of injury.",
         "Reducing sports injuries improves athlete wellbeing and team performance. Coaches can use risk predictions to modify training loads for high-risk athletes. The challenge is that injury data is often incomplete since minor injuries are not always reported. I will acknowledge this limitation in my analysis."),
        ("Building a Plagiarism Detection Tool",
         "I will build a tool that detects plagiarism in student essays. The tool will compare submitted essays against a database of known texts and flag similarities. Text similarity metrics like cosine similarity on TF-IDF vectors will be used.",
         "Plagiarism undermines academic integrity. An automated detection tool helps educators identify suspicious submissions quickly. The challenge is distinguishing paraphrase from plagiarism. My tool will flag high-similarity cases for human review rather than making automatic decisions."),
        ("Predicting Cryptocurrency Price Movements",
         "I will predict whether Bitcoin price will go up or down on the next day using historical price and volume data. A binary classification model will be trained on daily Bitcoin price data from CoinGecko. Technical indicators like moving averages will be used as features.",
         "Cryptocurrency markets are highly volatile and many traders are interested in prediction tools. A model that can predict price direction would be valuable for trading decisions. The challenge is that cryptocurrency markets are highly unpredictable and driven by sentiment and news that are not captured in price data alone. I will report the model's accuracy and discuss its practical limitations."),
        ("Building a Simple Chatbot for FAQs",
         "I will build a FAQ chatbot for a website. The chatbot will match user questions to a list of pre-written answers using text similarity. If no match is found, it will suggest the user contact support. I will implement this using Python.",
         "Many websites receive the same questions repeatedly. A chatbot that answers common questions reduces the load on customer support staff. The challenge is handling questions phrased differently from the pre-written FAQs. I will add multiple phrasings for common questions to improve matching."),
        ("Predicting Energy Star Ratings for Appliances",
         "I will predict the Energy Star efficiency rating of household appliances using their technical specifications. Features include power consumption, size, and brand. A classification model will assign appliances to Energy Star rating categories.",
         "Energy-efficient appliances reduce electricity bills and environmental impact. A prediction model could help consumers choose efficient products and help manufacturers design better products. The challenge is getting a comprehensive and up-to-date dataset of appliance specifications and ratings. I will use publicly available Energy Star programme data from the US EPA."),
        ("Sentiment Analysis of Political Speeches",
         "I will analyse the sentiment of political speeches using NLP. I will collect transcripts of speeches from public sources and apply a sentiment analyser. The goal is to see how sentiment varies across politicians and over time.",
         "Sentiment analysis of political speeches can reveal patterns in communication styles. Researchers and journalists could use this to analyse political rhetoric. The challenge is that political language is often nuanced and deliberately ambiguous. I will use a general-purpose sentiment model and acknowledge its limitations for political text."),
        ("Building a Number Plate Recognition System",
         "I will build a system to recognise vehicle number plates from images. I will use OCR to extract text from number plate regions detected in images. The system will be tested on a dataset of vehicle images with visible number plates.",
         "Number plate recognition has many applications including parking management and traffic law enforcement. An automated system can process many images quickly. The challenge is dealing with different number plate formats across states and countries. I will focus on Australian number plates and may struggle with plates from other regions."),
        ("Predicting Customer Satisfaction Scores",
         "I will predict customer satisfaction scores from customer service interaction data. Features include call duration, number of previous contacts, and resolution status. A regression model will predict the satisfaction score a customer is likely to give after an interaction.",
         "Customer satisfaction is a key metric for service businesses. Predicting satisfaction scores allows managers to identify and address poor customer experiences before they lead to churn. The challenge is that satisfaction is subjective and influenced by factors not captured in the interaction data. I will acknowledge these limitations and suggest additional data sources that could improve the model."),
        ("Analysing E-Commerce Purchase Patterns",
         "I will analyse purchase patterns from an e-commerce dataset. I will use the Online Retail dataset from the UCI repository. Basket analysis and visualisation will reveal which products are frequently bought together and which customer segments exist.",
         "Understanding purchase patterns helps retailers design better promotions and improve product placement. Association rule mining reveals which products tend to be bought together. The challenge is interpreting the rules and deciding which ones are actionable for the business. I will focus on rules with high confidence and support values."),
    ]

    for title, desc, biz in low_items:
        if len(records) >= 107:
            break
        records.append(_entry(len(records)+1, "Low", next(si), title, desc, biz))

    return records[:107]


# ---------------------------------------------------------------------------
# Exemplars (4, from outside the 214-proposal set)
# ---------------------------------------------------------------------------

EXEMPLARS = [
    {
        "id": "ex_high_1", "performance_group": "High", "score": 13,
        "text": (
            "Title: Predictive Modelling for Early Detection of Type-2 Diabetes\n\n"
            "Project Description:\n"
            "This project develops an ensemble ML pipeline to predict Type-2 diabetes onset using the NHANES longitudinal survey dataset. "
            "We combine XGBoost and a gradient-boosted neural network (TabNet) with SHAP-based feature attribution to surface the most clinically relevant risk factors. "
            "The data science team comprises a data engineer (ETL from NHANES API), an ML engineer (model training and deployment on AWS SageMaker), and a clinical informatician (domain validation).\n\n"
            "Business Model:\n"
            "Target beneficiaries are primary-care clinics and insurance providers seeking to reduce costly late-stage diabetes treatment. "
            "The value proposition is a 20-25% reduction in missed early diagnoses within the first year of deployment. "
            "Anticipated challenges include class imbalance (~8% positive rate), HIPAA compliance, and clinician adoption resistance. "
            "Mitigation strategies include SMOTE oversampling, de-identified federated data sharing, and a dashboard co-designed with GPs."
        ),
    },
    {
        "id": "ex_high_2", "performance_group": "High", "score": 14,
        "text": (
            "Title: NLP-Driven Analysis of Customer Churn in Subscription Services\n\n"
            "Project Description:\n"
            "We propose a multi-modal churn prediction system integrating structured transactional features with unstructured customer support ticket text. "
            "A BERT-based sentiment encoder will be fine-tuned on domain-specific ticket data, and its embeddings concatenated with behavioural features for a LightGBM classifier. "
            "Key data professionals include a data scientist (feature engineering, model selection), an NLP engineer (BERT fine-tuning), and a product analyst (business KPI alignment).\n\n"
            "Business Model:\n"
            "The primary beneficiary is the product team of a mid-size SaaS company with ~50,000 monthly subscribers. "
            "A 10% improvement in churn detection translates to ~$1.2 M in retained annual revenue. "
            "Challenges include concept drift as product offerings evolve, data labelling costs for support tickets, and privacy constraints on ticket content. "
            "We address these through a continual-learning retraining loop, active learning for annotation prioritisation, and role-based data access controls."
        ),
    },
    {
        "id": "ex_low_1", "performance_group": "Low", "score": 6,
        "text": (
            "Title: Social Media Analysis\n\n"
            "Project Description:\n"
            "I plan to collect data from Twitter and Instagram and analyse it using Python. "
            "I will look at what people are posting about and maybe find trends. "
            "Machine learning will be used to make predictions. The results will be useful.\n\n"
            "Business Model:\n"
            "Companies can use this to improve their marketing. There could be some challenges but we will deal with them when they come. "
            "Overall the project will provide value to stakeholders."
        ),
    },
    {
        "id": "ex_low_2", "performance_group": "Low", "score": 7,
        "text": (
            "Title: Weather Prediction Using Data\n\n"
            "Project Description:\n"
            "This project is about predicting the weather. We will get weather data from the internet and use it to train a model. "
            "The model will try to predict if it will rain or not. We will evaluate the model and see if it works.\n\n"
            "Business Model:\n"
            "People need to know the weather to plan their activities. If our predictions are accurate, it could help farmers and travellers. "
            "The main challenge is that weather is complex and hard to predict accurately."
        ),
    },
]


# ---------------------------------------------------------------------------
# Domain-specific expansion paragraphs
#
# The paper reports ~715 words per proposal on average.  The compact templates
# above average ~120-140 words.  Each proposal is expanded by inserting three
# Project-Description paragraphs and two Business-Model paragraphs drawn from
# domain-matched pools, targeting ~700-800 words for High performers and
# ~580-650 words for Low performers (overall mean ≈ 715 words).
#
# Seven domain categories cover all High-performer clusters.
# Low performers share a single generic (vague) expansion pool.
#
# Keyword matching uses whole-word regex boundaries (\b) to prevent false
# substring matches (e.g. "rna" inside "alternative", "icu" inside "particular").
# ---------------------------------------------------------------------------

import re as _re

# Whole-word keywords used to detect the domain of a proposal from its title.
# Rules:
#   - Use specific, unambiguous full words only (no 2-3 letter codes).
#   - Agriculture is separated from health to avoid "disease" cross-matching.
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "health":      ["hospital", "patient", "clinical", "medical", "sepsis",
                    "cancer", "diabetes", "radiology", "alzheimer", "chemotherapy",
                    "genomic", "tumour", "mammogram", "biomarker", "biomedical",
                    "pharmaceutical", "drug discovery", "protein", "single-cell",
                    "discharge summary", "blood product", "mental health"],
    "agriculture": ["crop", "yield", "irrigation", "livestock", "farm", "weed",
                    "plant disease", "soil", "precision farming", "agri"],
    "finance":     ["fraud", "credit", "insurance", "trading", "portfolio", "loan",
                    "bank", "financial", "mortgage", "invoice", "tariff",
                    "anti-money", "revenue management", "pricing"],
    "text":        ["language model", "sentiment", "contract review", "summarisation",
                    "transcript", "essay scoring", "misinformation", "named entity",
                    "question answering", "chatbot", "citation", "grant matching",
                    "plagiarism", "fake news", "news recommendation",
                    "playlist", "music recommendation"],
    "vision":      ["image", "visual inspection", "object detection", "segmentation",
                    "satellite imagery", "uav imagery", "multispectral", "lidar",
                    "defect detection", "crowd density", "gesture recognition",
                    "number plate", "pcb", "mammogram", "fundus", "retinopathy"],
    "systems":     ["recommendation system", "supply chain", "demand forecasting",
                    "vehicle routing", "logistics", "inventory", "warehouse",
                    "smart building", "occupancy", "traffic signal", "crime hotspot",
                    "flood inundation", "maritime vessel", "intrusion detection",
                    "phishing", "autonomous", "robot", "ride-sharing",
                    "churn prediction", "subscriber"],
    "environment": ["climate", "carbon footprint", "wildfire", "air quality",
                    "rainfall forecasting", "renewable energy", "wind turbine",
                    "electric vehicle", "water quality", "solar panel output",
                    "energy dispatch", "smart grid"],
}

# --- High-performer expansion paragraphs (3 desc + 2 biz per domain) ---

_HIGH_EXPAND: dict[str, dict[str, list[str]]] = {
    "health": {
        "desc": [
            ("All raw data assets will be catalogued with schema validation and range "
             "checks at ingestion, with versioned snapshots stored in a secure, access-"
             "controlled repository on AWS S3. A dedicated de-identification stage will "
             "replace all direct identifiers with surrogate keys before any downstream "
             "processing, with the mapping table held in a secrets manager accessible only "
             "to the data-engineering role. Preprocessing steps will be implemented as a "
             "reproducible pipeline, producing a consistent representation consumed by both "
             "training and inference workflows. All transformations will be logged to "
             "maintain a complete data-lineage record required for regulatory audit."),
            ("Model selection will follow a pre-registered experimental protocol with "
             "appropriate cross-validation strategy for the data type — stratified k-fold "
             "for independent samples, or temporal holdout for time-ordered data. "
             "Hyperparameter search will be conducted via Bayesian optimisation (Optuna), "
             "with the final model chosen by a composite score weighting predictive "
             "performance, calibration, and inference latency. Baselines will include "
             "established domain-appropriate comparators and the current system in use. "
             "Statistical significance of improvements will be assessed using Wilcoxon "
             "signed-rank tests with Bonferroni correction. Explanation outputs — SHAP "
             "summary plots and individual conditional expectation curves — will be "
             "generated for the final model to support regulatory review and "
             "domain-expert communication."),
            ("Deployment will follow a blue-green release strategy with automated rollback "
             "triggered if AUROC on the live monitoring cohort drops below the pre-specified "
             "alarm threshold. A population stability index (PSI) monitor will flag "
             "covariate drift weekly; a concept-drift detector based on a Kolmogorov-Smirnov "
             "test on prediction distributions will trigger retraining when the p-value "
             "exceeds 0.05 for three consecutive weeks. Model predictions, confidence "
             "intervals, and top contributing features will be surfaced via an operational "
             "dashboard integrated with the existing workflow system, presenting outputs in "
             "plain language to support decision-making by domain experts. Governance policy "
             "mandates human review of all high-stakes decisions informed by the model, "
             "ensuring the system operates as a decision-support tool rather than "
             "an autonomous decision-maker."),
        ],
        "biz": [
            ("The go-to-market strategy begins with a 12-month paid pilot at two anchor "
             "healthcare organisations, providing structured case studies and quantified "
             "ROI evidence for broader commercialisation. Pricing follows an annual SaaS "
             "model with contract values scaled to organisation size and usage volume, "
             "generating predictable recurring revenue with low churn risk. A clinical "
             "advisory board comprising practising specialists, a health economist, and a "
             "patient-advocate representative will review system design, training-data "
             "composition, and output distributions before deployment and annually "
             "thereafter. The total addressable market across Australian and New Zealand "
             "healthcare organisations exceeds $220 M per year and is growing at 14% "
             "annually, driven by increasing regulatory pressure to demonstrate "
             "data-driven quality improvement."),
            ("Ethical and regulatory compliance will be treated as a design constraint "
             "rather than an afterthought. The system will be assessed against the "
             "Australian Digital Health Agency's AI in Healthcare Framework before "
             "submission to the Therapeutic Goods Administration for Software as a Medical "
             "Device (SaMD) classification. A pre-specified subgroup analysis across age, "
             "sex, Indigenous status, and socioeconomic quintile will be published in a "
             "transparency report to demonstrate equitable performance. Any performance gap "
             "exceeding a pre-agreed threshold will trigger an automatic suppression of the "
             "model output for that subgroup and escalation to the clinical governance "
             "committee. Indemnity insurance covering AI-assisted clinical decisions will "
             "be secured before production go-live."),
        ],
    },
    "finance": {
        "desc": [
            ("Raw transactional data will be ingested from core banking or CRM systems "
             "via secure SFTP or REST API, encrypted in transit using TLS 1.3, and stored "
             "in a role-access-controlled data warehouse. A data-quality framework will "
             "enforce referential integrity, detect duplicate records, and flag statistical "
             "outliers using an Isolation Forest pre-screen before any feature engineering "
             "begins. Feature pipelines will run in a scheduled Airflow DAG, producing "
             "aggregated behavioural signals at daily, weekly, and 90-day rolling windows. "
             "All feature definitions will be registered in a centralised feature store "
             "(Feast) to prevent training-serving skew. Sensitive fields such as account "
             "numbers will be tokenised using format-preserving encryption prior to model "
             "input, ensuring compliance with PCI-DSS requirements throughout the pipeline."),
            ("The modelling approach will implement a champion-challenger architecture: "
             "the current production model (champion) is continuously compared against "
             "newly trained candidates (challengers) on a 10% traffic shadow deployment "
             "before full promotion. Walk-forward time-series cross-validation will be "
             "used in place of random split to respect temporal ordering and prevent "
             "look-ahead bias. Calibration of probability outputs will be verified using "
             "reliability diagrams and expected calibration error, ensuring that a "
             "predicted risk of 0.30 corresponds to an observed default rate of "
             "approximately 30% in the held-out cohort. SHAP-based explanation "
             "pipelines will generate per-customer feature attributions stored in the "
             "data warehouse for audit and regulatory inquiry response within the "
             "timeframe mandated by APRA Prudential Standard CPS 220."),
            ("Model monitoring will track four signal classes in production: data drift "
             "(PSI on input feature distributions), concept drift (AUROC on a rolling "
             "30-day labelled window), business-metric drift (approval rate and default "
             "rate versus monthly budget), and fairness drift (demographic parity gap "
             "across protected attribute groups). An automated alerting pipeline will "
             "page the model-risk team when any signal crosses its threshold. A quarterly "
             "independent model validation will be conducted by the internal model-risk "
             "function, reviewing training data composition, feature selection rationale, "
             "backtesting assumptions, and sensitivity to stress scenarios specified by "
             "the APRA scenario library. Full model documentation in APRA's prescribed "
             "format will be maintained and updated within 10 business days of any "
             "material model change."),
        ],
        "biz": [
            ("The solution targets mid-tier Australian financial services organisations "
             "that currently rely on off-the-shelf models with limited customisation. "
             "A SaaS licensing model with a minimum annual commitment aligns vendor "
             "incentives with customer usage growth. The first 12 months will focus on "
             "two anchor clients selected for their willingness to share labelled "
             "historical data and participate in a co-development advisory panel. "
             "Resulting case studies will form the core of the sales collateral for the "
             "next phase of growth. The total addressable market across Australian "
             "financial services AI is estimated at $340 M per year in analytics spend, "
             "with a serviceable obtainable market of $45 M in the first three years "
             "based on a 10% penetration assumption among the 50 largest organisations."),
            ("Regulatory compliance is a key selling point in the financial services "
             "sector. The system will provide auditable model outputs and explanation "
             "reports satisfying APRA Prudential Standard CPS 220 model-risk governance "
             "requirements. Model-performance summary reports will be generated in a "
             "format ready for submission to APRA and ASIC on request. Key-person risk "
             "in the modelling team will be mitigated through comprehensive model cards, "
             "automated retraining pipelines, and a 90-day knowledge-transfer programme "
             "for each new team member. Intellectual property will be protected through "
             "a combination of trade-secret designation for core feature-engineering "
             "libraries and copyright registration for novel software components."),
        ],
    },
    "text": {
        "desc": [
            ("Text preprocessing will use a reproducible spaCy pipeline covering "
             "sentence segmentation, tokenisation, lemmatisation, named-entity "
             "recognition, and dependency parsing, with pipeline versions pinned in "
             "a requirements file to ensure reproducibility. For transformer-based "
             "models, tokenisation will follow the pre-trained vocabulary of the "
             "chosen checkpoint, with maximum sequence lengths set to cover the 99th "
             "percentile of document lengths in the training corpus. Documents exceeding "
             "the context window will be handled via a sliding-window approach with "
             "stride equal to half the window size, with predictions aggregated by "
             "majority vote across windows. All preprocessing decisions will be "
             "documented in a data card accompanying the dataset, following the "
             "Datasheets for Datasets template to facilitate reproducibility and "
             "responsible reuse by future researchers."),
            ("Fine-tuning will follow a three-phase curriculum: (1) continued "
             "domain pre-training on unlabelled in-domain text for 3 epochs, "
             "(2) task-adaptive fine-tuning on the labelled training split for up to "
             "10 epochs with early stopping on validation loss, and (3) a final "
             "calibration step using temperature scaling on the validation set. "
             "Learning rates will be swept over [1e-5, 3e-5, 5e-5] using a linear "
             "warmup schedule over 6% of total training steps followed by cosine "
             "decay. Evaluation will use macro-averaged F1 for classification tasks "
             "and BERTScore alongside ROUGE-L for generation tasks, with human "
             "evaluation on a stratified sample of 200 outputs assessed by two "
             "independent domain-expert annotators achieving Cohen's κ ≥ 0.75 before "
             "annotations are used for model selection."),
            ("The inference service will be deployed as a containerised FastAPI "
             "application, with transformer models exported to ONNX format and "
             "quantised to INT8 via ONNX Runtime, achieving a 3× reduction in "
             "memory footprint and 2.5× throughput improvement with less than 0.5% "
             "accuracy degradation on the validation set. An A/B testing framework "
             "using a feature-flag service will allow controlled rollout to 5% of "
             "production traffic before full promotion. Model outputs will be logged "
             "to a structured data store for offline analysis of failure modes, "
             "with a weekly review cadence involving a domain-expert spot-check of "
             "50 randomly sampled predictions flagged as low-confidence by the "
             "model's softmax entropy. Feedback from this review will feed a "
             "human-in-the-loop retraining queue."),
        ],
        "biz": [
            ("The primary revenue stream is an API-based SaaS subscription, with volume "
             "discounts at 100 K, 500 K, and 1 M processed items per month. Enterprise "
             "customers with data-residency requirements will be offered an on-premise "
             "deployment option at a higher per-seat licence fee. The go-to-market motion "
             "begins with two anchor enterprise clients who co-develop the product in "
             "exchange for reduced first-year pricing, providing validated case studies "
             "for the next sales cycle. A freemium tier will drive self-serve adoption "
             "among individual practitioners and research teams, serving as a top-of-funnel "
             "pipeline for enterprise sales conversations. Customer acquisition cost is "
             "estimated at $4,200 per enterprise account based on comparable SaaS "
             "benchmarks, against a projected 3-year LTV of $62,000."),
            ("Data privacy and intellectual-property protection are central to customer "
             "trust in this market. Customer documents will never be retained beyond "
             "the processing session; all inference is stateless, with no logging of "
             "document content to persistent storage. Customers in the EU and Australia "
             "will benefit from in-region inference nodes to satisfy data-residency "
             "requirements under GDPR and the Privacy Act 1988 respectively. A "
             "responsible-AI policy will be published on the company website specifying "
             "prohibited use cases (surveillance, discriminatory profiling) and the "
             "processes for customer escalation when model outputs are disputed. "
             "Two independent red-team exercises per year will test the system for "
             "prompt-injection and data-extraction vulnerabilities, with findings "
             "disclosed and remediated within 30 days."),
        ],
    },
    "vision": {
        "desc": [
            ("Image data will be collected under a standardised acquisition protocol "
             "specifying camera angle, spatial resolution, and environmental conditions "
             "appropriate to the deployment setting. Raw images will be stored in lossless "
             "PNG format with metadata stripped to remove device identifiers before "
             "annotation. The annotation pipeline will use Label Studio with a three-"
             "annotator consensus scheme; bounding boxes, density maps, or segmentation "
             "masks with inter-annotator IoU below 0.75 will be escalated to a domain-"
             "expert adjudicator. Data augmentation will include random horizontal and "
             "vertical flips, rotation up to ±15°, colour-jitter, and Gaussian noise "
             "injection, implemented via Albumentations to ensure reproducibility "
             "from a fixed random seed."),
            ("Architecture selection will follow a systematic benchmark on a held-out "
             "validation set, comparing EfficientDet, YOLOv9, and a ViT-based detector "
             "across four operating points on the precision-recall curve. Transfer "
             "learning will initialise backbone weights from ImageNet-21K pretraining, "
             "with the classification head trained from scratch to avoid negative transfer "
             "of label semantics. Mixed-precision training (FP16 forward pass, FP32 "
             "gradient accumulation) will be used to halve GPU memory consumption and "
             "increase throughput by approximately 1.8×. Final model selection will "
             "weight F1 score, average inference time per image, and model size on disk "
             "to balance accuracy against deployment constraints on edge hardware. "
             "GradCAM saliency maps will be computed for a stratified sample of 500 "
             "validation images to verify that the model is attending to semantically "
             "relevant regions."),
            ("Edge deployment will use NVIDIA TensorRT for model optimisation, "
             "with INT8 post-training quantisation validated to within 1% mAP of the "
             "FP32 baseline on the validation set. A continuous integration pipeline "
             "will rebuild and regression-test the TensorRT engine after every model "
             "update, with automated rollback if throughput drops below the specified "
             "SLA of 60 FPS on the target hardware. Camera health monitoring will "
             "track lens fouling via a no-reference image sharpness metric (Laplacian "
             "variance), triggering a maintenance alert when the score falls below a "
             "calibrated threshold. All predictions, confidence scores, and anomaly "
             "flags will be persisted in a time-series database (InfluxDB) enabling "
             "retrospective analysis of false-negative clusters by scene type, "
             "deployment location, and operational condition."),
        ],
        "biz": [
            ("The pricing model targets a three-year payback period for the customer, "
             "with Year 1 costs covered by the first detectable reduction in error rate "
             "or operational efficiency gain. Hardware (cameras, edge GPUs) will be "
             "offered under a lease-to-own arrangement to minimise the upfront capital "
             "barrier for mid-size operators. Software will be licensed under an annual "
             "SaaS agreement covering model updates, remote monitoring, and a 99.5% "
             "uptime SLA backed by a service credit regime. Professional-services "
             "integration packages will connect the system to existing operational "
             "platforms via REST APIs. A network-effects moat will be cultivated by "
             "aggregating anonymised imagery across customers (with consent) to "
             "continually improve the shared backbone model while keeping "
             "customer-specific fine-tuned heads private."),
            ("Quality assurance and data-security requirements are a standard part of "
             "the procurement process in the target markets. The system will be "
             "validated through documented Installation Qualification and Operational "
             "Qualification (IQ/OQ) packages appropriate to the deployment context. "
             "Cybersecurity of edge inference nodes will be hardened in accordance "
             "with IEC 62443 industrial network security standards, including network "
             "segmentation, encrypted telemetry, and quarterly penetration testing. "
             "Sensitive imagery or data that could reveal proprietary details will be "
             "processed on-premise, with only aggregate statistics transmitted to the "
             "vendor's monitoring cloud. ISO 27001 certification will be completed in "
             "Year 1 to satisfy enterprise procurement requirements."),
        ],
    },
    "systems": {
        "desc": [
            ("The data infrastructure will support both batch and streaming ingestion "
             "patterns depending on the latency requirements of the use case. Historical "
             "data will be stored in a versioned, partitioned data lake on S3 and replayed "
             "to populate the feature store during initial model training. A centralised "
             "feature store will ensure consistent feature definitions across training and "
             "serving, preventing training-serving skew. Automated data-quality tests will "
             "gate every ingestion batch, rejecting loads with null rates above 2% or "
             "value distributions that deviate more than three standard deviations from "
             "the trailing 90-day baseline. All data transformations will be versioned "
             "and logged to support full reproducibility and audit."),
            ("The system will be evaluated using a held-out historical period to simulate "
             "production conditions, measuring performance improvement against the current "
             "heuristic or rule-based baseline used in production. For systems supporting "
             "online decisions, an A/B test will be run for a minimum of four weeks with "
             "10% treatment traffic before full promotion, using a sequential testing "
             "approach (mSPRT) to allow early stopping when statistical significance is "
             "reached. Causal inference techniques will be applied where needed to adjust "
             "for confounders in observational data. All experiment configurations, "
             "hypotheses, and analysis plans will be pre-registered in an internal "
             "experiment registry before the experiment launches."),
            ("Operational resilience will be ensured through redundant serving nodes "
             "behind a load balancer with health-check-based automatic failover, "
             "targeting 99.9% availability. The system will degrade gracefully to a "
             "rule-based fallback when the ML service is unavailable. Chaos engineering "
             "tests injecting latency, packet loss, and dependency failures will be "
             "conducted quarterly in a staging environment to validate failover behaviour. "
             "All infrastructure will be defined as code using Terraform, enabling "
             "reproducible environment provisioning and disaster-recovery replication "
             "in a secondary AWS region within a 4-hour RTO target."),
        ],
        "biz": [
            ("The platform will be positioned as a composable intelligence layer that "
             "integrates into existing operational systems via REST and GraphQL APIs, "
             "reducing the implementation barrier for customers who do not wish to "
             "replace their current infrastructure. Pricing will follow a consumption "
             "model (per API call or per decision) with a minimum monthly commitment "
             "that provides revenue predictability. The first three enterprise clients "
             "will be onboarded under a design-partner arrangement with reduced fees "
             "in exchange for weekly feedback sessions and the right to use anonymised "
             "performance data in marketing materials. The competitive moat will be "
             "built through proprietary training data accumulated via network effects, "
             "a continuously improving model that compounds accuracy advantages over "
             "competitors using static models, and deep integrations with four major "
             "ERP and WMS platforms that create meaningful switching costs."),
            ("Privacy and security due-diligence is a standard requirement for "
             "enterprise procurement in this sector. The system will complete ISO 27001 "
             "certification in Year 1 and SOC 2 Type II attestation in Year 2. "
             "Customer data will be logically isolated in separate database schemas "
             "with encryption at rest (AES-256) and field-level encryption for "
             "highly sensitive attributes. A vendor security questionnaire (based on "
             "the CAIQ-Lite standard) will be maintained and made available to "
             "procurement teams on request, pre-answering the most common questions "
             "to accelerate the sales cycle. Penetration testing will be conducted "
             "annually by a CREST-certified third party, with critical findings "
             "remediated within 5 business days and results summarised in a "
             "security transparency report."),
        ],
    },
    "environment": {
        "desc": [
            ("Geospatial and temporal data will be managed using a STAC (SpatioTemporal "
             "Asset Catalog) compliant data lake, enabling efficient discovery and "
             "retrieval of satellite, reanalysis, and sensor datasets by spatial bounding "
             "box and time range. Preprocessing will include radiometric calibration, "
             "atmospheric correction using the Sen2Cor processor for optical imagery, "
             "and co-registration of multi-source data to a common 10 m UTM grid. "
             "Cloud masking will use the s2cloudless machine-learning algorithm, with "
             "contaminated pixels interpolated from the nearest cloud-free observation "
             "within a 16-day window. All processed rasters will be stored in "
             "Cloud-Optimised GeoTIFF format to support partial reads and efficient "
             "tile-based parallel processing in the modelling pipeline."),
            ("Model training will use stratified spatial cross-validation with "
             "geographically contiguous folds to prevent spatial auto-correlation from "
             "inflating performance estimates — a common failure mode in geospatial ML "
             "studies. Prediction uncertainty will be quantified using a Monte Carlo "
             "dropout ensemble, with the inter-quantile range of the ensemble used "
             "to produce 90% prediction intervals reported alongside point estimates "
             "in all operational outputs. Skill scores will be computed relative to "
             "climatological and persistence baselines to contextualise model value "
             "in terms familiar to operational forecasters and domain scientists. "
             "Sensitivity analyses will test robustness to missing-data scenarios "
             "(simulating sensor outages at 5%, 10%, and 20% missing rates) to "
             "characterise operational reliability under realistic deployment conditions."),
            ("The operational system will ingest new observations on a daily automated "
             "schedule triggered by satellite overpass notifications from the Copernicus "
             "Data Space API. Updated predictions will be published to a public-facing "
             "OGC Web Map Tile Service (WMTS) within 2 hours of data availability, "
             "enabling integration with third-party GIS platforms used by government "
             "agencies and commercial customers. A model health dashboard will track "
             "data timeliness, preprocessing success rates, and prediction-versus-observation "
             "skill on a rolling 30-day window, with automated email alerts when skill "
             "degrades below operational thresholds. Annual model retraining incorporating "
             "the most recent 12 months of observational data will manage distribution "
             "shift arising from climate trend non-stationarity."),
        ],
        "biz": [
            ("Revenue will be generated through three channels: (1) government contracts "
             "with state and federal environmental agencies for operational forecasting "
             "services (anchor revenue, multi-year), (2) commercial API subscriptions "
             "for agribusiness, insurance, and energy companies requiring location-specific "
             "environmental intelligence, and (3) a professional-services stream for "
             "custom model development and integration projects. Government contracts "
             "will be pursued through open procurement panels (e.g., the NSW Digital "
             "Government Panel), while commercial subscriptions will be sold through "
             "a self-serve portal with a free tier capped at 1 000 API calls per month "
             "to support adoption by research institutions and small agribusinesses. "
             "The total addressable market for environmental AI services in Australia "
             "is estimated at $280 M annually, growing at 18% per year driven by "
             "increasing regulatory requirements for climate-risk disclosure."),
            ("Responsible deployment requires transparency about model skill limitations "
             "at different spatial scales, temporal horizons, and under extreme-event "
             "conditions not well represented in the training data. All operational "
             "outputs will include a model-skill footnote, a link to the publicly "
             "accessible verification dashboard, and guidance on appropriate versus "
             "inappropriate uses of the predictions. An open-science commitment will "
             "see training code, pre-trained model weights, and a subset of benchmark "
             "data published on Zenodo under a CC-BY licence within 12 months of "
             "commercial launch, supporting independent validation by the scientific "
             "community and building credibility with government customers who conduct "
             "due-diligence literature reviews. Climate-equity considerations will be "
             "addressed through a discounted-access programme for Pacific island "
             "nations and low-income agricultural communities."),
        ],
    },
}

# Agriculture-specific expansion pool (separated from health to avoid cross-contamination)
_HIGH_EXPAND["agriculture"] = {
    "desc": [
        ("Data will be collected from sensors, imaging devices, or measurement "
         "instruments appropriate to the agricultural setting — which may include "
         "fixed IoT sensor arrays, handheld scanners, or vehicle-mounted equipment. "
         "Raw readings will be quality-controlled using range checks calibrated "
         "against reference measurements, with missing intervals filled via linear "
         "interpolation for gaps shorter than 6 hours. Data will be stored in "
         "Parquet format partitioned by season and site identifier, and all "
         "collection protocols will be documented in a standard operating procedure "
         "shared with operators to ensure consistent data quality across sites "
         "and seasons."),
        ("Model performance will be evaluated using a held-out test set drawn from "
         "sites not seen during training, to prevent data leakage across spatially "
         "or temporally correlated observations. Metrics will be reported separately "
         "for each application context and operational condition (e.g., breed, "
         "species, season, or farm type) to capture variation in model reliability. "
         "Baseline comparisons will include the current manual assessment practice "
         "and a simple historical average model. Uncertainty quantification using "
         "a bootstrap ensemble will produce 90% prediction intervals alongside "
         "point estimates, enabling operators to make risk-aware decisions when "
         "model confidence is low."),
        ("The system will be deployable on standard tablets and laptops used in "
         "agricultural operations, without requiring a persistent internet connection. "
         "A lightweight quantised model supports on-device inference, with updates "
         "synced when connectivity is available. Outputs will be presented in a "
         "plain-language interface interpretable by agricultural professionals "
         "without data science training. Model updates incorporating the latest "
         "season's observations will be released annually via an OTA update "
         "mechanism, and operators will receive training on interpreting confidence "
         "indicators and flagging anomalous predictions for expert review."),
    ],
    "biz": [
        ("The solution will be commercialised through a subscription model with "
         "pricing proportional to the scale of the operation — for example, per "
         "animal, per site, or per season — aligning revenue with the agricultural "
         "calendar. Distribution will leverage existing agricultural advisory "
         "networks and cooperative relationships, reducing customer acquisition "
         "costs by embedding the tool within existing workflows. A pilot programme "
         "with five cooperating operations in Year 1 will generate outcome data to "
         "validate ROI claims and build the case-study portfolio needed for broader "
         "adoption. The total addressable market across Australian agriculture is "
         "estimated at $90 M per year in precision agriculture analytics, "
         "growing at 16% annually."),
        ("Producer trust requires transparency about model limitations and clear "
         "guidance on when expert judgment should override model recommendations. "
         "All outputs will include a confidence indicator and a plain-language "
         "explanation of the key factors driving each recommendation. An independent "
         "expert review panel will assess system outputs against best-practice "
         "guidelines and publish a seasonal performance report. Data ownership will "
         "remain with the producer; raw operational data will never be shared with "
         "third parties without explicit consent, and producers may request deletion "
         "of their data at any time. Compliance with the Australian Privacy Act 1988 "
         "will be maintained throughout the data lifecycle."),
    ],
}

# Fallback for proposals that don't match a specific domain keyword
_HIGH_EXPAND["general"] = {
    "desc": [
        ("Raw data will be ingested via automated pipelines incorporating schema "
         "validation, null-rate checks, and statistical outlier detection before "
         "any downstream processing. Versioned snapshots will be stored in a "
         "Parquet data lake, with all transformations logged in a lineage graph "
         "to support reproducibility and audit. Feature engineering will be "
         "implemented as a reusable Scikit-learn Pipeline, ensuring identical "
         "transformations are applied to training, validation, and inference data "
         "and preventing data-leakage bugs common in ad hoc preprocessing. "
         "The final feature set will be registered in a centralised feature store "
         "with semantic versioning, enabling consistent consumption across "
         "experiments and preventing training-serving skew in production."),
        ("Model selection will follow a rigorous protocol: stratified five-fold "
         "cross-validation, Bayesian hyperparameter search via Optuna, and final "
         "model chosen by a composite score balancing predictive performance, "
         "inference latency, and memory footprint. Baseline comparisons will "
         "include a rule-based heuristic (representing the current production "
         "system), a logistic regression, and a gradient-boosted decision tree. "
         "Statistical significance of improvements will be assessed using "
         "Wilcoxon signed-rank tests with Bonferroni correction for multiple "
         "comparisons. SHAP feature attributions and partial dependence plots "
         "will be generated for all evaluated models to ensure interpretability "
         "requirements are met before any deployment recommendation is made."),
        ("Deployment will use a containerised micro-service architecture with "
         "a CI/CD pipeline (GitHub Actions) running unit tests, integration tests, "
         "and automated model evaluation on every pull request. A canary release "
         "strategy will expose 5% of traffic to the new model before full "
         "promotion, with automated rollback triggered by a business-metric "
         "regression detector. Production monitoring will track data-drift (PSI), "
         "concept-drift (rolling AUROC), and system-level metrics (p99 latency, "
         "error rate) with on-call alerting for threshold breaches. "
         "Quarterly model reviews will reassess training-data currency, "
         "feature relevance, and fairness metrics, with findings documented "
         "in a model card updated in the central model registry."),
    ],
    "biz": [
        ("The go-to-market strategy focuses on a land-and-expand motion: an "
         "initial paid pilot with two anchor clients provides quantified ROI "
         "evidence and reference customers for broader commercial outreach. "
         "A value-based SaaS pricing model aligns vendor incentives with "
         "measurable business outcomes. The total addressable market in "
         "Australia is estimated at $150–250 M per year in AI-driven analytics "
         "for this sector, growing at 12% annually. A Series A funding round "
         "will be sought after the pilot phase to fund sales headcount, "
         "infrastructure scaling, and expansion into additional market segments. "
         "Key intellectual property will be protected through trade-secret "
         "designation for core algorithms and copyright registration for "
         "novel software components."),
        ("Responsible deployment requires a human-in-the-loop review process "
         "for all high-stakes decisions informed by the system. An ethics "
         "advisory panel comprising domain experts, a data-ethics researcher, "
         "and a consumer advocate will review system design and output "
         "distributions before go-live and annually thereafter. ISO 27001 "
         "certification will be completed in Year 1 to satisfy enterprise "
         "procurement requirements. A quarterly transparency report covering "
         "model performance, error-rate trends, fairness metrics, and "
         "any identified biases will be published on the company website. "
         "Customer data will be processed under a data-processing agreement "
         "that prohibits secondary use and ensures deletion upon contract "
         "termination."),
    ],
}

# --- Low-performer expansion paragraphs (shared across all domains) ---

_LOW_EXPAND_DESC: list[str] = [
    ("Once I have the data for this project, I will load it into a Python environment "
     "using the pandas library and begin with exploratory data analysis to understand "
     "the structure of the data, check for missing values, and identify any obvious "
     "outliers or data quality issues. Missing values will be handled using simple "
     "imputation strategies such as filling with the column mean or median, depending "
     "on the distribution of the feature. Outliers will be investigated manually and "
     "removed if they appear to be data entry errors rather than genuine observations. "
     "I will produce summary statistics and visualisations to confirm my understanding "
     "of the data before moving on to the modelling phase."),
    ("For the modelling phase, I plan to try several different machine learning "
     "algorithms and compare their performance. I will use the scikit-learn library "
     "in Python because it provides easy-to-use implementations of many standard "
     "algorithms. I will start with simple models like logistic regression or "
     "linear regression as a baseline and then try more complex models such as "
     "decision trees, random forests, and gradient boosting. I will use "
     "cross-validation to evaluate each model and avoid overfitting to the training "
     "data. Hyperparameter tuning will be done using grid search or random search "
     "depending on how many parameters there are. The best-performing model will "
     "be selected based on the validation set performance."),
    ("To evaluate the performance of my model, I will use standard evaluation "
     "metrics appropriate to the task. For classification problems I will report "
     "accuracy, precision, recall, and F1-score, and plot a confusion matrix "
     "to visualise where the model makes mistakes. For regression problems I will "
     "use mean absolute error and root mean squared error. I will split the data "
     "into a training set and a test set, making sure not to use the test set "
     "during model development to get an unbiased estimate of performance. "
     "I will compare the final model's performance against a simple baseline "
     "to confirm that the machine learning approach actually provides a meaningful "
     "improvement. The results will be presented in tables and charts in the "
     "project report."),
]

_LOW_EXPAND_BIZ: list[str] = [
    ("If the project produces good results, I think it could potentially be useful "
     "in a real-world context. The main beneficiaries would be the organisations "
     "or individuals who currently have to deal with this problem manually. "
     "By automating some of the process using machine learning, they could save "
     "time and potentially make better decisions. Of course, the model would need "
     "to be tested more thoroughly before it could be deployed in a real setting, "
     "and there would need to be a process for updating it as new data becomes "
     "available. I acknowledge that my proof-of-concept prototype is just a "
     "starting point, and significant further development would be needed before "
     "it could be used commercially."),
    ("There are several challenges I will need to manage throughout this project. "
     "The most significant is getting access to good quality data, since real-world "
     "datasets are often messy, incomplete, or not representative of the problem "
     "I want to solve. I will do my best to find the most suitable publicly "
     "available dataset, but I acknowledge this may limit the practical relevance "
     "of my results. Another challenge is the time and computational resources "
     "available to me as a student. I will prioritise the most important aspects "
     "of the project and accept that some refinements may not be possible within "
     "the project timeline. I will be transparent about these limitations in my "
     "report and discuss how they could be addressed in future work."),
]


_DOMAIN_KEYWORD_LIST = [(k, v) for k, v in _DOMAIN_KEYWORDS.items()]


def _detect_domain(proposal: dict) -> str:
    """Match domain using whole-word regex to prevent false substring matches."""
    title_lower = proposal["text"].split("\n")[0].lower()
    for domain, keywords in _DOMAIN_KEYWORD_LIST:
        for kw in keywords:
            pattern = r"\b" + _re.escape(kw) + r"\b"
            if _re.search(pattern, title_lower):
                return domain
    return "general"


def _expand(proposal: dict) -> dict:
    """Expand proposal text with domain-appropriate additional paragraphs."""
    group = proposal["performance_group"]
    text  = proposal["text"]

    if group == "High":
        domain = _detect_domain(proposal)
        pool   = _HIGH_EXPAND.get(domain, _HIGH_EXPAND["general"])
        # Insert all desc paragraphs before the Business Model section
        desc_addition = "\n\n".join(pool["desc"])
        biz_addition  = "\n\n".join(pool["biz"])
    else:
        desc_addition = "\n\n".join(_LOW_EXPAND_DESC)
        biz_addition  = "\n\n".join(_LOW_EXPAND_BIZ)

    text = text.replace(
        "\n\nBusiness Model:\n",
        "\n\n" + desc_addition + "\n\nBusiness Model:\n"
    )
    text = text.rstrip() + "\n\n" + biz_addition

    return {**proposal, "text": text}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    from collections import Counter

    def to_band(raw):
        s = (raw / 15) * 100
        if s >= 80: return "HD"
        if s >= 70: return "D"
        if s >= 60: return "C"
        if s >= 50: return "P"
        return "N"

    high = [_expand(p) for p in _high_proposals()]
    low  = [_expand(p) for p in _low_proposals()]
    assert len(high) == 107, f"Expected 107 high proposals, got {len(high)}"
    assert len(low)  == 107, f"Expected 107 low proposals, got {len(low)}"

    payload = {
        "proposals": high + low,
        "exemplars": EXEMPLARS,
    }

    out_path = Path(__file__).parent / "proposals_214.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    all_wc = [len(p["text"].split()) for p in high + low]
    h_wc   = [len(p["text"].split()) for p in high]
    l_wc   = [len(p["text"].split()) for p in low]
    h_bands = Counter(to_band(p["human_score"]) for p in high)
    l_bands = Counter(to_band(p["human_score"]) for p in low)
    print(f"Generated {len(high)} High + {len(low)} Low = {len(high)+len(low)} proposals")
    print(f"High scores: min={min(p['human_score'] for p in high):.2f}  "
          f"max={max(p['human_score'] for p in high):.2f}  "
          f"mean={sum(p['human_score'] for p in high)/len(high):.2f}")
    print(f"High bands: HD={h_bands['HD']} ({h_bands['HD']/107*100:.0f}%)  "
          f"D={h_bands['D']} ({h_bands['D']/107*100:.0f}%)  "
          f"[target: HD≈63%, D≈37%]")
    print(f"Low  scores: min={min(p['human_score'] for p in low):.2f}  "
          f"max={max(p['human_score'] for p in low):.2f}  "
          f"mean={sum(p['human_score'] for p in low)/len(low):.2f}")
    print(f"Low  bands: C={l_bands['C']} ({l_bands['C']/107*100:.0f}%)  "
          f"P={l_bands['P']} ({l_bands['P']/107*100:.0f}%)  "
          f"N={l_bands['N']} ({l_bands['N']/107*100:.0f}%)  "
          f"[target: C≈62%, P≈28%, N≈10%]")
    print(f"Word count:  High mean={sum(h_wc)/len(h_wc):.0f}  "
          f"Low mean={sum(l_wc)/len(l_wc):.0f}  "
          f"Overall mean={sum(all_wc)/len(all_wc):.0f}  (paper target: ~715)")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
