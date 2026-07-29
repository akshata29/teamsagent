// Adaptive Card builders for the Capital Markets research assistant (Teams-native UI).
//
// Each builder returns the raw Adaptive Card content object; the agent wraps it with
// CardFactory.adaptiveCard(...) + MessageFactory.attachment(...) before sending.
// Adaptive Cards are an Option B capability: the automatic Foundry Responses->Activity
// bridge (Option A) preserves text only, so cards/citations are rendered here.

type Card = Record<string, unknown>;

interface DocHit {
  id: string;
  title: string;
  classification: string;
  snippet?: string;
  score?: number;
}

interface InvokeResult {
  option?: string;
  persona_id?: string;
  query?: string;
  answer?: string;
  doc_hits?: DocHit[];
  visible_doc_ids?: string[];
  trimmed_doc_ids?: string[];
  identity_basis?: string;
  note?: string;
}

function classificationBadge(classification: string): Record<string, unknown> {
  const map: Record<string, { text: string; color: string }> = {
    public: { text: "PUBLIC", color: "Good" },
    internal: { text: "INTERNAL", color: "Accent" },
    mnpi: { text: "MNPI", color: "Attention" },
  };
  const b = map[classification] ?? { text: classification.toUpperCase(), color: "Default" };
  return {
    type: "TextBlock",
    text: b.text,
    color: b.color,
    weight: "Bolder",
    size: "Small",
    horizontalAlignment: "Right",
  };
}

function identityBadge(basis?: string): { text: string; color: string } {
  switch (basis) {
    case "per_user_obo":
      return { text: "Per-user OBO — trimmed to your entitlements", color: "Good" };
    case "public_only":
      return { text: "Public only — sign in for entitled research", color: "Warning" };
    case "app_only":
      return { text: "App-only identity", color: "Accent" };
    default:
      return { text: basis ?? "unknown", color: "Default" };
  }
}

/** Build the research answer Adaptive Card content from a backend InvokeResult. */
export function buildResearchCard(result: InvokeResult): Card {
  const docs = result.doc_hits ?? [];
  const idBadge = identityBadge(result.identity_basis);

  const docItems = docs.map((d) => ({
    type: "Container",
    spacing: "Small",
    separator: true,
    items: [
      {
        type: "ColumnSet",
        columns: [
          {
            type: "Column",
            width: "stretch",
            items: [
              { type: "TextBlock", text: d.title, weight: "Bolder", size: "Small", wrap: true },
              { type: "TextBlock", text: d.id, isSubtle: true, spacing: "None", size: "Small" },
            ],
          },
          { type: "Column", width: "auto", items: [classificationBadge(d.classification)] },
        ],
      },
    ],
  }));

  const body: Array<Record<string, unknown>> = [
    {
      type: "TextBlock",
      text: "Capital Markets Research",
      weight: "Bolder",
      size: "Medium",
      wrap: true,
    },
    {
      type: "TextBlock",
      text: idBadge.text,
      color: idBadge.color,
      size: "Small",
      isSubtle: true,
      spacing: "None",
      wrap: true,
    },
    { type: "TextBlock", text: result.answer ?? "(no answer)", wrap: true, spacing: "Medium" },
  ];

  if (docItems.length) {
    body.push({
      type: "TextBlock",
      text: `Sources (${docItems.length})`,
      weight: "Bolder",
      spacing: "Medium",
      wrap: true,
    });
    body.push(...docItems);
  }

  if (result.note) {
    body.push({
      type: "TextBlock",
      text: result.note,
      wrap: true,
      isSubtle: true,
      size: "Small",
      spacing: "Medium",
    });
  }

  return {
    $schema: "http://adaptivecards.io/schemas/adaptive-card.json",
    type: "AdaptiveCard",
    version: "1.5",
    body,
    actions: [
      { type: "Action.Submit", title: "Semiconductor view", data: { query: "What is our semiconductor sector view?" } },
      { type: "Action.Submit", title: "High-yield energy credit", data: { query: "Any high-yield energy credit ideas?" } },
      { type: "Action.Submit", title: "Duration positioning", data: { query: "What is our duration positioning?" } },
    ],
  };
}

/** Simple welcome card shown when the user first opens the agent. */
export function buildWelcomeCard(): Card {
  return {
    $schema: "http://adaptivecards.io/schemas/adaptive-card.json",
    type: "AdaptiveCard",
    version: "1.5",
    body: [
      { type: "TextBlock", text: "Capital Markets Research Assistant", weight: "Bolder", size: "Medium" },
      {
        type: "TextBlock",
        text: "Ask about your desk's research. After you sign in, results are trimmed to your entitlements via On-Behalf-Of (per-user document-level security).",
        wrap: true,
        isSubtle: true,
      },
    ],
    actions: [
      { type: "Action.Submit", title: "What is our semiconductor sector view?", data: { query: "What is our semiconductor sector view?" } },
    ],
  };
}
