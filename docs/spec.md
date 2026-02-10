## spec.md: Functional Requirements

### 1. Goal

To generate "Ximenean" standard cryptic clues that include a precise definition, a fair subsidiary indication (wordplay), and nothing else.
We aim to create stand alone clues that can be solved individually (not part of a full crossword grid).

### 2. Clue Types to Support

The system must be capable of generating at least the following standard wordplay devices:

* 
**Anagrams:** Rearranging "fodder" using a valid indicator.


* 
**Charades:** Joining individually clued words or letters.


* 
**Containers/Inclusions:** Placing one word inside another.


* 
**Reversals:** Reading a word backward, with directional indicators appropriate for Across or Down placement.


* 
**Hidden Words:** Embedding the answer within the clue text.


* 
**Homophones:** Words that sound like the answer, indicated by terms related to hearing or speech.


* 
**Double Definitions:** Two separate definitions of the same word.


* 
**&lit (All-in-one):** Rare construction where the entire clue serves as both definition and wordplay.



### 3. Quality Control (QC)

* 
**Mechanical Validation:** Scripts must verify that anagram fodder contains the exact letters of the answer or that a hidden word is actually present in the suggested string.


* 
**Adversarial Solving:** A "Solver" LLM must be able to solve the generated clue without knowing the answer beforehand.
