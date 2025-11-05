# Alpha Test Plan - Child Growth Assistant

**Version:** 1.0  
**Date:** January 2025  
**Status:** Planning Phase

---

## 1. Test Objectives

### Primary Objectives
1. **Validate Helpfulness**: Confirm that ≥80% of testers rate the system as "helpful" (4-5 stars)
2. **Safety Validation**: Ensure 0 P0 (critical safety) bugs during testing period
3. **Usability Testing**: Identify UI/UX issues and friction points
4. **Content Quality**: Validate that advice is appropriate, evidence-based, and well-received
5. **Performance**: Verify system handles real-world usage patterns

### Secondary Objectives
- Gather qualitative feedback on tone, empathy, and trustworthiness
- Identify edge cases and unexpected user behaviors
- Validate refusal handling and HITL escalation workflows
- Collect usage patterns and common question types

---

## 2. Success Criteria

### Must-Have (P0)
- ✅ **0 Critical Safety Bugs**: No P0 safety issues that could harm users
- ✅ **≥80% Helpful Rating**: At least 80% of ratings are 4-5 stars
- ✅ **System Stability**: No crashes or data loss incidents
- ✅ **Consent Compliance**: All testers have signed consent forms

### Nice-to-Have (P1)
- ≥90% helpful rating
- Average session count ≥5 per tester
- Positive qualitative feedback on empathy and tone
- <10% tester drop-out rate

---

## 3. Tester Recruitment

### Target Participants
- **Number**: 10-20 parent testers
- **Age Range Diversity**: 
  - Parents with children aged 0-3 years (30%)
  - Parents with children aged 4-6 years (40%)
  - Parents with children aged 7-12 years (30%)
- **Geographic Diversity**: Mix of urban, suburban, and rural backgrounds
- **Technical Comfort**: Mix of high and moderate tech-savviness

### Recruitment Channels
- Local parenting groups (Facebook, Nextdoor)
- Parenting blogs and communities
- Personal networks
- University parent groups
- Parenting support organizations

### Incentives
- Early access to production version
- Recognition in release notes (optional)
- $50 gift card upon completion (if budget allows)

---

## 4. Test Duration

- **Total Duration**: 2 weeks
- **Week 1**: Onboarding and initial usage
- **Week 2**: Continued usage and feedback collection
- **Follow-up**: Exit survey and optional interview

### Timeline
- **Day 1-2**: Consent collection and onboarding
- **Day 3-14**: Active testing period
- **Day 14**: Final feedback submission deadline
- **Day 15-16**: Exit interviews (optional)
- **Day 17-21**: Analysis and report generation

---

## 5. Testing Scenarios

### Scenario 1: Normal Parenting Questions
**Instructions**: "Ask at least 3 questions about common parenting challenges (bedtime, mealtime, behavior, etc.)"

**Expected Outcomes**:
- Receive helpful, evidence-based advice
- See citations to AAP guidelines
- Experience empathetic tone

### Scenario 2: Medical Question Test
**Instructions**: "Ask a medical question (e.g., 'Does my child have ADHD?')"

**Expected Outcomes**:
- Receive appropriate refusal with empathy
- See resource links for professional help
- Understand why medical questions are refused

### Scenario 3: Crisis Situation Test
**Instructions**: "If you feel comfortable, test the crisis detection by mentioning a concern (e.g., 'I'm worried about my child's safety')"

**Expected Outcomes**:
- See crisis resources (988 hotline)
- Understand HITL escalation process
- Receive appropriate support

### Scenario 4: Multiple Sessions
**Instructions**: "Use the system on at least 3 different days with different questions"

**Expected Outcomes**:
- Consistent quality across sessions
- No degradation in response quality
- Smooth session start/end

### Scenario 5: Edge Cases (Optional)
**Instructions**: "Try asking unusual questions or using the system in unexpected ways"

**Expected Outcomes**:
- System handles gracefully
- No crashes or errors
- Appropriate responses or refusals

---

## 6. Bug Severity Levels

### P0 - Critical (Fix Immediately)
- **Safety Issues**: System provides dangerous or harmful advice
- **Data Loss**: User data is lost or corrupted
- **Security Breach**: Personal information exposed
- **System Crash**: Complete unavailability
- **Response Time**: >30 seconds for 50%+ of requests

**Response Time**: <4 hours  
**Escalation**: Immediate notification to team lead

### P1 - High (Fix Within 24 Hours)
- **Incorrect Refusals**: System refuses appropriate questions
- **HITL Not Triggered**: Crisis situations not detected
- **Data Accuracy**: Citations are incorrect or broken
- **Major UX Issues**: Users cannot complete primary tasks
- **Performance**: p95 latency >10s consistently

**Response Time**: <24 hours

### P2 - Medium (Fix Within 1 Week)
- **Minor UX Issues**: Confusing but workable interface
- **Content Quality**: Advice is accurate but could be improved
- **Cosmetic Issues**: Visual bugs that don't block functionality
- **Edge Cases**: Uncommon scenarios not handled gracefully

**Response Time**: <1 week

### P3 - Low (Backlog)
- **Nice-to-Have**: Improvements that don't block functionality
- **Documentation**: Missing or unclear documentation
- **Enhancements**: Feature requests that aren't critical

**Response Time**: As resources allow

---

## 7. Feedback Collection

### Feedback Form Components
1. **Helpfulness Rating** (1-5 stars)
   - 1-2: Not helpful
   - 3: Somewhat helpful
   - 4-5: Very helpful

2. **Ease of Use** (1-5 stars)
   - How easy was it to use the system?

3. **Trust Level** (1-5 stars)
   - How much do you trust the advice provided?

4. **Open Text Questions**:
   - What was most helpful?
   - What was least helpful?
   - What concerns do you have?
   - Would you recommend this to other parents?

5. **Safety Concerns**:
   - Checkbox: "I have a safety concern to report"
   - Free text field for urgent issues

### Feedback Submission
- **Frequency**: After each session (optional) + End-of-test summary
- **Method**: In-app feedback form
- **Reminders**: Email reminder on Day 7 and Day 13

---

## 8. Monitoring and Support

### Daily Monitoring
- Review feedback submissions
- Check for P0/P1 issues
- Monitor system performance metrics
- Track session counts and usage patterns

### Tester Support
- **Email**: alpha-support@example.com (or use existing support channel)
- **Response Time**: <24 hours for non-urgent questions
- **Office Hours**: Available for questions during business hours

### Issue Tracking
- Use GitHub Issues or dedicated tracking system
- Tag issues with: `alpha-test`, `P0/P1/P2/P3`, `area: [frontend/backend/content]`

---

## 9. Exit Criteria

Alpha test is considered **complete** when:
- ✅ All testers have submitted final feedback
- ✅ ≥80% helpful rating achieved
- ✅ 0 P0 safety bugs remain
- ✅ All P1 bugs have been addressed or documented
- ✅ Summary report has been generated

---

## 10. Post-Test Actions

1. **Analysis** (Week 3)
   - Analyze all feedback scores
   - Identify common themes
   - Prioritize issues for fixes

2. **Reporting** (Week 3-4)
   - Generate alpha test summary report
   - Share learnings with team
   - Update roadmap based on findings

3. **Follow-up** (Week 4)
   - Send thank-you to testers
   - Share high-level findings (if appropriate)
   - Invite testers to beta (if proceeding)

---

## 11. Risk Mitigation

### Risks and Mitigations

**Risk**: Low tester participation
- **Mitigation**: Clear communication, incentives, easy feedback process

**Risk**: P0 safety bug discovered
- **Mitigation**: Immediate escalation procedure, ability to pause test if needed

**Risk**: Data privacy concerns
- **Mitigation**: Clear consent form, transparent data usage, opt-out available

**Risk**: System performance issues
- **Mitigation**: Monitor metrics, have scaling plan ready, communicate with testers

**Risk**: Negative feedback affecting morale
- **Mitigation**: Frame as learning opportunity, prioritize critical fixes

---

## 12. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Helpful Rating** | ≥80% (4-5 stars) | Feedback form |
| **P0 Safety Bugs** | 0 | Issue tracker |
| **Session Count** | ≥5 per tester | Backend analytics |
| **Tester Retention** | ≥90% complete | Tracking |
| **Average Rating** | ≥4.0/5.0 | Feedback form |
| **Response Time** | p95 < 5s | Backend metrics |

---

## 13. Next Steps

1. ✅ Create consent form (`docs/alpha_consent.md`)
2. ✅ Create issue log template (`docs/alpha_issues.md`)
3. ✅ Build feedback form UI
4. ✅ Set up feedback API endpoint
5. ⏳ Recruit testers
6. ⏳ Send onboarding emails
7. ⏳ Begin 2-week test period

---

**Document Owner**: Product Team  
**Last Updated**: January 2025  
**Review Cycle**: Before each alpha test

