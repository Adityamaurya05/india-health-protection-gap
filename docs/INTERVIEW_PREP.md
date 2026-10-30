# Interview Prep: India Health Protection Gap Case

This is your **consulting** project (Bain, BCG, McKinsey, Big 4 strategy). They'll care less about
code and more about **structure, judgement and communication**.

## 60-second pitch

> "I ran a self-directed consulting case: if India's out-of-pocket health spending converged toward
> emerging-market peers, how big would the retail health insurance opportunity be? Using World Bank data, I
> showed that Indians pay **[X]%** of health costs out of pocket, **[Y]** points above the peer median and above
> what India's income predicts. I sized the insurable pool top-down at about **[Z] crore** of premium
> equivalent, then projected three scenarios to 2030. In the central case that's **[A] crore** of new private
> premium, of which a mid-size insurer could target **[B] crore**. I built it as a linked Excel model and a
> 10-slide deck, and the tornado showed the answer hinges on **[top driver]**, so that's the first thing I'd
> validate with IRDAI data. Because I work in health insurance distribution, I also wrote the next-phase
> hypotheses on where to play and how to win."

## Frameworks you used (name them in the interview)
* **Issue tree / MECE:** the README tree splits the question into gap today → insurable → growth → capture.
  The branches don't overlap and together cover the question.
* **Pyramid principle:** the answer comes first (memo and exec summary), then supporting points, then data.
* **Action titles:** every slide title is a full-sentence conclusion, not a topic like "Market size".
* **Top-down vs bottom-up sizing:** top-down from national spend; bottom-up (lives x premium per life) is the cross-check.
* **Sensitivity / tornado:** shows which assumptions actually matter, so the team knows where to spend validation time.

## Likely questions

**Q: Why top-down? Isn't bottom-up more accurate?**
A: "They answer different things. Top-down tells me the theoretical headroom from household spending.
Bottom-up tells me today's actual market. The *gap between them* is the insight. I built the bottom-up
sheet as a template to fill from IRDAI, because I didn't want to type in numbers I couldn't source."

**Q: Your insurable share is 30%. Where does that come from?**
A: "It's an assumption, and the deck labels it as one. Insurance mostly covers hospitalisation, while a lot
of OOP in India goes on outpatient care and medicines. The right source is the National Health Accounts
breakdown of OOP by function. In the tornado it's one of the biggest swing factors, so it's the first
thing I'd validate." *(Don't claim a specific NHA figure unless you've looked it up.)*

**Q: Why cap the OOP shift at the insurable pool?**
A: "Insurance can't absorb spending it doesn't cover, like most pharmacy and OPD spend. Without the cap,
the income-implied scenario would overstate the prize. That's why two scenarios converge in the chart."

**Q: Why would OOP fall at all?**
A: "Rising incomes, government schemes, insurer distribution such as bancassurance, and regulation. The
scenarios don't forecast *which*; they size what happens *if* it does. The 'private capture' assumption
splits the shift between government and private insurers."

**Q: What would you tell the CEO in one sentence?**
A: Read your exec summary title. Practise saying it in under 15 seconds.

**Q: What's the biggest weakness of your analysis?**
A: Pick one honestly. For example: "Growth in health spend is a US$ CAGR held at constant FX, which mixes
real growth with currency moves. I'd rebuild it in INR using National Health Accounts series."

## Mental-math drill (consulting interviews test this)
Practise the chain with round numbers before the interview:
`1.4 bn people x US$ 80 per head = US$ 112 bn total health spend; x 50% OOP = US$ 56 bn; x 30% insurable = US$ 17 bn; ÷ 0.85 = US$ 20 bn of premium.`
*(These are illustrative round numbers for practice only, NOT the model's figures and NOT facts.)*

## Facts to verify before you quote them
Any external "fact" about Indian health insurance (penetration %, IRDAI premium totals, scheme coverage)
should be checked against the **latest IRDAI Annual Report** or official sources. Don't quote from memory,
and don't quote from this file.
