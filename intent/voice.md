# Intent: A spoken interface for the portfolio chatbot

## Purpose
A visitor to my portfolio site (usually a recruiter or a possible collaborator) can ask the
chatbot a question out loud instead of typing it. The server turns the recording into text,
the chatbot answers from my profile exactly as it does for a typed question, and the answer
is spoken back.

## Target audience
The same people as the site: recruiters, hiring managers, and collaborators. Many will try
the microphone once, on a laptop, in a room that is not quiet, with a question they would
otherwise have typed.

## What must not go wrong
1. **My name, my project names, and numbers.** A transcript that turns "Jeevan Gowda
   Kumaraswamy", "Campus Events Navigator", "Kubernetes", "FastAPI", or "CPSC 415" into
   other words changes the question, and the chatbot will then answer a different question
   with full confidence. These are the words a recruiter cares about most and the words a
   transcriber is most likely to get wrong.
2. **Saying something the profile does not say.** The spoken answer is the chatbot's
   answer. The refuse-to-fabricate rule from `intent/portfolio.md` applies to what is said
   aloud exactly as to what is typed: shipped work is stated, "not yet" is said plainly,
   and anything the profile does not cover gets "I don't know", never a guess.
3. **The API key leaving the server.** The browser sends only the recording. Every model
   call happens on the server.
4. **A visitor running up my bill.** Every voice turn is three billed calls. The server
   caps what it accepts, and the page stops recording after 30 seconds.

## What the program does when the transcript may be wrong
- It always **shows the visitor what it heard** ("You said: …") above the answer, so a
  misheard name is visible and the visitor can ask again or type the question instead.
- If the transcript is **empty**, that is a failed transcript, not a crash: the visitor is
  told "I didn't catch that", and no chat or speech call is made.
- It answers the transcript as heard. It does not try to guess what was "really" said: the
  chatbot's grounding rule stops a misheard question from producing a made-up answer.
- During development, the transcript is **checked by code, not by the transcriber**. I write
  down what I said before any model hears the clip; the code then measures the word error
  rate and reports which of the must-survive words (my name, project names, numbers) went
  missing. A second transcription model is the cross-check, and my own ears are the last word.

## Spoken answers
- At most three sentences, with no markdown, lists, or URLs, because it is heard, not read.
- English by default, with a voice I have listened to and chosen. I record what each voice
  does with my name and with "CPSC 415".

## Out of scope for Week 7
- Streaming or real-time conversation; one recording in, one answer out.
- Storing visitors' recordings. Nothing a visitor says is kept after the reply.
- Hosting. The per-turn cost measured here is the evidence for the hosting decision
  (due in `spec.md` before November 30).

## Approved by
Jeevan Gowda Kumaraswamy
Date: November 2, 2026
