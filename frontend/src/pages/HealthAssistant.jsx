import { useState } from "react";
import { ExternalLink, MessageSquare, Send } from "lucide-react";
import "./HealthAssistant.css";

const LAB_RESULTS_URL = "https://medlineplus.gov/lab-tests/how-to-understand-your-lab-results/";
const CBC_URL = "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/";
const GLUCOSE_URL = "https://medlineplus.gov/lab-tests/blood-glucose-test/";
const CHOLESTEROL_URL = "https://medlineplus.gov/lab-tests/cholesterol-levels/";

const TOPICS = [
  {
    id: "reports",
    title: "Understanding a lab report",
    question: "How should I read a lab report?",
    answer: "A lab report lists tests performed on a sample and their results. Compare a result with the reference range printed on that report: ranges can differ between laboratories and groups. A result inside a range does not guarantee health, and a result outside it does not by itself diagnose a condition. A healthcare professional can interpret results with your history and other findings.",
    source: "MedlinePlus: How to Understand Your Lab Results",
    sourceUrl: LAB_RESULTS_URL,
    terms: ["report", "result", "reference range", "lab test", "laboratory", "normal range"],
  },
  {
    id: "hemoglobin",
    title: "Hemoglobin",
    question: "What does hemoglobin measure?",
    answer: "Hemoglobin is an iron-rich protein in red blood cells that carries oxygen from the lungs to the rest of the body. It is one of the measurements commonly included in a complete blood count (CBC).",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: CBC_URL,
    terms: ["hemoglobin", "haemoglobin", " hgb", " hb "],
  },
  {
    id: "rbc",
    title: "RBC",
    question: "What does an RBC count measure?",
    answer: "RBC means red blood cell. A CBC measures the number of red blood cells in a blood sample; these cells carry oxygen from the lungs to the rest of the body.",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: CBC_URL,
    terms: ["rbc", "red blood cell", "red cells"],
  },
  {
    id: "wbc",
    title: "WBC",
    question: "What does a WBC count measure?",
    answer: "WBC means white blood cell. A CBC measures the total number of white blood cells in a blood sample. White blood cells are part of the immune system and help fight infections and other diseases.",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: CBC_URL,
    terms: ["wbc", "white blood cell", "white cells"],
  },
  {
    id: "platelets",
    title: "Platelets",
    question: "What do platelets do?",
    answer: "Platelets are blood cell fragments that help blood clot and stop bleeding. A CBC can include a platelet count.",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: CBC_URL,
    terms: ["platelet", "thrombocyte"],
  },
  {
    id: "glucose",
    title: "Glucose",
    question: "What does a blood glucose test measure?",
    answer: "A blood glucose test measures glucose, a type of sugar in the blood and the body's main source of energy. The meaning of a result depends on the type of test and the person's circumstances; this assistant does not interpret individual values.",
    source: "MedlinePlus: Blood Glucose Test",
    sourceUrl: GLUCOSE_URL,
    terms: ["glucose", "blood sugar", "sugar level"],
  },
  {
    id: "cholesterol",
    title: "Cholesterol",
    question: "What is total cholesterol?",
    answer: "A cholesterol test can report total cholesterol, which includes HDL and LDL cholesterol. The test may also report these components separately. This general explanation does not interpret an individual's result.",
    source: "MedlinePlus: Cholesterol Levels",
    sourceUrl: CHOLESTEROL_URL,
    terms: ["cholesterol", "lipid profile", "lipid panel", "hdl", "ldl"],
  },
];

function findTopic(question) {
  const normalized = ` ${question.toLowerCase().replace(/[^a-z0-9]+/g, " ")} `;
  const asksForClinicalAdvice = /\b(diagnos(?:e|is)?|treat(?:ment)?|medication|medicine|prescrib\w*|cure|symptom|disease|cancer|diabetes|anemia|anaemia|dosage|dose|lower|raise|improve|manage|reduce)\b|\bshould\s+i\b/i.test(question);
  const asksForPersonalInterpretation = /\b(my|these|this)\s+(result|value|level|report|test)s?\b/i.test(question)
    || /\b(is|are)\s+(my\s+)?(hemoglobin|haemoglobin|rbc|wbc|platelets?|glucose|blood sugar|cholesterol)\s+(normal|high|low|abnormal)\b/i.test(question)
    || /\b(high|low|abnormal)\s+(blood\s+)?(glucose|sugar|hemoglobin|haemoglobin|rbc|wbc|platelets?|cholesterol)\b/i.test(question);

  if (asksForClinicalAdvice || asksForPersonalInterpretation) return null;

  const matchesTopic = (topic) => topic.terms.some((term) => normalized.includes(term));
  return TOPICS.find((topic) => topic.id !== "reports" && matchesTopic(topic))
    ?? TOPICS.find((topic) => topic.id === "reports" && matchesTopic(topic));
}

function HealthAssistant() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);

  function askQuestion(event) {
    event.preventDefault();
    const submitted = question.trim();
    if (!submitted) return;
    setResponse({ question: submitted, topic: findTopic(submitted) ?? null });
  }

  function selectTopic(topic) {
    setQuestion(topic.question);
    setResponse({ question: topic.question, topic });
  }

  return (
    <div className="assistant-page">
      <div className="assistant-shell">
        <header className="assistant-header">
          <div className="assistant-title-icon"><MessageSquare size={23} /></div>
          <span className="assistant-eyebrow">MEDAI HEALTH EDUCATION</span>
          <h1>Health Education Assistant</h1>
          <p>Explore clear, general information about lab reports and common markers.</p>
        </header>

        <section className="assistant-notice" aria-label="Assistant scope">
          <strong>Curated educational assistant</strong>
          <p>
            Answers are selected from locally stored educational content. This is not
            generative AI, a diagnostic system, or a substitute for professional advice.
            Your questions stay in this browser and are not sent to a service.
          </p>
        </section>

        <section className="assistant-topics" aria-labelledby="topics-heading">
          <div className="assistant-section-heading">
            <span className="assistant-eyebrow">CHOOSE A TOPIC</span>
            <h2 id="topics-heading">Suggested questions</h2>
          </div>
          <div className="assistant-topic-grid">
            {TOPICS.map((topic) => (
              <button
                className={`assistant-topic-button ${response?.topic?.id === topic.id ? "selected" : ""}`}
                key={topic.id}
                onClick={() => selectTopic(topic)}
                type="button"
              >
                <span>{topic.title}</span>
                <strong>{topic.question}</strong>
              </button>
            ))}
          </div>
        </section>

        <form className="assistant-question-form" onSubmit={askQuestion}>
          <label htmlFor="assistant-question">Ask about a supported topic</label>
          <div className="assistant-input-row">
            <input
              id="assistant-question"
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="For example: What does WBC measure?"
              value={question}
            />
            <button type="submit" aria-label="Ask question">
              <Send size={17} />
              Ask
            </button>
          </div>
          <small>Questions are checked only against this page's local educational topics.</small>
        </form>

        {response && (
          <section className="assistant-answer" aria-live="polite" aria-labelledby="answer-heading">
            <span className="assistant-eyebrow">EDUCATIONAL RESPONSE</span>
            <h2 id="answer-heading">{response.topic ? response.topic.title : "Topic not supported yet"}</h2>
            <p className="assistant-answer-question">{response.question}</p>
            {response.topic ? (
              <>
                <p>{response.topic.answer}</p>
                <a href={response.topic.sourceUrl} target="_blank" rel="noreferrer">
                  {response.topic.source} <ExternalLink size={14} />
                </a>
              </>
            ) : (
              <p>
                This version only answers questions about understanding lab reports,
                hemoglobin, RBC, WBC, platelets, glucose, and cholesterol. Try one of
                the suggested questions above. It cannot answer personal diagnosis or
                treatment questions.
              </p>
            )}
          </section>
        )}

        <footer className="assistant-footer">
          General information only. For interpretation of your own results, speak with
          a qualified healthcare professional.
        </footer>
      </div>
    </div>
  );
}

export default HealthAssistant;
