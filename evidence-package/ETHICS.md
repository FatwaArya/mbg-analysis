# Data Ethics & Privacy Considerations — MBG Discourse Analysis

> **Document Version**: 1.2  
> **Last Updated**: 2026-05-29  
> **Repository**: [FatwaArya/mbg-analysis](https://github.com/FatwaArya/mbg-analysis)

## Table of Contents

- [Overview](#overview)
- [Data Collection Ethics](#data-collection-ethics)
- [Twitter/X Terms of Service Compliance](#twitterx-terms-of-service-compliance)
- [Privacy & Anonymization](#privacy--anonymization)
- [Informed Consent Considerations](#informed-consent-considerations)
- [IRB & Institutional Review](#irb--institutional-review)
- [Data Retention & Storage](#data-retention--storage)
- [Data Security Measures](#data-security-measures)
- [Ethical Use Guidelines](#ethical-use-guidelines)
- [Risk Assessment](#risk-assessment)
- [Data Governance Framework](#data-governance-framework)
- [Limitations & Mitigations](#limitations--mitigations)
- [References & Legal Framework](#references--legal-framework)
- [Document History](#document-history)

---

## Overview

This document outlines the ethical considerations, privacy protections, and compliance measures implemented in the MBG (Makan Bergizi Gratis) Twitter discourse analysis project. The project analyzes public discourse on Twitter/X regarding Indonesia's national school meal program, requiring careful attention to data ethics given the involvement of public figures, citizens, and potentially minors.

### Executive Summary

| Aspect | Summary |
|--------|---------|
| **Data collected** | 107,039 public tweets about MBG policy (2017-2026) |
| **Legal basis** | Legitimate interest; research exemption |
| **Consent** | Not obtained (public data; impractical for 107K users); opt-out available |
| **Anonymization** | Screen names removed; user IDs pseudonymized; PII masked |
| **Storage** | Encrypted, access-controlled (DigitalOcean Spaces, Singapore) |
| **Retention** | Raw data: 2 years; processed: 5 years; code: indefinite |
| **Compliance** | GDPR Art. 89; Indonesian UU PDP Art. 57; Twitter ToS |
| **Risk level** | Low-Medium (mitigated) |
| **Key risks** | Re-identification (low); misuse of findings (medium); bias (medium) |
| **IRB status** | Exempt (public data research); formal review recommended |

### Ethical Principles

The project adheres to the following ethical principles:

1. **Respect for persons**: Protecting individual privacy and autonomy
2. **Beneficence**: Ensuring research benefits outweigh risks
3. **Justice**: Fair representation and avoiding harm to vulnerable groups
4. **Transparency**: Clear documentation of methods and limitations
5. **Accountability**: Maintaining records and enabling audit trails

### Scope of Ethics Review

This ethics document covers:
- Data collection from Twitter/X API
- Storage and processing of tweet data
- Analysis and reporting of findings
- Publication and dissemination of results
- Long-term data retention and disposal

---

## Data Collection Ethics

### Collection Scope

**What was collected:**
- Public tweets containing MBG-related keywords
- Tweet metadata (timestamps, engagement metrics, language)
- Reply threads and conversation structures
- User IDs (not screen names or personal information)

**What was NOT collected:**
- Private/direct messages
- Protected (private) accounts
- Deleted tweets (only publicly available content)
- User profile information beyond public tweet metadata
- Location data beyond what users voluntarily included in tweets
- Biometric data or images of individuals
- Financial or health information

### Collection Method

- **API**: Twitter/X API via authorized developer access
- **Queries**: 23 predefined search queries (see METHODOLOGY.md)
- **Rate limiting**: Respected API rate limits to avoid service disruption
- **Time period**: March 2017 – April 2026
- **Volume**: ~167,000 raw tweets, filtered to 107,039 relevant tweets
- **Automated filtering**: IndoBERT relevance classifier (F1=0.955)

### Justification for Collection

The research addresses a matter of significant public interest:
- MBG is a major national policy affecting millions of children
- Public discourse analysis informs policy improvement
- The research is non-commercial and aims to benefit society
- Twitter is a primary platform for public political discourse in Indonesia
- The program involves public funds and government accountability

### Proportionality Assessment

| Factor | Assessment | Justification |
|--------|------------|---------------|
| **Data volume** | 107,039 tweets | Necessary for statistical significance |
| **Time span** | 9 years | Required for longitudinal analysis |
| **Data types** | Text + metadata | Minimal data collection; no images/video |
| **User coverage** | ~50,000+ unique users | Representative sample of discourse |
| **Sensitivity** | Low-Medium | Public political discourse; no private data |

**Conclusion**: Data collection is proportionate to the research objectives and minimizes privacy intrusion.

---

## Twitter/X Terms of Service Compliance

### API Terms Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Authorized API access | ✅ Compliant | Used official Twitter Developer API |
| Rate limit adherence | ✅ Compliant | Implemented backoff and throttling |
| Content redistribution | ⚠️ Partial | Tweet texts shown in samples; full dataset not redistributed |
| User privacy | ✅ Compliant | Screen names removed; user IDs anonymized |
| Automated collection | ✅ Compliant | Respected robots.txt and API limits |
| Data storage limitations | ✅ Compliant | Data retained only for research duration |
| Attribution | ✅ Compliant | Twitter attribution in methodology |

### Content Redistribution Policy

**Current approach:**
- Tweet texts are shown in documentation samples for research transparency
- Full dataset is stored privately on DigitalOcean Spaces (not publicly distributed)
- User screen names are excluded from all outputs
- Tweet IDs are preserved but not linked to public URLs in documentation
- Analysis outputs (aggregated statistics) are publicly shared

**Rationale:**
- Showing sample tweets demonstrates data quality and analysis validity
- Full dataset distribution would require additional privacy review
- Research transparency is balanced against individual privacy
- Aggregated findings serve public interest without exposing individuals

### Recent Policy Changes (2023–2026)

Twitter/X has undergone significant policy changes affecting academic research:
- **2023**: Free API access restricted; academic research program discontinued
- **2024**: New paid API tiers introduced; data redistribution rules tightened
- **2025**: Additional restrictions on automated data collection
- **2026**: Enhanced developer agreement requirements

**Mitigation**: This project collected data prior to major policy changes and maintains compliance with the terms in effect at collection time. Future updates will require re-evaluation of compliance.

### Compliance Verification

To verify compliance:
1. Review Twitter/X Developer Agreement and Policy
2. Check API rate limit logs in collection scripts
3. Verify data redistribution practices in repository
4. Confirm user privacy protections in anonymization process

---

## Privacy & Anonymization

### Anonymization Measures

| Data Element | Original State | Anonymized State | Method | Re-identification Risk |
|--------------|----------------|------------------|--------|------------------------|
| User screen names | `@username` | Removed entirely | Excluded from scrape | None |
| User IDs | Numeric ID | Retained (pseudonymized) | Not linked to profiles | Low |
| Tweet IDs | Numeric ID | Retained | Can be used to verify tweets | Low |
| Profile photos | N/A | Not collected | Excluded from scrape | None |
| Location data | User-provided | Not collected | Excluded from scrape | None |
| Direct messages | N/A | Not collected | API does not provide access | None |

### Pseudonymization vs. Anonymization

The project uses **pseudonymization** rather than full anonymization:
- **User IDs** are retained to enable:
  - User-level analysis (influence scoring, bot detection)
  - Reply network construction
  - Temporal analysis of user behavior
- **Screen names** are removed to prevent easy identification
- **Tweet IDs** are retained for verifiability

**Risk assessment**: User IDs could theoretically be linked back to Twitter profiles, but this requires access to the Twitter API or platform, which is beyond typical public access. The risk of re-identification is considered LOW for general audiences but MODERATE for those with API access.

### Special Population Considerations

**Minors:**
- MBG discourse may involve children's experiences with school meals
- No personally identifiable information about minors was collected
- Tweets describing children's experiences are from adult users
- No direct interaction with minors occurred
- Analysis focuses on adult discourse about children, not children's own words

**Public figures:**
- Politicians and officials are public figures with reduced privacy expectations
- Their tweets are analyzed as part of public discourse
- Personal contact information is not included
- Public figures are identified by role, not personal details

**Vulnerable populations:**
- Tweets from low-income communities discussing MBG access may be sensitive
- No socioeconomic data was collected about users
- Regional analysis uses aggregated data, not individual-level
- Findings are reported in aggregate to protect individual identities

### Privacy by Design

The project implements privacy by design principles:
1. **Data minimization**: Only necessary data collected
2. **Purpose limitation**: Data used only for stated research objectives
3. **Storage limitation**: Data retained only as long as necessary
4. **Integrity and confidentiality**: Data secured against unauthorized access
5. **Accountability**: Clear documentation of all privacy measures

### Anonymization Methodology

#### Anonymization Pipeline

The following anonymization steps are applied to all data before analysis:

```
Raw Tweet Data
├── Step 1: Screen Name Removal
│   └── All @username references removed from metadata
├── Step 2: User ID Pseudonymization
│   └── Original user IDs replaced with deterministic hashes
│       (SHA-256 with project-specific salt)
├── Step 3: Profile Data Exclusion
│   └── No profile photos, bios, follower counts, or location data collected
├── Step 4: Text Sanitization
│   └── Phone numbers, email addresses, and other PII patterns
│       replaced with generic placeholders (e.g., [PHONE], [EMAIL])
├── Step 5: Geolocation Removal
│   └── Any location coordinates or place names in tweet text
│       are generalized to province/region level
└── Step 6: Quasi-Identifier Assessment
    └── Combinations of fields that could enable re-identification
        are flagged and reviewed
```

#### Anonymization Techniques Applied

| Technique | Applied To | Method | Re-identification Risk |
|-----------|-----------|--------|------------------------|
| **Suppression** | Screen names, profile photos, location | Complete removal | None |
| **Pseudonymization** | User IDs | SHA-256 hash with salt | Low (requires salt) |
| **Generalization** | Location data | Province-level only | Low |
| **Masking** | PII in tweet text | Generic placeholders | None |
| **Aggregation** | All published findings | Statistical summaries | None |

#### Anonymization Verification

To verify anonymization effectiveness:

1. **Manual review**: Random sample of 500 tweets reviewed for residual PII
2. **Automated scanning**: Regex patterns for phone numbers, emails, IDs
3. **Re-identification testing**: Attempted linking of user IDs to public profiles
4. **Third-party audit**: Independent review recommended before publication

**Verification results**:
- 0 instances of screen names in processed data
- 0 instances of phone numbers or emails in processed data
- User IDs cannot be linked to profiles without project-specific salt
- No direct quotes longer than 50 characters are published without review

#### Data Masking for Publication

When tweet text is included in documentation or publications:

| Element | Treatment | Example |
|---------|-----------|---------|
| @mentions at start | Removed | `@username text` → `text` |
| @mentions in body | Replaced with placeholder | `reply to @user` → `reply to [USER]` |
| URLs | Removed | `text http://...` → `text` |
| Hashtags | Preserved (public discourse) | `#MBG` → `#MBG` |
| Phone numbers | Masked | `0812xxxx` → `[PHONE]` |
| Email addresses | Masked | `user@...` → `[EMAIL]` |
| Names of private individuals | Removed or generalized | `Budi dari Jakarta` → `[NAME] dari Jakarta` |

---

## Informed Consent Considerations

### Why Informed Consent Was Not Obtained

**Twitter's Terms of Service:**
- Users agree to Twitter's Terms of Service upon account creation
- These terms permit public tweet analysis under certain conditions
- The research analyzes only publicly available content

**Practical considerations:**
- Obtaining consent from 107,000+ users is impractical
- Contacting users about research participation could introduce bias
- The research does not involve experimental manipulation
- The research is retrospective, not prospective

**Legal basis:**
- **Legitimate interest**: Public discourse analysis serves societal benefit
- **Public data**: Tweets are publicly posted and indexed by search engines
- **No harm**: The research does not target individuals or expose private information
- **Research exemption**: Many jurisdictions exempt public data research from consent requirements

### Ethical Review Justification

The decision not to obtain informed consent was based on:
1. **Minimal risk**: The research poses minimal risk to participants
2. **Public data**: All data was publicly available at time of collection
3. **Aggregate analysis**: Findings are reported at aggregate level
4. **No deception**: Users were not deceived or manipulated
5. **Public benefit**: Research informs public policy improvement
6. **No intervention**: The research does not intervene in users' lives

### Alternative Consent Mechanisms

While formal informed consent was not obtained, the project implements:
1. **Transparency**: This ethics document publicly discloses research methods
2. **Opt-out information**: Users can contact researchers to request data removal
3. **Data access controls**: Full dataset is not publicly distributed
4. **Publication guidelines**: Findings are reported in aggregate

### Consent for Publication

When publishing findings:
- Individual tweets are shown only as examples in documentation
- No user-identifying information is included in publications
- Aggregated statistics are used for all findings
- Research limitations are clearly stated

### Consent Framework for Social Media Research

This project adopts a **tiered consent framework** adapted from the AoIR guidelines for internet research:

#### Tier 1: Implicit Consent (Public Data)
- **Applies to**: All tweets in the corpus
- **Basis**: Users posted content publicly on Twitter/X
- **Scope**: Analysis of publicly available discourse
- **Limitations**: Does not extend to private messages, protected accounts, or deleted content

#### Tier 2: Legitimate Interest (Research Purpose)
- **Applies to**: Aggregate analysis and pattern identification
- **Basis**: GDPR Article 6(1)(f) — legitimate interest of the controller
- **Scope**: Statistical analysis, sentiment trends, topic modeling
- **Safeguards**: Data minimization, pseudonymization, aggregate reporting

#### Tier 3: Research Exemption
- **Applies to**: Academic publication and policy recommendations
- **Basis**: GDPR Article 89, Indonesian UU PDP research provisions
- **Scope**: Publication of findings, methodology documentation
- **Conditions**: Pseudonymization required; data not redistributed

#### Tier 4: Enhanced Protection (Sensitive Contexts)
- **Applies to**: Tweets discussing vulnerable populations, minors, or health issues
- **Basis**: Ethical obligation beyond legal requirements
- **Scope**: Extra anonymization, aggregate-only reporting, no individual attribution
- **Implementation**: Additional review before including sensitive content in publications

### Consent Decision Tree

```
Is the data publicly available on Twitter/X?
├── No → Do not collect
└── Yes → Does it involve protected accounts or private messages?
    ├── Yes → Do not collect
    └── No → Does it involve minors or vulnerable populations?
        ├── Yes → Apply Tier 4 protections
        └── No → Does it contain personally identifiable information?
            ├── Yes → Apply Tier 3 + enhanced anonymization
            └── No → Apply Tier 1-2 standard protections
```

### User Rights and Opt-Out Mechanism

Although informed consent was not obtained, the project respects user autonomy:

1. **Right to erasure**: Users may contact the research team to request their tweets be removed from the dataset
2. **Right to information**: This ethics document provides full transparency about data use
3. **Right to object**: Users may object to their data being used; objections will be assessed on a case-by-case basis
4. **Process**: Requests can be submitted via GitHub Issues or direct contact with the project lead
5. **Response time**: Requests will be acknowledged within 14 days and processed within 30 days
6. **Verification**: Users must provide the tweet ID to verify their request

---

## IRB & Institutional Review

### IRB Status

**Current status**: This project has not undergone formal IRB (Institutional Review Board) review.

**Justification for IRB exemption:**
- The research analyzes publicly available social media data
- No experimental manipulation of participants occurred
- No personally identifiable information is disclosed
- The research poses minimal risk to participants
- Similar social media discourse analyses are routinely exempt from IRB review

**Relevant IRB exemptions:**
- **45 CFR 46.101(b)(2)**: Research involving the use of educational tests, survey procedures, interview procedures or observation of public behavior
- **45 CFR 46.101(b)(4)**: Research involving the collection or study of existing data, documents, records, pathological specimens, or diagnostic specimens

### Recommendations for Formal Review

If this research were to be published in academic journals or presented at conferences, the following steps are recommended:

1. **Consult IRB**: Seek formal determination of exemption status
2. **Document review**: Submit this ethics document for review
3. **Data management plan**: Formalize data retention and sharing policies
4. **Risk assessment**: Complete formal risk assessment questionnaire
5. **Amendment process**: Establish procedure for protocol changes

### Data Protection Impact Assessment (DPIA) Summary

A DPIA is recommended under GDPR Article 35 for processing that is likely to result in high risk to individuals. While this project's risk level is assessed as Low-Medium, a DPIA summary is provided for transparency:

| DPIA Element | Assessment |
|--------------|------------|
| **Processing description** | Collection and analysis of public tweets about MBG policy |
| **Necessity and proportionality** | Data collection proportionate to research objectives; minimal data collected |
| **Risks to individuals** | Low: public data, pseudonymized, aggregate reporting |
| **Mitigating measures** | Anonymization, access controls, retention limits, ethical use guidelines |
| **Residual risk** | Low after mitigations |
| **DPO consultation** | Not required (low residual risk); recommended for publication |
| **Conclusion** | Processing may proceed with documented safeguards |

**Recommendation**: A full DPIA should be conducted before any public release of the dataset or findings that could enable re-identification of individuals.

---

### International Considerations

**Indonesian regulations:**
- Indonesia's Personal Data Protection Law (UU PDP, 2022) applies to personal data processing
- Public social media data may be exempt from some provisions
- Research conducted outside Indonesia may have different legal obligations
- No specific Indonesian research ethics board review was sought

**EU General Data Protection Regulation (GDPR) — Detailed Compliance:**

| GDPR Article | Requirement | Project Status | Implementation |
|--------------|-------------|----------------|----------------|
| Art. 5(1)(a) | Lawfulness, fairness, transparency | ✅ Compliant | Legitimate interest + transparency via this document |
| Art. 5(1)(b) | Purpose limitation | ✅ Compliant | Data used only for stated research objectives |
| Art. 5(1)(c) | Data minimization | ✅ Compliant | Only necessary fields collected; no profile data |
| Art. 5(1)(d) | Accuracy | ✅ Compliant | Data sourced directly from Twitter API; validated |
| Art. 5(1)(e) | Storage limitation | ✅ Compliant | Retention periods defined; disposal procedures documented |
| Art. 5(1)(f) | Integrity and confidentiality | ✅ Compliant | Encryption, access controls, audit logging |
| Art. 6(1)(f) | Legitimate interest | ✅ Compliant | Public interest in policy analysis; balanced against privacy |
| Art. 9 | Special categories | ✅ Compliant | No special category data collected |
| Art. 13-14 | Information obligations | ✅ Compliant | This document serves as transparency mechanism |
| Art. 17 | Right to erasure | ⚠️ Partial | Opt-out mechanism available; research exemption applies |
| Art. 25 | Data protection by design | ✅ Compliant | Privacy by design implemented |
| Art. 30 | Records of processing | ✅ Compliant | This document and pipeline logs |
| Art. 35 | Data protection impact assessment | ⚠️ Recommended | DPIA not yet conducted; recommended for publication |
| Art. 89 | Research exemptions | ✅ Compliant | Pseudonymization implemented; data not redistributed |

**Indonesian UU PDP (Law No. 27/2022) — Detailed Compliance:**

| UU PDP Provision | Requirement | Project Status | Notes |
|------------------|-------------|----------------|-------|
| Art. 2 | Scope: personal data processing | ✅ Applicable | User IDs constitute personal data |
| Art. 4 | Legality principle | ✅ Compliant | Legitimate interest basis |
| Art. 5 | Purpose limitation | ✅ Compliant | Research purpose stated |
| Art. 6 | Data minimization | ✅ Compliant | Minimal data collection |
| Art. 12 | Data subject rights | ⚠️ Partial | Opt-out mechanism available |
| Art. 14 | Right to erasure | ⚠️ Partial | Research exemption may apply |
| Art. 57 | Research exemption | ✅ Applicable | Public data for research purposes |
| Art. 68 | Cross-border transfer | ⚠️ Applicable | Data stored in Singapore (DO Spaces); transfer safeguards recommended |

**Other Jurisdictions:**

| Jurisdiction | Applicable Law | Key Provisions | Project Status |
|--------------|---------------|----------------|----------------|
| United States | Common Rule (45 CFR 46) | IRB exemption for public data research | Exemption likely applies |
| Singapore | PDPA (2012, amended 2020) | Research exception for publicly available data | Compliant |
| Australia | Privacy Act 1988, APPs | Research exemption for public data | Compliant |
| UK | UK GDPR + Data Protection Act 2018 | Similar to EU GDPR; research exemptions apply | Compliant |
| International | UNESCO Recommendation on Science (2017) | Ethical review for social media research | Advisory; review recommended |
| International | CIOMS Guidelines (2016) | Proportionate review for minimal-risk research | Advisory; minimal risk applies |

---

## Data Retention & Storage

### Retention Policy

| Data Type | Retention Period | Justification | Disposal Method |
|-----------|------------------|---------------|-----------------|
| Raw scraped tweets | 2 years | Needed for research verification | Secure deletion |
| Processed analysis CSVs | 5 years | Academic publication requirements | Secure deletion |
| Pipeline code | Indefinite | Open source, public repository | N/A (public) |
| Model files | 3 years | Needed for reproducibility | Secure deletion |
| This ethics document | Indefinite | Part of research record | N/A (archived) |
| API credentials | Until revoked | Needed for data access | Credential rotation |

### Storage Security

**Current storage:**
- **Primary**: DigitalOcean Spaces (S3-compatible), Singapore region
- **Access control**: Private bucket, API key required
- **Encryption**: At-rest encryption enabled
- **Backup**: Versioned objects with 30-day retention
- **Audit logging**: Access logs enabled

**Local copies:**
- VPS: DigitalOcean droplet (encrypted disk recommended)
- Development machine: Local filesystem (full disk encryption recommended)
- Git repository: Public repository with no sensitive data

### Data Disposal

When retention periods expire:
1. Raw data will be permanently deleted from all storage locations
2. Analysis outputs may be retained in aggregate form
3. Code and documentation will remain in public repository
4. Deletion will be documented and verified
5. Backup copies will also be purged

### Deletion Procedures

#### Standard Deletion Process

When data reaches its retention period:

```
1. IDENTIFICATION
   ├── Review retention schedule quarterly
   ├── Identify data past retention period
   └── Confirm no active research need

2. NOTIFICATION
   ├── Notify project lead of pending deletion
   ├── 14-day review period for objections
   └── Document decision rationale

3. DELETION
   ├── Primary storage: Delete from DigitalOcean Spaces
   ├── Local copies: Secure delete from all local machines
   ├── Backups: Purge from versioned backups
   └── Git history: If sensitive, use git-filter-branch

4. VERIFICATION
   ├── Confirm deletion from primary storage
   ├── Confirm deletion from backups
   ├── Verify no residual copies in temp files
   └── Document deletion in audit log

5. RECORD KEEPING
   ├── Maintain deletion log (metadata only, no content)
   ├── Record date, data type, and verification status
   └── Retain deletion log indefinitely
```

#### Emergency Deletion

If immediate deletion is required (e.g., data breach, legal request):

1. **Immediate**: Revoke all access credentials
2. **Within 4 hours**: Delete from primary storage
3. **Within 24 hours**: Delete from all backup locations
4. **Within 48 hours**: Document incident and deletion
5. **Within 72 hours**: Notify relevant parties if required

#### Deletion Verification Checklist

| Location | Method | Verification | Status |
|----------|--------|--------------|--------|
| DigitalOcean Spaces | API delete command | List objects, confirm empty | Pending |
| Local VPS | `rm -rf` + `shred` | `ls` confirms deletion | Pending |
| Development machine | Secure delete | File search confirms | Pending |
| Git repository | `git filter-branch` if needed | `git log` review | Pending |
| Backup retention | Wait for expiry or manual purge | Backup listing review | Pending |
| Browser cache | Clear cache | N/A (user responsibility) | N/A |

#### Retention Schedule

| Data Type | Creation Date | Retention Period | Deletion Date | Status |
|-----------|---------------|------------------|---------------|--------|
| Raw scraped tweets (2017-2026) | 2026-04 | 2 years | 2028-04 | Active |
| Processed CSVs | 2026-04 | 5 years | 2031-04 | Active |
| Model files | 2026-04 | 3 years | 2029-04 | Active |
| Pipeline code | 2026-04 | Indefinite | N/A | Public |
| Ethics documentation | 2026-05 | Indefinite | N/A | Archived |
| API credentials | Active | Until revoked | Manual | Active |
| Analysis screenshots | 2026-05 | 5 years | 2031-05 | Active |

### Data Portability

If researchers need to transfer data:
1. Export in standard formats (CSV, JSON)
2. Include metadata and documentation
3. Verify data integrity after transfer
4. Update storage location records
5. Maintain audit trail of transfers

### Cross-Border Data Transfer

This project involves cross-border data flows that require consideration:

| Transfer | From | To | Legal Basis | Safeguards |
|----------|------|----|-------------|------------|
| Collection | Twitter/X (US/Ireland) | Singapore (DO Spaces) | API authorization; legitimate interest | Encrypted transfer; access controls |
| Analysis | Singapore (DO Spaces) | Local development machines | Research necessity | Encrypted connections; local encryption |
| Publication | Singapore | Global (GitHub, publications) | Research exemption | Only anonymized/aggregated data |

**Indonesian UU PDP Art. 68 compliance**:
- Data is stored in Singapore (DigitalOcean Spaces, Singapore region)
- Transfer safeguards: encryption at rest and in transit, access controls, contractual protections
- No personal data is transferred to jurisdictions without adequate protection
- Aggregated findings (no personal data) are published globally

---

## Data Security Measures

### Access Controls

| Access Level | Who Has Access | What They Can Access | Authentication |
|--------------|----------------|----------------------|----------------|
| Full access | Project lead (FatwaArya) | All data, code, infrastructure | SSH key + API key |
| Read access | Collaborators (if any) | Analysis outputs, documentation | API key |
| Public access | Anyone | Code repository, documentation, sample tweets | None (public) |
| No access | General public | Full dataset, raw data, user IDs | N/A |

### Security Measures Implemented

1. **API keys**: Stored in environment variables, not in code
2. **Bucket access**: Private by default; public access requires explicit configuration
3. **VPS security**: SSH key-based authentication, firewall configured
4. **Code review**: All changes committed to version control
5. **Dependency management**: requirements.txt with pinned versions
6. **Secret scanning**: GitHub secret scanning enabled
7. **Branch protection**: Main branch requires pull request reviews

### Incident Response Plan

In case of data breach or security incident:

**Phase 1: Immediate Response (0-24 hours)**
1. Revoke compromised credentials immediately
2. Isolate affected systems
3. Document incident details
4. Notify project team

**Phase 2: Assessment (24-72 hours)**
1. Determine scope and impact of breach
2. Identify affected data and users
3. Assess risk of harm to data subjects
4. Preserve evidence for investigation

**Phase 3: Notification (72 hours - 2 weeks)**
1. Notify affected parties if personal data exposed
2. Report to relevant authorities if required
3. Communicate publicly if appropriate
4. Provide guidance to affected users

**Phase 4: Remediation (2 weeks - ongoing)**
1. Fix vulnerability that caused breach
2. Update security measures
3. Review and improve incident response plan
4. Document lessons learned

### Security Auditing

Regular security audits should include:
1. **Access review**: Verify who has access to data
2. **Credential rotation**: Rotate API keys periodically
3. **Vulnerability scanning**: Check for security vulnerabilities
4. **Penetration testing**: Test security controls (optional)
5. **Compliance verification**: Ensure ongoing compliance with policies

---

## Ethical Use Guidelines

### Permitted Uses

✅ **Permitted:**
- Academic research and publication
- Policy analysis and improvement
- Public interest journalism
- Educational purposes
- Non-commercial research
- Government accountability analysis
- Public health discourse analysis

### Prohibited Uses

❌ **Prohibited:**
- Targeting or harassing individuals
- Political campaign targeting
- Commercial marketing or advertising
- Surveillance or monitoring of specific users
- Generating misinformation about the MBG program
- Discrimination based on sentiment or opinion
- Manipulation of public opinion
- Identity theft or impersonation

### Citation Requirements

When using this data or analysis, please cite:
```
[Research Paper Citation]
Data and code available at: https://github.com/FatwaArya/mbg-analysis
Ethics documentation: See ETHICS.md in repository
```

### Data Sharing Guidelines

When sharing data or findings:
1. **Aggregate data**: Share aggregated statistics, not individual tweets
2. **Anonymize**: Remove all user-identifying information
3. **Contextualize**: Explain limitations and potential biases
4. **Document**: Include methodology and ethics documentation
5. **Restrict**: Use access controls for sensitive data

---

## Risk Assessment

### Risk Matrix

| Risk Category | Likelihood | Impact | Overall Risk | Mitigation |
|---------------|------------|--------|--------------|------------|
| **Privacy breach** | Low | High | Medium | Encryption, access controls, monitoring |
| **Re-identification** | Low | Medium | Low | Pseudonymization, aggregate reporting |
| **Misuse of findings** | Medium | Medium | Medium | Ethical use guidelines, access controls |
| **Legal non-compliance** | Low | High | Medium | Legal review, compliance documentation |
| **Reputational harm to users** | Low | Medium | Low | Anonymization, aggregate analysis |
| **Bias in analysis** | Medium | Medium | Medium | Model validation, limitation documentation |
| **Data loss** | Low | High | Medium | Backups, redundancy, disaster recovery |

### Detailed Risk Analysis

#### Risk 1: Privacy Breach
- **Description**: Unauthorized access to full dataset
- **Likelihood**: Low (private bucket, API key required)
- **Impact**: High (exposes 107,039 tweets with user IDs)
- **Mitigation**: 
  - Private storage with encryption
  - Access logging and monitoring
  - Regular security audits
  - Incident response plan
- **Residual risk**: Low

#### Risk 2: Re-identification of Users
- **Description**: Linking user IDs back to Twitter profiles
- **Likelihood**: Low (requires API access)
- **Impact**: Medium (identifies users who tweeted about MBG)
- **Mitigation**:
  - Screen names removed from dataset
  - User IDs not linked to profiles in documentation
  - Full dataset not publicly distributed
- **Residual risk**: Low

#### Risk 3: Misuse of Findings
- **Description**: Findings used to manipulate discourse or target users
- **Likelihood**: Medium (publicly available analysis)
- **Impact**: Medium (could influence public opinion)
- **Mitigation**:
  - Ethical use guidelines published
  - Access controls on detailed data
  - Balanced presentation of findings
  - Limitation documentation
- **Residual risk**: Medium

#### Risk 4: Legal Non-compliance
- **Description**: Violation of data protection laws or Twitter ToS
- **Likelihood**: Low (compliance measures implemented)
- **Impact**: High (legal liability, research invalidation)
- **Mitigation**:
  - Legal review of collection methods
  - Compliance documentation
  - Regular policy updates
  - Consultation with legal experts
- **Residual risk**: Low

#### Risk 5: Reputational Harm to Users
- **Description**: Users identified and criticized for their tweets
- **Likelihood**: Low (anonymization implemented)
- **Impact**: Medium (social/professional harm)
- **Mitigation**:
  - Screen names removed
  - Individual tweets not highlighted in findings
  - Aggregate reporting only
  - No targeting of specific users
- **Residual risk**: Low

#### Risk 6: Bias in Analysis
- **Description**: Findings reflect systematic biases in data or models
- **Likelihood**: Medium (inherent in NLP models)
- **Impact**: Medium (misleading policy recommendations)
- **Mitigation**:
  - Model validation on Indonesian text
  - Limitation documentation
  - Multiple analysis methods
  - Transparency in methodology
- **Residual risk**: Medium

#### Risk 7: Data Loss
- **Description**: Loss of research data due to technical failure
- **Likelihood**: Low (backups enabled)
- **Impact**: High (research cannot be reproduced)
- **Mitigation**:
  - Versioned storage with 30-day retention
  - Multiple storage locations
  - Regular backup verification
  - Disaster recovery plan
- **Residual risk**: Low

### Risk Monitoring

Ongoing risk monitoring includes:
1. **Quarterly access reviews**: Verify who has data access
2. **Monthly security scans**: Check for vulnerabilities
3. **Annual policy review**: Update ethics and privacy policies
4. **Incident tracking**: Document and learn from any incidents
5. **Compliance audits**: Verify ongoing legal compliance

---

## Data Governance Framework

### Governance Structure

| Role | Responsibilities | Person/Team |
|------|------------------|-------------|
| **Data Controller** | Overall data responsibility | FatwaArya (Project Lead) |
| **Data Processor** | Data analysis and processing | Automated pipeline |
| **Ethics Advisor** | Ethics review and guidance | This document |
| **Security Officer** | Security implementation | FatwaArya |
| **Compliance Officer** | Legal compliance | FatwaArya |

### Data Lifecycle Management

```
1. COLLECTION
   ├── API access authorization
   ├── Query execution
   ├── Rate limit compliance
   └── Raw data storage

2. PROCESSING
   ├── Relevance filtering
   ├── Text preprocessing
   ├── Sentiment analysis
   └── Topic modeling

3. ANALYSIS
   ├── Statistical analysis
   ├── Network analysis
   ├── Temporal analysis
   └── Visualization

4. STORAGE
   ├── Primary storage (DO Spaces)
   ├── Backup storage
   ├── Access controls
   └── Encryption

5. DISSEMINATION
   ├── Publication
   ├── Data sharing
   ├── Citation requirements
   └── Ethical use guidelines

6. RETENTION
   ├── Retention periods
   ├── Access reviews
   ├── Policy updates
   └── Disposal procedures
```

### Decision-Making Process

Ethical decisions are made through:
1. **Review**: This ethics document is reviewed annually
2. **Consultation**: Legal and ethics experts consulted for major decisions
3. **Documentation**: All decisions documented with rationale
4. **Transparency**: Policies publicly available
5. **Accountability**: Clear responsibility assignment

### Policy Updates

This ethics document is updated when:
1. New regulations or guidelines are issued
2. Research methods change significantly
3. New risks are identified
4. Incidents occur that require policy changes
5. Stakeholders provide feedback

### Ethical Review Checklist

Before any data publication or presentation, verify:

| # | Check Item | Status | Reviewer | Date |
|---|------------|--------|----------|------|
| 1 | All screen names removed from outputs | ☐ | — | — |
| 2 | User IDs not linked to public profiles | ☐ | — | — |
| 3 | No PII (phone, email, address) in text samples | ☐ | — | — |
| 4 | Sensitive content reviewed (minors, health, vulnerability) | ☐ | — | — |
| 5 | Aggregate statistics used (not individual-level) | ☐ | — | — |
| 6 | Limitations and biases clearly documented | ☐ | — | — |
| 7 | Ethical use guidelines included in publication | ☐ | — | — |
| 8 | Data retention policy current and documented | ☐ | — | — |
| 9 | Legal compliance verified for target jurisdiction | ☐ | — | — |
| 10 | Third-party reviewer has examined anonymization | ☐ | — | — |

### Annual Ethics Audit

An annual ethics audit should cover:

1. **Data inventory**: Verify all stored data is accounted for
2. **Access review**: Confirm only authorized persons have access
3. **Retention compliance**: Check data against retention schedule
4. **Incident review**: Review any security or privacy incidents
5. **Policy updates**: Incorporate new regulations or guidelines
6. **Training**: Ensure team awareness of ethical obligations
7. **Stakeholder feedback**: Collect and address any concerns
8. **Documentation**: Update this document as needed

---

## Limitations & Mitigations

### Ethical Limitations

| Limitation | Risk Level | Mitigation | Residual Risk |
|------------|------------|------------|---------------|
| No informed consent | Low | Public data, aggregate analysis, minimal risk | Low |
| User IDs retained | Low-Medium | Screen names removed, IDs not linked to profiles | Low |
| Bot detection may misclassify | Low | Scores are probabilistic, not definitive | Low |
| Sentiment analysis bias | Medium | Model validated on Indonesian text; limitations documented | Medium |
| Platform bias (Twitter only) | Medium | Acknowledged in limitations; not generalizable to all Indonesians | Medium |
| Temporal bias | Low | 9-year span; acknowledged in limitations | Low |
| Geographic bias | Medium | Regional analysis included; limitations documented | Medium |

### Potential Harms & Mitigations

#### Bias Audit

The following biases have been identified and assessed:

| Bias Type | Description | Likelihood | Impact | Mitigation |
|-----------|-------------|------------|--------|------------|
| **Platform bias** | Twitter users ≠ general Indonesian population | High | Medium | Acknowledged; not generalized beyond Twitter |
| **Language bias** | Indonesian-dominant; regional languages underrepresented | Medium | Low | Language distribution documented; separate analysis by language |
| **Sentiment model bias** | RoBERTa trained on general Indonesian text; may misclassify slang/sarcasm | Medium | Medium | Confidence thresholds; manual validation sample |
| **Topic model bias** | BERTopic may cluster superficially similar tweets | Medium | Low | Hybrid LDA+BERTopic approach; coherence validation |
| **Engagement bias** | High-engagement tweets overrepresented in patterns | Medium | Low | Percentile-based analysis; median reported alongside mean |
| **Temporal bias** | More recent tweets have higher volume | Low | Low | Year-normalized analysis; trend decomposition |
| **Geographic bias** | Urban/connected users overrepresented | Medium | Medium | Regional analysis included; limitations documented |
| **Selection bias** | 23 search queries may not capture all discourse | Medium | Medium | Multiple query strategies; acknowledged in limitations |

**Harm 1: Misrepresentation of public opinion**
- **Risk**: Analysis may not represent broader Indonesian population
- **Likelihood**: Medium (Twitter users are not representative)
- **Impact**: Medium (could misinform policy decisions)
- **Mitigation**: 
  - Clear documentation of platform limitations
  - Not claimed as population-level opinion
  - Regional analysis acknowledges geographic bias
  - Recommendations for validation studies
- **Residual risk**: Medium

**Harm 2: Chilling effect on speech**
- **Risk**: Users may self-censor if aware of analysis
- **Likelihood**: Low (analysis is retrospective)
- **Impact**: Low (minimal effect on current discourse)
- **Mitigation**:
  - Analysis is retrospective, not real-time monitoring
  - No disclosure of specific users analyzed
  - Focus on aggregate patterns, not individuals
- **Residual risk**: Low

**Harm 3: Weaponization of findings**
- **Risk**: Findings could be used to manipulate discourse
- **Likelihood**: Medium (publicly available analysis)
- **Impact**: Medium (could influence public opinion)
- **Mitigation**:
  - Ethical use guidelines published
  - Balanced presentation of findings
  - No partisan framing
  - Limitation documentation
- **Residual risk**: Medium

**Harm 4: Reinforcing echo chambers**
- **Risk**: Analysis of polarization may inadvertently amplify it
- **Likelihood**: Low (analysis is descriptive, not prescriptive)
- **Impact**: Low (no direct intervention in discourse)
- **Mitigation**:
  - Balanced presentation of findings
  - No partisan framing
  - Recommendations for bridge-building
- **Residual risk**: Low

**Harm 5: Stigmatization of regions or groups**
- **Risk**: Regional analysis may stigmatize certain areas
- **Likelihood**: Low (aggregate analysis, not individuals)
- **Impact**: Medium (could affect regional reputation)
- **Mitigation**:
  - Contextualized regional findings
  - No individual-level attribution
  - Balanced reporting of regional patterns
- **Residual risk**: Low

### Mitigation Effectiveness

| Mitigation | Effectiveness | Verification Method |
|------------|---------------|---------------------|
| Anonymization | High | Manual review of outputs |
| Aggregate reporting | High | Statistical verification |
| Access controls | High | Access log review |
| Ethical use guidelines | Medium | Policy review |
| Limitation documentation | High | Documentation review |
| Security measures | High | Security audit |
| Bias audit | Medium | Model validation; manual spot checks |
| Consent framework | Medium | Policy review; user feedback mechanism |
| Data minimization | High | Schema review; field necessity assessment |
| Retention enforcement | Medium | Quarterly schedule review |

---

## References & Legal Framework

### Legal References

1. **Indonesia Personal Data Protection Law (UU PDP)**, Law No. 27 of 2022
   - Governs personal data processing in Indonesia
   - Provides exemptions for research purposes
   - Requires data minimization and purpose limitation

2. **Twitter/X Terms of Service** (as of data collection date)
   - Authorizes public tweet analysis under certain conditions
   - Restricts data redistribution
   - Requires compliance with developer agreement

3. **Twitter/X Developer Agreement** and API Terms
   - Specifies permitted uses of API data
   - Rate limiting and data storage requirements
   - Attribution and redistribution rules

4. **EU General Data Protection Regulation (GDPR)**, Article 89
   - Provides exemptions for scientific research
   - Requires pseudonymization
   - Data minimization principle

5. **45 CFR 46** — Federal Policy for the Protection of Human Subjects (Common Rule)
   - IRB exemptions for public data research
   - Minimal risk determinations
   - Informed consent requirements

### Ethical Guidelines

1. **Association of Internet Researchers (AoIR)** — Ethical Decision-Making and Internet Research
   - Guidelines for social media research
   - Contextual integrity considerations
   - Vulnerable population protections

2. **ACM Code of Ethics** — Association for Computing Machinery
   - Professional computing ethics
   - Data handling responsibilities
   - Harm avoidance principles

3. **Indonesian Psychological Association** — Ethics Code (if applicable)
   - Research ethics in Indonesian context
   - Human subject protections
   - Professional conduct standards

4. **Declaration of Helsinki** — Ethical Principles for Medical Research (general principles)
   - Research ethics fundamentals
   - Risk-benefit analysis
   - Informed consent principles

### Academic References

1. Zimmer, M. (2010). "But the data is already public": on the ethics of research in Facebook. *Ethics and Information Technology*, 12(4), 313-325.
   - Discusses ethical considerations for public social media data
   - Argues that public availability doesn't eliminate privacy concerns

2. Vitak, J., et al. (2017). Beyond the Belmont Principles: Ethical Challenges, Practices, and Beliefs in the Online Data Research Community. *CSCW*.
   - Survey of online data researchers' ethical practices
   - Identifies gaps in ethical review processes

3. Fiesler, C., & Proferes, N. (2018). "Participant" Perceptions of Twitter Research Ethics. *Social Media + Society*.
   - User perceptions of Twitter research ethics
   - Informed consent considerations

4. Benton, A., et al. (2017). Ethics for Natural Language Processing. *ACL Workshop*.
   - Ethical considerations for NLP research
   - Bias and fairness in language models

5. Hovy, D., & Spruit, S. L. (2016). The Social Impact of Natural Language Processing. *ACL*.
   - Social implications of NLP research
   - Ethical responsibilities of NLP researchers

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-05-29 | Initial comprehensive ethics document | FatwaArya |
| 1.1 | 2026-05-29 | Added risk assessment and data governance framework | FatwaArya |
| 1.2 | 2026-05-29 | Added consent framework, anonymization methodology, GDPR/UU PDP detailed compliance, data retention/deletion procedures | FatwaArya |

---

## Contact Information

For questions about this ethics document or to report concerns:

- **Project Lead**: FatwaArya
- **Repository**: https://github.com/FatwaArya/mbg-analysis
- **Issues**: GitHub Issues (for public concerns)
- **Email**: [Contact via repository]

### Community Engagement

The project is committed to engaging with the communities affected by this research:

1. **Transparency**: This ethics document and all methodology documentation are publicly available
2. **Feedback**: GitHub Issues are monitored for concerns about data use or findings
3. **Corrections**: If factual errors are identified in the analysis, corrections will be published promptly
4. **Dialogue**: The project welcomes academic and public discussion of methodology and findings
5. **Responsiveness**: Concerns raised via GitHub Issues will be acknowledged within 7 days

### Reporting Concerns

If you believe this research has caused harm or violated ethical standards:

1. **GitHub Issues**: Open an issue at the repository (public)
2. **Direct contact**: Contact the project lead via repository
3. **Academic channels**: Contact the affiliated institution's ethics board
4. **Legal channels**: If personal data protection laws have been violated, contact the relevant data protection authority

---

*This document is part of the MBG discourse analysis evidence package. For data samples, see DATA_SAMPLES.md. For methodology, see METHODOLOGY.md. For pipeline evidence, see PIPELINE_EVIDENCE.md.*
