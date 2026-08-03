# About Circuit Heroes and circuitheroesLM

## The genesis

Before there was an embedded language model, there was a deck of cards.

At age seven, **Lakshveer Rao** designed Circuit Heroes and began putting the
electronics-learning card game into the world. The premise was both playful
and serious: children should be able to meet real processors, sensors,
drivers, outputs, displays, and power parts; combine them into devices; and
learn the logic of a circuit without first facing the cost, danger, or
complexity of a physical workbench.

The first game was not a decorative electronics theme placed over ordinary
cards. Its play was built from engineering relationships. A player chooses a
processor, connects inputs and drivers, produces outputs, adds a display or
power source, and reasons about how the complete device works. The physical
cards turned the input → process → output path into something children could
hold, discuss, and play.

Laksh publicly showcased Circuit Heroes at the Kids Business Carnival while
he was seven. The idea later expanded through new decks and games, guided
circuit-building activities, and real projects. The current Circuit Heroes
site reports that the product has reached **300+ families worldwide** and
received a **five-star Amazon rating**. Those figures describe the card-game
ecosystem; they are not model-download or benchmark figures.

## From cards to builds

Circuit Heroes grew into more than one deck. The original *League of
Components* format presents component “heroes”; the newer *Circuit Builder —
Lion Circuits Edition 1* presents 36 engineering cards and introduces P-Unit
and UCIL as ways to reason about power and circuit structure. The website also
hosts short engineering games—including component identification, constraint
challenges, and circuit-building activities—and examples of real builds made
by children.

The editions differ, but the learning principle is consistent:

1. begin with the real name and role of a component;
2. understand where signals and power travel;
3. connect parts into a meaningful hardware system;
4. test the learner through play; and
5. turn understanding into a real build.

This is the educational DNA inherited by circuitheroesLM.

## From builds to a local engineering model

circuitheroesLM asks a new question: **can the game keep inventing useful
engineering lessons when there is no internet?**

The answer explored by this repository is a downloadable, electronics-native
model and runtime built for microcontrollers. Instead of treating a tiny board
as a remote control for a cloud chatbot, the pilot performs trained neural
inference on an ESP32-S3. Reviewed engineering records ground exact facts;
the model selects and structures explanations, clues, quizzes, and game
missions; and a verifier protects names, symbols, behavior, and safety fields.

That creates one continuous project lineage:

```text
physical component cards
        ↓
playable circuit thinking
        ↓
real electronics builds
        ↓
pocket learning hardware
        ↓
fully offline engineering AI
```

The card game is the genesis. circuitheroesLM is the open technical foundation
for the next chapter.

## Why the project is open

An engineering model is useful only when its claims can be inspected. This
repository therefore publishes the model architecture, training and export
code, tokenizer, quantized weights, binary formats, native C runtime, dataset
manifests, evaluations, hardware firmware, and measured ESP32-S3 results.

The current release is a measured pilot, not a claim to contain all of
electronics. Its 52 reviewed records establish a complete, reproducible path
from engineering data to local inference. The longer-term goal is a much
richer, license-reviewed foundation for components, modules, symbols, pins,
connections, circuits, measurements, debugging, simulation concepts,
robotics, and safe hardware design.

## Project principles

- **Real engineering underneath the game.** Activities should reward correct
  circuit relationships, not electronics-flavored guessing.
- **Simple enough for a first learner.** A child should meet the idea before
  the jargon, while names and facts remain technically correct.
- **Local by design.** Core learning must work without Wi-Fi or a cloud API.
- **Grounded where precision matters.** The model may vary its lesson or game,
  but must not invent a pin, rating, symbol, or safety rule.
- **Evidence before spectacle.** Model size, speed, memory, accuracy, and
  limitations are published with reproducible artifacts.
- **Buildable by others.** The stack is intended as a base that makers,
  teachers, researchers, and hardware companies can study and extend.

## Sources and further reading

The project history above combines Laksh's first-hand account with the
following public sources. Product reach and rating figures are explicitly
attributed to the Circuit Heroes website because those figures can change.

- [Circuit Heroes — official website](https://www.circuitheroes.com/)
- [How Circuit Heroes works](https://www.circuitheroes.com/how-it-works)
- [Circuit Heroes games](https://www.circuitheroes.com/play)
- [Real builds by kids](https://www.circuitheroes.com/builds)
- [Current decks and product figures](https://www.circuitheroes.com/buy)
- [EducationWorld profile of Lakshveer Rao](https://educationworld.in/young-achiever-lakshveer-rao/)
- [Hyderabad Kids Fair 2025 brochure](https://hydkidsfair.com/wp-content/uploads/2025/08/HKF-2025-brochure1.pdf)

## About the creator

**Lakshveer Rao** is the young creator of Circuit Heroes and circuitheroesLM.
His work connects three things that are too often separated: learning through
play, building real hardware, and making AI small enough to live alongside the
electronics it explains.

The goal is not merely to place an AI label on a learning product. It is to
build an inspectable engineering intelligence that can live in a child's
pocket, work offline, and help the next learner move from “What is this
component?” to “What can I build with it?”
