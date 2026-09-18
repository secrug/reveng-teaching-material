# Session 1 — Opening lecture script: "Two futures, one foundation"

This is the expanded 15-minute opening for Session 1 (it replaces the shorter
"Slide 1" block in [s01-binaries.md](s01-binaries.md#000--opening-this-session-only-10-min-warm-up-replaced) — use whichever fits your style; this
one carries the fuller argument). It is a **script with stage directions**, not
slides. Deliver it standing away from the screen. The whole point is that the most
important thing you say all semester, you say with the projector off.

The argument has one job: to inoculate students against the moment — coming in
about forty minutes — when an LLM solves the cold open faster than they can, and
they silently conclude the course is pointless. You beat that conclusion by making
a stronger argument than "AI is unreliable." You concede that AI is *good*, and
show why the fundamentals matter **anyway, in every future.**

---

## The script

### 1. Concede the strong version (2 min)

> "I'll start with the thing your instinct is going to keep whispering all
> semester, and I'll say it before you do: my honest guess is that AI is going to
> get better and faster than any human in this room at raw reverse engineering.
> Probably not in some distant sci-fi sense — soon, and at the boring mechanical
> parts first. I'm not going to stand here and pretend the machine is dumb. It
> isn't. If I have to win your attention by lying to you about the tools, I've
> already lost."

*(Say this plainly. Credibility for the next twelve minutes depends on you not
overselling. Students can smell a teacher defending obsolete turf, and the whole
lecture dies if they think that's what this is.)*

### 2. The gap between the headline and your hands (4 min)

> "So here's the puzzle. You read the headlines — AI agents autonomously finding
> vulnerabilities, escaping sandboxes, running offensive security on their own.
> And then you actually get your hands on one of these tools" — *[name your
> firsthand example here; e.g. the offensive-security agent you evaluated]* — "and
> it's… fine. It's useful. But left to drive on its own it flails, and the moment
> a real pentester sits next to it and steers, it gets dramatically better.
>
> Why the gap? I can think of two honest explanations, and notice that I'm not
> accusing anyone of fraud. One: the public demos are not the whole story — they
> are curated, and they run on compute budgets nobody spends on a normal task. A
> result that took a million tokens and fifty resets and a human quietly picking
> the target is a real result, but it is not the result the headline implies.
> Two: there was more human guidance in the loop than the write-up admits. In
> practice it's usually both. The unguided, everyday version of these tools is
> weaker than the story — for now."

*(Fair-and-factual note for you, the lecturer: state the curation/compute point as
an inference from the gap you personally observed, not as a proven accusation. If
a student pushes — "how do you know they're not just better than you say?" — the
honest answer is: "I don't, for certain. That's why my argument in a minute
doesn't depend on being right about it." That honesty is worth more than winning
the point.)*

### 3. The empirical wedge: novelty breaks it (3 min)

> "There's a second piece of evidence, and this one you'll get to test yourselves
> at the end of the year. Defenders have started deliberately building binaries
> that *mislead* AI — code shaped to trigger the machine's assumptions and send it
> confidently the wrong way. And more simply: AIs still fail a lot of CTF
> challenges. Not the ones that look like ten thousand tutorials it has seen —
> those it crushes. The *novel* ones. The ones with a custom instruction set it
> has never seen, a homemade algorithm that isn't in any textbook, a trick that
> exists nowhere on the internet.
>
> That's the tell. The machine is strongest where the problem resembles its
> training and weakest where the problem is genuinely new. And real security work
> — the work worth paying for — is disproportionately the genuinely new part.
> We're going to spend the last part of this course *building* challenges like
> that. You'll write binaries that break AIs. You can't do that without
> understanding exactly how the AI is reasoning and where it stops."

### 4. The crux — you don't have to win the bet (4 min)

> "Now the important part. Everything I just said about timelines could be wrong.
> Maybe the machine surpasses even a machine-plus-expert next year. I want to show
> you why it *doesn't matter* for the decision you're making by sitting in this
> room. There are two futures, and I'll take either one.
>
> **Future one:** it stays true that AI plus a human's intuition and creativity
> beats AI alone. The machine does the grinding; the human aims it, catches its
> mistakes, and supplies the leaps it can't make. In that future, you want to be
> the human in that pair — and you can only be that human if you understand the
> machine well enough to aim it and to know when it's lying. That's fundamentals.
>
> **Future two:** the machine gets so good it beats the human-plus-machine team at
> the reverse engineering itself. Fine. Then the value doesn't disappear — it
> moves *upstream*. The job stops being 'reverse this binary by hand' and becomes
> 'design, build, deploy, and validate the automated security systems that do it
> at scale' — for companies, on real infrastructure, where you are responsible for
> whether the thing actually works. You cannot architect a system whose primitives
> you don't understand. You cannot validate an automated reverse-engineering
> pipeline if you can't read what it produces. That's fundamentals plus the common
> techniques — and *more* of them, not fewer.
>
> Look at where those two roads go. They go through the same door. I genuinely
> cannot tell you which future we get. I can tell you that in every one of them,
> the person who understands the machine wins, and the person who only knows how
> to type prompts into a box loses. That's not a safe bet because I'm optimistic.
> It's a safe bet because *both* outcomes require the same foundation. This
> semester is that foundation. It's the one investment that pays off no matter who
> is right about the timeline."

### 5. How you'll actually work with the hard stuff (2 min)

> "One more thing, so you don't mishear me. I am not telling you to memorize
> everything or to work without AI. That would be stupid, and you'd ignore me
> anyway. Here's the actual working model, and it's what professionals do:
>
> The fundamentals and the common techniques — how the machine works, the stack,
> control flow, data structures, the standard bag of tricks — those you *own*. Not
> look-up-able. Internalized, because you use them every single time and there's
> no time to look them up.
>
> The exotic stuff — some bizarre anti-debugging trick, a custom virtual machine,
> a weird cryptographic scheme you've never met — you do *not* memorize. You
> recognize the shape of it, you look it up, you have the AI explain it to you in
> thirty seconds. And then — this is the whole point — because you own the
> fundamentals, you can actually *use* that explanation on the spot. Your
> fundamentals are what let you cash the check the AI just wrote. Someone without
> them gets a beautiful explanation they can't apply to anything.
>
> That's the course. Own the foundation. Rent the exotica. Use the machine for
> everything, and be the one person in the room who can tell when it's wrong."

*(Then transition straight into the decompiler deal and housekeeping from the
standard S1 opening, and on into the cold open.)*

---

## Why this works (notes for the lecturer)

- **It concedes first.** The argument is bulletproof precisely because it grants
  the strongest version of the student's objection ("AI will beat us at this") and
  *still* lands on "so learn the fundamentals." A student cannot use "but AI is
  really good" against you, because you said it first and louder.
- **It is robust to being wrong.** The two-futures structure means you never have
  to defend a timeline prediction. Whether AI plateaus or explodes, the conclusion
  holds. That is the single most important rhetorical property of the whole
  course, and it's worth stating explicitly to the students — teach them the
  *shape* of the argument, not just its conclusion.
- **It sets up the year's payoff.** "You'll build binaries that break AIs" plants
  the flag for the end-of-course CTF work. When they get there, they'll understand
  it as the proof of everything claimed in week one.
- **It stays honest about the tools.** The failure mode of this lecture is
  becoming an anti-AI sermon. Don't. The correct exit state is: *AI is powerful, I
  intend to use it constantly, and I am going to become the person who can wield
  it.* Land it as an invitation to power, not a warning against a threat.

---

## The one-line version (for the slide, and for their notes)

> AI moved the bottleneck. Whether the future is *AI + you* or *you building the
> systems*, both run on the same fundamentals — so the fundamentals are the one
> bet that pays off in every future.
