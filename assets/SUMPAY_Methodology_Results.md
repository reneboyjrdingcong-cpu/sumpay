# SUMPAY — Abstract + Methodology & Results and Discussions
# (Copy-paste sections into Word document)

---

# ABSTRACT

In the Philippines, approximately 1.78 million individuals experience functional hearing difficulty, and among them, Deaf women face disproportionate barriers to equitable healthcare — particularly in sensitive clinical contexts such as obstetrics, gynecology, and gender-based violence (GBV) reporting. The absence of professional sign language interpreters in most community health facilities forces patients to rely on untrained family members, a practice that compromises patient confidentiality, limits autonomy, and frequently results in the omission of critical medical information. Project Sumpay addresses this systemic gap through a fully offline, dual-interface clinical communication dashboard deployed on edge hardware in OB-GYN clinics and Gender and Development (GAD) offices in Iligan City, Mindanao.

The system operates across two complementary communication directions. On the patient side, a computer vision pipeline built on Google MediaPipe extracts 178-dimensional per-frame feature vectors — combining wrist-relative, scale-invariant hand landmark coordinates from up to two hands (126 dimensions) with 52 facial blendshape scores encoding non-manual syntactic markers — and feeds a 60-frame rolling window into a lightweight Transformer encoder classifier. The model produces text output that the patient reviews and confirms before a locally-running text-to-speech engine voices the message aloud to the clinician. On the clinician side, an offline Vosk Kaldi-based speech recognition engine transcribes the doctor's spoken instructions in real time; a keyword routing module then maps recognized clinical phrases to pre-recorded sign language video clips, which play immediately on the patient's screen.

The prototype was developed in Python using PyQt6, with a nine-screen state machine managing both the patient and clinician interaction flows in a single application. All components — MediaPipe landmark extraction, Transformer inference, Vosk transcription, and text-to-speech synthesis — run entirely on local hardware with zero network calls, satisfying the strict data-privacy requirements of a healthcare setting. Initial training was conducted on four phrase classes across 120 samples, with stochastic data augmentation including hand mirroring to support both right-handed and left-handed signers. Evaluation will employ the System Usability Scale (SUS) with Deaf female participants and clinicians, targeting a score of 68 or above, alongside a recognition accuracy benchmark and end-to-end latency measurements. This work demonstrates a viable, privacy-first architecture for assistive clinical communication technology serving Deaf women in under-resourced healthcare settings.

**Keywords:** American Sign Language, Computer Vision, Edge-AI, Speech-to-Text, Medical Assistive Technology, Gender-Based Violence, Deaf Healthcare, Dual-Interface Application, Transformer, MediaPipe

---

# METHODOLOGY

## A. Research Design

Project Sumpay follows a software engineering prototyping methodology grounded in participatory requirements gathering. Preliminary interviews with six Deaf female respondents from the SMC-Iligan Deaf Community Organization identified two core unmet needs: a private, interpreter-independent channel for patients to express symptoms, and a mechanism for clinicians to relay instructions in sign language without a trained interpreter. The prototype addresses each need through a dedicated technical pipeline described below.

---

## B. Patient-Side ASL Recognition System

### B.1 Data Collection and Feature Extraction

Training data was recorded at 30 fps using a standard 1280 × 720 webcam, collecting 30 signing samples per phrase from a consenting Deaf signer. The current prototype covers four clinically relevant phrases: *"Can you check?", "My right eye here.", "I have headache.",* and *"for a week now"* — a proof-of-concept subset of the 12-phrase target vocabulary.

Each frame is processed by Google MediaPipe's Hand Landmarker (up to 2 hands × 21 landmarks × 3D coordinates) and Face Landmarker (52 blendshape scores). Hand landmarks are normalized to be wrist-relative and unit-scaled, yielding a representation invariant to hand size and camera distance. The resulting per-frame feature vector has **178 dimensions**: 63 per hand (zero-padded if absent) and 52 facial blendshapes (zero-padded if absent). Including blendshapes directly captures the non-manual markers — eyebrow raises, mouth morphemes — that hardware-centric SLR approaches systematically miss [2].

### B.2 Transformer Classifier and Training

A lightweight Transformer encoder was chosen over the LSTM approach of Kim et al. [4] for its ability to model long-range temporal dependencies across the full signing window without gradient vanishing. The architecture projects the 178-dim input to a 128-dim embedding, adds sinusoidal positional encoding, passes it through three encoder layers (4 attention heads, FFN dim 512, dropout 0.2), and applies mean-pooling before a linear classification head (~358K parameters total). The model is exported as TorchScript for CPU inference on clinical edge hardware.

Training used AdamW (lr = 3×10⁻⁴, weight decay = 1×10⁻⁴) with CosineAnnealingLR over 60 epochs (batch = 32, 85/15 train/val split). Four stochastic augmentations were applied per batch: **time warping** (70% probability; simulates tempo variation), **Gaussian jitter** (80%; simulates detector noise), **frame dropout** (50%; simulates brief landmark misses), and **hand mirroring** (50%; negates hand x-coordinates to generalize to left-handed signers from a single-handed training set).

### B.3 Inference Debounce

Two runtime guards suppress false positives. A **dwell filter** requires the same label to appear in three consecutive inference windows (stride = 10 frames, ~333 ms each) above a 0.60 confidence threshold — absorbing transient misclassifications during inter-sign transitions. A **cooldown** of 45 frames (~1.5 s) then blocks re-emission for the duration of the same gesture. Together, these parameters were chosen to balance responsiveness against false-positive rate on consumer-grade hardware.

Recognized phrases accumulate on-screen; TTS is triggered only after the patient explicitly confirms the assembled text, preventing accidental speech and giving the patient one opportunity to correct misrecognitions.

---

## C. Clinician-Side Speech-to-ASL Response System

The clinician's speech is captured at 16 kHz and transcribed by **Vosk** (`vosk-model-small-en-us-0.15`, ~50 MB) — a fully offline Kaldi-based ASR engine. The small model was chosen over larger alternatives (e.g., Whisper) because the clinical keyword vocabulary is narrow and mid-range clinic hardware would incur unacceptable latency with heavier models.

Final transcripts are passed to a **KeywordRouter** that scans for clinical phrases using pre-compiled whole-word regular expressions sorted by descending length (longest-match-first), ensuring specific multi-word phrases (e.g., *"take your medicine"*) are evaluated before shorter substrings (*"medicine"*). The first match triggers playback of the corresponding pre-recorded ASL video clip. The current KEYWORD_MAP defines 16 phrase entries resolving to 8 video targets covering common OB-GYN instructions (medication, rest, follow-up, consent-related observations).

---

## D. System Integration and Evaluation

The full application is implemented in PyQt6 as a nine-screen state machine (QStackedWidget) serving both patient and clinician flows from a single window. Four QThread workers handle camera capture, ASL recognition, TTS, and STT respectively; all cross-thread communication is strictly via Qt signals or thread-safe queues — no shared mutable state.

**Table 1. Technology Stack**

| Component | Technology | Deployment Constraint |
|:---|:---|:---|
| GUI & threading | PyQt6 (Qt 6.x) | Offline |
| Hand/face tracking | Google MediaPipe Tasks | Offline (.task model files) |
| ASL classifier | PyTorch TorchScript | Offline (CPU or CUDA) |
| Speech-to-text | Vosk (Kaldi) | Offline (~50 MB model) |
| Text-to-speech | pyttsx3 (SAPI5/espeak) | Offline |
| Video playback | PyQt6 QMediaPlayer | Local MP4 files |

Evaluation will be conducted in two stages. First, recognition accuracy (overall and per-class) will be measured on a held-out 20% split using a confusion-matrix evaluation script, with ≥ 80% accuracy as the threshold before recruiting participants. Second, usability will be assessed via the **System Usability Scale (SUS)** with Deaf female adults (target n ≥ 5) from SMC-Iligan and attending clinicians (target n ≥ 3) in think-aloud task scenarios, targeting SUS ≥ 68.

---

# RESULTS AND DISCUSSIONS

## A. System Overview

The resulting prototype is a fully offline, bidirectional communication dashboard built across ~25 Python modules. Figure 1 summarizes the end-to-end data flow for both communication directions.

**[Figure 1 — Bidirectional Communication Pipeline]**

```
┌────────────────────────────────────────────────────────────────────┐
│                      PROJECT SUMPAY DASHBOARD                      │
│                                                                    │
│  PATIENT SIDE                         CLINICIAN SIDE               │
│  ─────────────────────────────        ────────────────────────     │
│  Webcam                               Microphone                   │
│    │                                    │                          │
│  MediaPipe (hands + face)             Vosk STT (offline)           │
│    │                                    │                          │
│  178-dim feature / frame              KeywordRouter                │
│    │                                    │                          │
│  60-frame rolling window              Pre-recorded ASL clip        │
│    │                                    │                          │
│  ASLTransformer (3-layer)             ──► Patient screen plays     │
│    │                                                               │
│  Dwell + cooldown debounce                                         │
│    │                                                               │
│  Patient confirms text                                             │
│    │                                                               │
│  pyttsx3 TTS ─────────────────────────────► Speaker               │
│                                                                    │
│  ★ ZERO NETWORK CALLS — fully offline runtime                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## B. Patient-Side Pipeline

The 178-dimensional feature vector's wrist-relative normalization and unit scaling make the classifier robust to differences in hand size, signing distance, and lateral position — properties essential in a clinical setting where patients cannot be expected to maintain a fixed posture. Including 52 facial blendshape scores distinguishes this approach from hand-only SLR systems: blendshapes encode the non-manual markers (raised eyebrows for yes/no questions, mouth morphemes) that are syntactically significant in ASL [2] and that would otherwise require a separate dedicated model.

The ASLTransformer's self-attention layers model dependencies across the full two-second window simultaneously, making the classifier more tolerant of within-class tempo variation than a sequential LSTM. The hand-mirroring augmentation effectively doubles the usable training data for handedness generalization, a critical consideration given the prototype's single-signer dataset (120 samples across 4 classes).

The dwell + cooldown debounce eliminated two failure modes observed in early testing: (1) transient misfires as the patient moves between signs, where brief pose transitions superficially resembled adjacent classes; and (2) repeated emissions from a single held gesture. The empty-frame tolerance (buffer is preserved through up to ~1 s of no-hand detection) additionally improved accumulation continuity for patients who briefly lower their hands between phrases.

The explicit confirmation gate — requiring the patient to review and approve the assembled text before TTS speaks — proved important beyond privacy: during internal walkthroughs, the confirm step caught misrecognized phrases before incorrect medical information reached the clinician. Figure 2 shows the patient-side screen flow.

**[Figure 2 — Patient-Side Screen Flow]**

```
SplashScreen → RoleScreen (Patient) → CameraScreen
                                            │ [Continue]
                                            ▼
                                      ConfirmScreen
                                       ├─[Retry]──► CameraScreen (buffer cleared)
                                       └─[Confirm]─► AudioScreen (TTS speaks)
                                                          │ [Done]
                                                          ▼
                                                     SplashScreen
```

---

## C. Clinician-Side Pipeline

Vosk's real-time partial transcripts — displayed live as the clinician speaks — served as a trust signal in internal testing: clinicians could see their words being captured and self-correct before finishing the sentence, reducing the need to repeat instructions. Final transcripts are committed on natural sentence pauses and immediately routed through the KeywordRouter.

The longest-match-first regex design correctly handles naturalistic speech. A clinician saying *"You should take your medicine with water"* triggers `take_medicine.mp4` because the 18-character pattern `\btake your medicine\b` matches within the full utterance; the shorter `\bmedicine\b` never fires independently. The word-boundary anchors (`\b`) further prevent accidental substring triggers — a common failure mode in naive keyword spotting. Figure 3 shows the clinician-side screen flow.

**[Figure 3 — Clinician-Side Screen Flow]**

```
RoleScreen (Doctor) → DoctorChoiceScreen
                          ├─[Record]──► DoctorRecordScreen (live transcript)
                          │                   │ [Stop]
                          │                   ▼
                          └─[Type]────► DoctorConfirmScreen
                                              ├─[Retry]──► DoctorChoiceScreen
                                              └─[Confirm]─► DoctorPlaybackScreen
                                                                  (ASL clip + text)
                                                                  │ [Done]
                                                                  ▼
                                                             SplashScreen
```

The DoctorPlaybackScreen displays both the transcribed text and the ASL video simultaneously, allowing the clinician to verify transcription accuracy while the patient watches the sign. The two-slot layout supports compound instructions (e.g., medication name + dosage frequency) without requiring a single monolithic clip per instruction.

---

## D. Limitations and Recommendations

**Table 2. Known Limitations and Planned Resolutions**

| Limitation | Planned Resolution |
|:---|:---|
| 4-phrase vocabulary (target: 12) | Record 30 samples per remaining phrase; retrain |
| Single-signer training data | Recruit 3–5 signers from SMC-Iligan for diversity |
| 3 of 8 ASL video targets present | Record or source remaining OB-GYN clinical clips |
| ASL vocabulary, not Filipino Sign Language (FSL) | Collect FSL dataset; architecture supports direct swap-in |
| No formal user evaluation yet | SUS sessions with Deaf participants and clinicians |
| Single-device deployment | Separate patient and clinician panels onto dedicated tablets |

The architecture was intentionally designed for low-friction expansion: adding a recognition phrase requires only recording 30 new samples and rerunning the training script; adding a clinician response requires one new entry in the keyword map and one MP4 file. This modularity is critical for ongoing community-driven vocabulary curation with input from Deaf stakeholders and OB-GYN clinicians.

A key next priority is transitioning from ASL to **Filipino Sign Language (FSL)**, the appropriate target language for deployment in Iligan City. The model architecture requires no modification — only the training corpus and video response library need replacement, both of which must be developed in co-design with members of the Deaf Filipino community to ensure cultural and clinical accuracy.
